[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Frontend coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_frontend&key_text=Frontend+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Frontend

This django project provides an installable PWA duplicating all functions of the [command line tools](CLI/):
- Create and edit config files
- Provision new ESP32 nodes
- Manage schedule keywords and rules
- Send API calls at runtime through intuitive card-based interface

When run with SSL and a domain this app can be installed to the homescreen on iOS and Android.

## Usage

While the app can be run as a local development server, docker is strongly recommended

### Docker

Build the docker image:
```
sudo docker build -t micropython-smarthome:1.0 . -f frontend/docker/Dockerfile
```

Copy the [docker-compose.yaml example](frontend/docker/docker-compose.yaml) and make changes as needed.

Supported Env Vars:
- `ALLOWED_HOSTS`: Comma-separated list of domains and IPs where the app can be reached, all others will be blocked. Defaults to wildcard if omitted (not recommended).
- `CONFIG_DIR`: Path to directory where config files are written. Defaults to `micropython-smarthome/config_files` if omitted.
- `NODE_PASSWD`: Webrepl password of all ESP32s, defaults to `password` if omitted.
- `SECRET_KEY`: Your django secret key, if omitted a new key will be generated each time the app starts (may break active sessions).
- `VIRTUAL_HOST`: Reverse proxy domain, make sure to add the same domain to `ALLOWED_HOSTS`.

Once configuration is complete run `docker compose up -d`. The webapp can now be accessed at any of your `ALLOWED_HOSTS`, provided the domains/IPs point to your docker host.

### Local Development Server

The development server can be run with django's `manage.py`:
```
cd frontend/
pipenv run python3 manage.py runserver
```

The app can now be accessed at [localhost:8000/](http://localhost:8000/).

Environment variables can be added to `.env` in the repository root before running.

To access the app from clients other than the host, either set the `ALLOWED_HOSTS` env var or start the server listening on all interfaces:
```
cd frontend/
pipenv run python3 manage.py runserver 0:8000
```

## Management commands

Custom management commands can be used to export all config files from the SQL database to `CONFIG_DIR`, or to read the contents of `CONFIG_DIR` into the database. This can be useful to create backups, recover from a corrupted database, or to migrate to another host. However, unless the CLI tools are used heavily it is recommended to just backup the database itself.

Export:
```
cd frontend/
python3 manage.py export_configs_to_disk
```

Import:
```
cd frontend/
python3 manage.py import_configs_from_disk
```

## Unit tests

Tests have full coverage of the django backend:
```
cd frontend/
pipenv run python3 manage.py test
```
