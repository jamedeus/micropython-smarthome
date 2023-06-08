# syntax=docker/dockerfile:1

# Node dependencies build stage
FROM node:19-buster-slim as node_build

COPY frontend/package.json .
RUN npm install

# Python dependencies build stage
FROM python:3.10-slim-buster as py_build

COPY frontend/docker/requirements.txt .
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
RUN mkdir /repo/firmware

# Smarthome core modules, peripheral modules, dependencies
COPY core /repo/core/
COPY devices /repo/devices
COPY sensors /repo/sensors
COPY lib /repo/lib

# Frontend
COPY frontend/manage.py /repo/frontend/manage.py
COPY frontend/api /repo/frontend/api
COPY frontend/node_configuration /repo/frontend/node_configuration
COPY frontend/frontend /repo/frontend/frontend
COPY frontend/webapp /repo/frontend/webapp

# Copy node + python dependencies to final build stage
COPY --from=node_build node_modules/bootstrap/dist/css/bootstrap.min.css /repo/frontend/node_modules/bootstrap/dist/css/bootstrap.min.css
COPY --from=node_build node_modules/bootstrap/dist/js/bootstrap.bundle.min.js /repo/frontend/node_modules/bootstrap/dist/js/bootstrap.bundle.min.js
COPY --from=node_build node_modules/bootstrap/dist/js/bootstrap.min.js /repo/frontend/node_modules/bootstrap/dist/js/bootstrap.min.js
COPY --from=node_build node_modules/bootstrap-icons/font/bootstrap-icons.css /repo/frontend/node_modules/bootstrap-icons/font/bootstrap-icons.css
COPY --from=node_build node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff /repo/frontend/node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff
COPY --from=node_build node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2 /repo/frontend/node_modules/bootstrap-icons/font/fonts/bootstrap-icons.woff2
COPY --from=node_build node_modules/jquery/dist/jquery.min.js /repo/frontend/node_modules/jquery/dist/jquery.min.js
COPY --from=node_build node_modules/spinkit/spinkit.min.css /repo/frontend/node_modules/spinkit/spinkit.min.css
COPY --from=node_build node_modules/smoothscroll-polyfill/dist/smoothscroll.min.js /repo/frontend/node_modules/smoothscroll-polyfill/dist/smoothscroll.min.js
COPY --from=node_build node_modules/rangeslider.js/dist/rangeslider.min.js /repo/frontend/node_modules/rangeslider.js/dist/rangeslider.min.js
COPY --from=py_build /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/

# Run migrations, start dev server
COPY frontend/docker/entrypoint.sh /repo/entrypoint.sh
CMD ["/repo/entrypoint.sh"]
