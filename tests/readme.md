[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Frontend coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_firmware&key_text=Firmware+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Unit Tests

This directory contains all unit tests for the project (except django, see [frontend](frontend/)).
- `CLI`: Tests for the [command line tools](/CLI/) used to create and manage nodes
- `client`: Tests that make API calls to a baremetal ESP32 node and verify responses
- `firmware`: Tests written in micropython that run on a baremetal ESP32 with results read over UART
- `mock_environment`: A mocked environment to run the firmware tests on cpython for coverage measurement

All tests should be run with [pipenv](/Pipfile) activated.

## CLI

To run the CLI tests go to the repo root and paste this:

```
export PYTHONPATH=$PYTHONPATH:`pwd`/CLI
pipenv run coverage run run_cli_tests.py
pipenv run coverage report
```

Note: The `run_cli_tests.py` script applies mocks that prevent `CLI/cli_config.json` from being read (if it exists). Running tests without the script will likely fail.

## Client

These tests make an exhuastive set of API calls to an ESP32 with a [mocked config file](/tests/client/client_test_config.json). The same calls are made using both the custom protocol and HTTP. This enables much more thorough coverage of responses and errors than can be achieved with tests running directly on an ESP32, where memory fragmentation limits the number of tests that can be run.

Client tests require an ESP32 with [firmware](https://gitlab.com/jamedeus/micropython-smarthome/-/releases) flashed and wifi connected. The [test script](/tests/client/runtests.py) can upload the mocked config file automatically.

Upload config and run tests in 1 step:
```
./tests/client/runtests.py --ip <target-node-ip> --upload
```

Run tests without uploading config:
```
./tests/client/runtests.py --ip <target-node-ip>
```

Coverage measurement is not possible since the code under test runs on a remote host (ESP32).

## Firmware

The firmware tests require an ESP32 connected via USB. Flash the [firmware](https://gitlab.com/jamedeus/micropython-smarthome/-/releases) if you haven't already and run through setup to connect the node to your wifi.

Once the ESP32 is set up use [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) to view serial output:
```
mpremote connect /dev/ttyUSB0
```

Firmware tests can be uploaded to the ESP32 in a single step with [provision.py](/CLI/provision.py):
```
./CLI/provision.py --test <target-node-ip>
```

When the upload completes the node will reboot and run the first group of tests. To prevent memory fragmentation issues the test are split into 4 groups:
- core
- api
- device
- sensors

A results summary is printed at the end of each group followed by a menu used to select the next group of tests. Complete results from all groups can be viewed by pressing 6 at the menu.

## Frontend

See the [frontend readme](/frontend/README.md) for django and react test instructions.

## Mock Environment

The mock environment runs firmware tests in cpython for coverage measurement, see [here](/tests/mock_environment/readme.md) for details. No hardware is required to run these tests.

## Convenience script

The [run_all_tests.sh](run_all_tests.sh) script automatically runs the CLI, frontend, and firmware tests (in mocked environment). Simply call the script:
```
./run_all_tests.sh
```

Separate coverage reports will be printed for each suite when the tests complete.

Note: the mock command receiver must be set up before running this script, see [here](/tests/mock_environment/readme.md) for instructions.
