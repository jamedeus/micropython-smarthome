# syntax=docker/dockerfile:1

# Node dependencies build stage
FROM node:19-buster-slim as node_build

COPY frontend/package.json .
RUN npm install

# Python dependencies build stage
FROM python:3.10-slim-buster as py_build

COPY docker/requirements.txt .
RUN pip install --no-cache-dir -r /requirements.txt

# Final build stage
FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Default env vars, can be overridden in docker-compose
ENV REPO_DIR="/repo/"
ENV CONFIG_DIR="/repo/config/"
ENV NODE_PASSWD="password"

# Create dir for repo, copy in modules
WORKDIR /repo
RUN mkdir /repo/config

# Smarthome core modules
COPY boot.py /repo/boot.py
COPY setup.py /repo/setup.py
COPY Api.py /repo/Api.py
COPY Config.py /repo/Config.py
COPY Group.py /repo/Group.py
COPY SoftwareTimer.py /repo/SoftwareTimer.py

# Peripheral modules + dependencies
COPY lib /repo/lib
COPY devices /repo/devices
COPY sensors /repo/sensors
COPY ir-remote /repo/ir-remote

# Frontend
COPY frontend/manage.py /repo/frontend/manage.py
COPY frontend/api /repo/frontend/api
COPY frontend/node_configuration /repo/frontend/node_configuration
COPY frontend/frontend /repo/frontend/frontend
COPY frontend/webapp /repo/frontend/webapp

# Copy node + python dependencies to final build stage
COPY --from=node_build node_modules/bootstrap/dist/css/bootstrap.min.css /repo/frontend/node_modules/bootstrap/dist/css/bootstrap.min.css
COPY --from=node_build node_modules/bootstrap/dist/js/bootstrap.bundle.min.js /repo/frontend/node_modules/bootstrap/dist/js/bootstrap.bundle.min.js
COPY --from=node_build node_modules/bootstrap-icons/font/bootstrap-icons.css /repo/frontend/node_modules/bootstrap-icons/font/bootstrap-icons.css
COPY --from=node_build node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff /repo/frontend/node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff
COPY --from=node_build node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2 /repo/frontend/node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2
COPY --from=node_build node_modules/jquery/dist/jquery.min.js /repo/frontend/node_modules/jquery/dist/jquery.min.js
COPY --from=node_build node_modules/spinkit/spinkit.min.css /repo/frontend/node_modules/spinkit/spinkit.min.css
COPY --from=node_build node_modules/smoothscroll-polyfill/dist/smoothscroll.min.js /repo/frontend/node_modules/smoothscroll-polyfill/dist/smoothscroll.min.js
COPY --from=node_build node_modules/rangeslider.js/dist/rangeslider.min.js /repo/frontend/node_modules/rangeslider.js/dist/rangeslider.min.js
COPY --from=py_build /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Vanilla database, migrations applied, no configs/nodes
# Persists between sessions if volume used, or can mount in external db
COPY docker/default-db.sqlite3 /repo/frontend/db.sqlite3

CMD ["python", "frontend/manage.py", "runserver", "0:8456"]
