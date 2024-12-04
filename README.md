[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Firmware coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_firmware&key_text=Firmware+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Frontend coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_react&key_text=Frontend+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Django coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_django&key_text=Django+Coverage&key_width=110)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Latest Release](https://gitlab.com/jamedeus/micropython-smarthome/-/badges/release.svg?key_text=Firmware+Release&key_width=112)](https://gitlab.com/jamedeus/micropython-smarthome/-/releases)

# Micropython Smarthome

## Firmware

Pre-built firmware binaries can be downloaded from [releases](https://gitlab.com/jamedeus/micropython-smarthome/-/releases).

See [firmware](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/firmware) for build instructions.

## Command line tools

See [CLI readme](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/CLI).

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

## Useful documentation links

* [Micropython ESP32 build instructions](https://github.com/micropython/micropython/blob/master/ports/esp32/README.md#setting-up-esp-idf-and-the-build-environment)
* [Micropython release history](https://github.com/micropython/micropython/releases)
* [Micropython asyncio](https://docs.micropython.org/en/latest/library/asyncio.html)
* [Micropython manifest files](https://docs.micropython.org/en/latest/reference/manifest.html)
