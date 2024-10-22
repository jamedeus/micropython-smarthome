# Mock Testing Environment

This environment allows hardware-level unit tests written for micropython to run on cpython, enabling coverage measurement. Tests also run significantly faster here and do not have to be split into groups to avoid memory fragmentation (see [unit_test_main.py](tests/firmware/unit_test_main.py)).

The [mocks](tests/mock_environment/mocks/) directory contains dummy modules for all micropython-specific libraries used in this project. This directory must be patched into the python import path before running tests.

In some cases (time, logging) python preferentially imports the stdlib module over a mock with the same name, regardless of position within the import path. For these cases the stdlib module must be imported, then its methods are overwritten with references to mocked methods. See [runtests.py](tests/mock_environment/runtests.py) to better understand how this works.

A [mock API receiver script](mock_command_receiver/mock_command_receiver.py) is also provided to simulate hardware devices on the LAN (smart dimmers, WLED instances, etc). This makes it possible to run all unit tests without access to the physical hardware the device classes interface with.

## Usage

Build the mock API receiver docker image and start it:
```
cd tests/mock_environment/mock_command_receiver/
docker build -t smarthome_mock_receiver:0.1 . -f Dockerfile
docker compose up -d
cd ..
```

Add the IP of your docker host to [unit_test_config.json](tests/firmware/unit_test_config.json):
```
"mock_receiver": {
    "ip": "192.168.1.229",
    "port": 8956,
    "error_port": 8955,
    "api_port": 8321
}
```

Check the firewall on your docker host and make sure these ports and `9999` are not blocked.

Then simply run [runtests.py](tests/mock_environment/runtests.py) from the project root directory:
```
cd ../../
coverage run --source='core,devices,sensors' tests/mock_environment/runtests.py
coverage report
```

## Ports

If the default ports `8956`, `8955`, and `8321` are already in use they must be changed in **both** [unit_test_config.json](tests/firmware/unit_test_config.json) and [docker-compose.yaml](tests/mock_environment/mock_command_receiver/docker-compose.yaml).

These ports are used for:
- `port`: Simulates successful API calls to Tasmota devices, WLED instances, and desktop integration
- `error_port`: Simulates failed API calls, returns 500 to all requests
- `api_port`: Simulates another ESP32 node for [ApiTarget](tests/firmware/test_device_apitarget.py) tests

The port `9999` is used to simulate requests to TpLink Kasa devices. This cannot be changed because it is not configurable on the actual TpLink devices (the same test suite is run against physical hardware when run outside the mocked environment).

The mock receiver host's firewall **must not block these ports** or the tests will fail.

## Mocked Micropython Modules
- [x] machine.pin
- [x] machine.PWM
- [x] machine.SoftI2C
- [x] machine.Timer
- [x] machine.RTC
- [x] machine.enable_irq
- [x] machine.disable_irq
- [x] micropython.schedule
- [x] micropython.mem_info
- [x] ir_tx.Player
- [x] time.sleep_ms
- [x] time.sleep_us
- [x] time.time
- [x] requests
- [x] asyncio
- [x] si7021
- [x] gc
- [x] network
- [x] webrepl
- [x] logging
- [x] ubinascii
- [x] dht
- [x] tls
- [x] vfs

The following are not currently mocked, but may be added in the future if tests for `core/boot.py` are added:
- [ ] os
- [ ] inisetup
- [ ] flashbdev
