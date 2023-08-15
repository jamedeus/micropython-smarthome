# Mock Micropython Modules

This directory contains mocked versions of modules exclusive to Micropython. This allows code written for micropython to run on cpython, with all its expected dependencies and their methods available in the import path. Most mocks are empty classes with no functionality, exceptions are documented below.

## Json module

The `runtests.py` script replaces `json.loads` and `json.JSONDecoder` with mocks that handle invalid syntax by raising OSError (rather than JSONDecodeError). This matches the behavior of micropython's json module, which does not implement JSONDecodeError. The JSONDecoder mock also raises a ValueError if the encoded JSON contains NaN (not suppoorted on micropython).

## Logging module

Note: this project does NOT use the `logging` module from [micropython-lib](https://github.com/micropython/micropython-lib/tree/c113611765278b2fc8dcf8b2f2c3513b35a69b39), which is fairly limited. Instead [pfalcon's implementation](https://github.com/pfalcon/pycopy-lib/blob/master/logging/logging/__init__.py) is used.

Most of the mocked logic is only required for the `clear_log` API endpoint, which clears all log handlers, creates a new log file, and creates a new handler.

The `runtests.py` script adds a mock `Logger()` instance to the `logging.root.handlers` list. This allows the `clear_log` endpoint to call the `close` method of the root logger. It also replaces `logging.FileHandler` with a mocked class that creates its filename argument on disk, matching micropython's behavior.

After `clear_log` creates a new log file and handler it clears the contents of `logging.root.handlers`, then adds its new handler with `addHandler`. This method is mocked to simply add another instance of `Logger()` to the handlers list. The handler created in the endpoint is ignored as it is not important to any tests.

All log level methods (`log.info`, `log.error`, etc) simply write any argument they receive to `app.log` unmodified - timestamps are not important for any unit tests.

## Machine module

### machine.Pin

The `value` method can be called with an argument to set the `pin_state` attribute. When called without argument it returns the `pin_state` attribute.

Constants required to provision pins and set interrupts exist but their values are ignored.

### machine.PWM

The `duty` method can be called with an argument to set the `_duty` attribute. When called without argument it returns the `_duty` attribute.

### machine.reset

The reset method (used to hard reboot microcontrollers) is mocked with a `Reset` class instantiated as `reset` within the machine module, ensuring all importing modules receive the same object. Calling the object simply sets `reset.called` to True, allowing tests to confirm it was called.

### machine.Timer

This is the most complicated mock, used to simulate hardware interrupt timers on the ESP32.

The ESP32 has 4 hardware timers which can be accessed by instantiating `Timer` with `0`, `1`, `2`, or `3` as argument. Multiple pieces of code running on the same ESP32 can read/modify the same timer by instantiating `Timer` with the same argument. Scope is not relevant since all state information is stored in the hardware-level device that `Timer` interacts with, rather than in memory.

To simulate this in cpython, instantiated timers are stored in a class-level dict `_timers` keyed by their `timer_id` arg. When `Timer` is instantiated the `__new__` method checks if the `timer_id` it received exists in the dict and returns the existing instance if so. Otherwise, a new instances is created, added to the dict, and returned. All future attempts to instantiate `Timer` with the same `timer_id` will receive this instance.

When the `init` method is called a new thread is created to handle the callback function. The thread waits for the requested number of seconds, then checks if the timer was canceled while waiting. If not, the callback runs.

The `deinit` method sets a `threading.Event()` attribute checked by the thread handler function. This causes the thread to exit without running the callback after the timer expires.

The `value` method returns the remaining time in milliseconds, calculcated from the `start_time` and `period` attribute created by `init`.

## Micropython module

### micropython.schedule

The `schedule` method requires 2 arguments: a function to call and its argument. In micropython this is used to call a function during an interrupt with execution delayed until immediately after the heap is locked. The mock simply calls the function immediately.

## Network module

### network.WLAN

The ESP32 has 2 wifi interfaces (access point and station), both of which are controlled by the `WLAN` module. Objects representing each interface are obtained by instantiating `WLAN` with `network.AP_IF` and `network.STA_IF` respectively. Either can be instantiated from any context to check connection status etc.

The mocked module returns separate singleton objects for each interface, allowing multiple files to obtain the same object. This enables unit tests to read values set by the code under test the same way they would on baremetal. There is no functionality, all methods simply set and return attributes.

The `active` method called with no argument returns the `_active` attribute. When called with an argument it sets the `_active` attribute.

The `config` method accepts the `"mac"`, `"ssid"`, and `"reconnects"` string arguments and returns the corresponding attribute. Alternately, the `ssid=` or `reconnects=` kwargs can be used to set the attribute. The mac address is hardcoded and cannot be set. These attributes have no functionality and are only used to verify tests.

The `connect` method takes ssid and password arguments, sets the `_status` attribute to `STAT_CONNECTING`, and starts a 100ms timer with a callback that completes the connection. A failed connection can be simulated by using the arbitrary ssid `wrong`, which results in `_status = STAT_NO_AP_FOUND` and `connected = False`. Any other ssid will result in `_status = STAT_GOT_IP`, `connected = True`, and the `_ifconfig` attribute being set to an address/subnet/gateway tuple with localhost as the current IP. The `connect` method is only available for the station interface and raises an exception when called by access point.

The `disconnect` method sets the `connected` attribute to `False`. When called for the station interface it also sets `_ifconfig` to a placeholder tuple and `_status` to `8` (WIFI_REASON_ASSOC_LEAVE, see esp-idf).

The `isconnected` method returns the `connected` attribute.

The `ifconfig` method called with no argument returns the `_ifconfig` attribute, which contains a tuple set in the `connect` and `disconnect` methods. It can also be called with a 4-tuple as argument to set the `_ifconfig` attribute.

## SI7021 module

This module mocks the [si7021 driver](https://github.com/chrisbalmer/micropython-si7021) used in this project. It simply returns hardcoded temperature and humidity values.


## Uasyncio module

The cpython `asyncio` module is aliased to `uasyncio` and used as-is, with the addition of `sleep_ms` and `sleep_us` coroutines that only exist in micropython.

## Urequests module

The cpython `requests` module is aliased to `urequests` and used as-is in most cases.

The `Response` class (returned by most requests methods) is replaced by a subclass that modifies the `json()` method. When the response contents are not valid JSON a `ValueError` is raised instead of `JSONDecodeError` to match the behavior of micropython's `urequests`. There are no other differences.

## Webrepl module

The webrepl mock has no functionality, it simply contains a `start` method which creates a socket in the `listen_s` attribute. This allows tests to detect if webrepl has been started.
