# Unit Tests

This directory contains all unit tests for the project (except django, see [frontend](frontend/)).
- `CLI`: Tests for the [command line tools](/CLI/) used to create and manage nodes
- `client`: (currently broken) Tests that make API calls against a baremetal ESP32 node
- `firmware`: Tests written in micropython that run on a baremetal ESP32 with results read over UART
- `mock_environment`: A mocked environment to run the firmware tests on cpython for coverage measurement

All tests should be run with [pipenv](/Pipfile) activated.

## CLI

To run the CLI tests go to the repo root and paste this:

```
export PYTHONPATH=$PYTHONPATH:`pwd`/CLI
pipenv run coverage run --omit='tests/*' -m unittest discover tests/cli
pipenv run coverage report -m --precision=1
```

## Client

The client tests are not currently functional.

These tests send an exhuastive set of API calls to an ESP32 with a [mocked config file](/tests/client/client_test_config.json) and verify the responses.

## Firmware

The firmware tests require an ESP32 connected via USB. Flash the [firmware](https://gitlab.com/jamedeus/micropython-smarthome/-/releases) if you haven't already and run through setup to connect the node to your wifi.

Firmware tests can be uploaded to the ESP32 in a single step with [provision.py](/CLI/provision.py):
```
./CLI/provision.py --test <target-node-ip>
```

When the upload completes the node will reboot and run the first group of tests. Due to memory fragmentation issues the tests run in 4 groups:
- core
- api
- device
- sensors

Once the core tests complete the results will be printed followed by a menu used to select the next group of tests. Complete results from all tests can be viewed by pressing 6 at the menu.

## Mock Environment

The mock environment runs firmware tests in cpython for coverage measurement, see [here](/tests/mock_environment/readme.md) for details.
