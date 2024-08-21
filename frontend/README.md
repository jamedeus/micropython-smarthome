[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Frontend coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_react&key_text=Frontend+Coverage&key_width=120)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![Django coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_django&key_text=Django+Coverage&key_width=110)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

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
docker build -t micropython-smarthome:1.0 . -f frontend/docker/Dockerfile
```

Copy the [docker-compose.yaml example](frontend/docker/docker-compose.yaml) and make changes as needed.

Supported Env Vars:
- `ALLOWED_HOSTS`: Comma-separated list of domains and IPs where the app can be reached, all others will be blocked. Defaults to wildcard if omitted (not recommended).
- `NODE_PASSWD`: Webrepl password of all ESP32s, defaults to `password` if omitted.
- `SECRET_KEY`: Your django secret key, if omitted a new key will be generated each time the app starts (may break active sessions).
- `VIRTUAL_HOST`: Reverse proxy domain, make sure to add the same domain to `ALLOWED_HOSTS`.
- `GEOCODE_API_KEY`: API key used to get GPS coordinates from https://geocode.maps.co/ (make account for free key). This is used in the overview page default location modal to look up city coordinates, which are added to ESP32 config files and used to get accurate sunrise and sunset times.

Once configuration is complete run `docker compose up -d`. The webapp can now be accessed at any of your `ALLOWED_HOSTS`, provided the domains/IPs point to your docker host.

### Local Development Server

All frontend pages are rendered by react bundles, which are imported by django templates containing a context which is rehydrated as the initial state object. These must be compiled before the frontend can be used.

To build the react bundles run:
```
cd frontend
npm install
npm run build
```

Then start the django development server (there is no separate node backend):
```
cd frontend/
pipenv run python3 manage.py migrate
pipenv run python3 manage.py runserver
```

The app can now be accessed at [localhost:8000/](http://localhost:8000/).

Environment variables can be added to `.env` in the repository root before running (see docker section for supported env vars).

To access the app from clients other than the host, either set the `ALLOWED_HOSTS` env var or start the server listening on all interfaces:
```
cd frontend/
pipenv run python3 manage.py runserver 0:8000
```

#### React Development

To automatically rebuild the webpack bundles when changes are detected run:
```
cd frontend
npm run watch
```

All react bundles are served from django templates, so the django development server (above) must be running to access the app. There is no node backend.

## Unit tests

### Run django tests
```
cd frontend/
pipenv run coverage run --source='.' manage.py test
pipenv run coverage report
```

### Run react tests
```
cd frontend/
npm install
npm run test -- --coverage
```
