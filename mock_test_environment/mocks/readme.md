# Mock Micropython Modules

This directory contains mocked versions of modules exclusive to Micropython. This allows code written for micropython to run on cpython, with all its expected dependencies and their methods available in the import path. Most mocks are empty classes with no functionality, exceptions are documented below.

## Logging module

Note: this project does NOT use the `logging` module from [micropython-lib](https://github.com/micropython/micropython-lib/tree/c113611765278b2fc8dcf8b2f2c3513b35a69b39), which is fairly limited. Instead [pfalcon's implementation](https://github.com/pfalcon/pycopy-lib/blob/master/logging/logging/__init__.py) is used.

Most of the mocked logic is only required for the `clear_log` API endpoint, which clears all log handlers, creates a new log file, and creates a new handler.

The `runtests.py` script adds a mock `Logger()` instance to the `logging.root.handlers` list. This allows the `clear_log` endpoint to call the `close` method of the root logger.

After `clear_log` creates a new log file and handler it clears the contents of `logging.root.handlers`, then adds its new handler with `addHandler`. This method is mocked to simply add another instance of `Logger()` to the handlers list. The handler created in the endpoint is ignored as it is not important to any tests.

## Machine module

### machine.Pin

The `value` method can be called with an argument to set the `pin_state` attribute. When called without argument it returns the `pin_state` attribute.

### machine.PWM

The `duty` method can be called with an argument to set the `_duty` attribute. When called without argument it returns the `_duty` attribute.

### machine.Timer

This is the most complicated mock, used to simulate hardware interrupt timers on the ESP32.

The ESP32 has 4 hardware timers which can be accessed by instantiating `Timer` with `0`, `1`, `2`, or `3` as argument. Multiple pieces of code running on the same ESP32 can read/modify the same timer by instantiating `Timer` with the same argument. Scope is not relevant since all state information is stored in the hardware-level device that `Timer` interacts with, rather than in memory.

To simulate this in cpython, instantiated timers are stored in a class-level dict `_timers` keyed by their `timer_id` arg. When `Timer` is instantiated the `__new__` method checks if the `timer_id` it received exists in the dict and returns the existing instance if so. Otherwise, a new instances is created, added to the dict, and returned. All future attempts to instantiate `Timer` with the same `timer_id` will receive this instance.

When the `init` method is called a new thread is created to handle the callback function. The thread waits for the requested number of seconds, then checks if the timer was canceled while waiting. If not, the callback runs.

The `deinit` method sets a `threading.Event()` attribute checked by the thread handler function. This causes the thread to exit without running the callback after the timer expires.

## Network module

### network.WLAN

In micropython the `WLAN` module controls the ESP32's wifi interface. It can be instantiated from any context to check connection status etc.

This is mocked with a singleton class which returns the same instance when instantiated multiple times. There is no functionality, all methods simply set and return attributes.

The `active` method called with no argument returns the `_active` attribute. When called with an argument it sets the `_active` attribute.

The `connect` method takes ssid and password arguments and immediately sets the `connected` attribute to `True`.

The `isconnected` method returns the `connected` attribute.

The `ifconfig` method returns a hardcoded address/subnet/gateway tuple. This diverges from micropython's behavior but is adequate for the current test suite.

## SI7021 module

This module mocks the [si7021 driver](https://github.com/chrisbalmer/micropython-si7021) used in this project. It simply returns hardcoded temperature and humidity values.


## Urequests module

The cpython `requests` module is aliased to `urequests` and used as-is in most cases.

The `Response` class (returned by most requests methods) is replaced by a subclass that modifies the `json()` method. When the response contents are not valid JSON a `ValueError` is raised instead of `JSONDecodeError` to match the behavior of micropython's `urequests`. There are no other differences.
