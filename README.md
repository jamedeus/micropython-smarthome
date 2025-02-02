[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Firmware coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_firmware&key_text=Firmware+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Frontend coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_react&key_text=Frontend+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Django coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_django&key_text=Django+Coverage&key_width=110)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Latest Release](https://gitlab.com/jamedeus/micropython-smarthome/-/badges/release.svg?key_text=Firmware+Release&key_width=112)](https://gitlab.com/jamedeus/micropython-smarthome/-/releases)

# Micropython Smarthome

An overly ambitious but surprisingly successful attempt to build a home automation framework entirely in MicroPython. Runs on ESP32.

## Features
* **Stand-alone nodes**: Each ESP32 runs independently with no hub or cloud required.
* **Designed for automation**: Configure things to do what you want, when you want.
* **Extensible hardware drivers**: Object-oriented framework allows new device and sensor drivers to be added with just a few lines of code.
* **Django-powered PWA**: Installable web frontend to view node status, change configuration, and send API calls.
* **Command line client**: Interactive menus or CLI arguments, synchronizes with the django backend (or can be used standalone).
* **Local API**: Everything can be controlled with HTTP on LAN, no data leaves the network.
* **Secure wifi setup**: After flashing firmware a [captive portal](https://en.wikipedia.org/wiki/Captive_portal) is served with HTTPS to securely set wifi credentials.

## Design Goals
* **Automation over remote control**: Lots of commercial IOT products emphasize controlling things with your phone. **This is a bad user experience** - walking to the light switch is usually faster than finding the right button in a bloated app that gets a UI update right when you learn where everything is. Instead, this project aims to provide granular configuration options so you can **automate things once and forget about it**.
* **Maintainability and testability**: The project aims to be as [DRY](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself) as possible. Functions shared by the web frontend and CLI tools are imported from modules in the [util](/util) package so they can be maintained in one place. Most of the hardware-level API is abstracted into base classes and inherited by individual drivers to reduce bugs and make testing easier.
* **Extensibility**: New [device](devices/readme.md) and [sensor](sensors/readme.md) drivers can often be written with fewer than 50 lines of code thanks to a cooperative class inheritance system. JSON [metadata](/util/metadata) automatically integrates new drivers into the frontend with no additional javascript needed.
* **Responsive and reliable**: Since all requests stay on the LAN, latency is very low and everything still works when the internet goes down.

## Firmware

Pre-built firmware binaries can be downloaded from [releases](https://gitlab.com/jamedeus/micropython-smarthome/-/releases).

See [firmware](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/firmware) for build, flash, and wifi setup instructions.

## Command line tools

The command line client can be used to generate config files, provision new nodes, check status, and send API commands using either interactive menus or CLI arguments. See the [CLI readme](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/CLI) for details.

## Unit testing

See [test readme](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/tests).

## Development

Requirements:
* pipenv (>=2023.6.2)
* npm
* docker

Install dependencies for the frontend, firmware, and CLI tools:
```
pipenv install --dev
cd frontend
npm install
cd ..
cd firmware
npm install
```

Build the frontend and apply django database migrations:
```
cd frontend
npm run build
pipenv run python3 manage.py migrate
```
* Note: run `npm run watch` to automatically rebuild bundles when react components change.

Install git hooks (see comments at the top of each file):
```
cp hooks/pre-commit hooks/post-commit .git/hooks/
```

### Useful documentation links

* [Micropython ESP32 build instructions](https://github.com/micropython/micropython/blob/master/ports/esp32/README.md#setting-up-esp-idf-and-the-build-environment)
* [Micropython release history](https://github.com/micropython/micropython/releases)
* [Micropython asyncio](https://docs.micropython.org/en/latest/library/asyncio.html)
* [Micropython manifest files](https://docs.micropython.org/en/latest/reference/manifest.html)
