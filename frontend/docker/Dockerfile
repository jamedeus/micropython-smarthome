# syntax=docker/dockerfile:1

# Node dependencies build stage
FROM node:19-buster-slim AS node_build

# Copy directory containing package.json and react components
COPY frontend/ .
WORKDIR /frontend
# Install node modules, bundle react components
RUN npm install
RUN npm run build

# Python dependencies build stage
FROM python:3.10-slim-buster AS py_build

COPY frontend/docker/requirements.txt .
RUN pip install --no-cache-dir -r /requirements.txt

# Final build stage
FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create dir for repo, copy in core modules, peripheral modules, dependencies
WORKDIR /repo
COPY core /repo/core/
COPY devices /repo/devices
COPY sensors /repo/sensors
COPY lib /repo/lib
COPY util /repo/util

# Add utils to global path
ENV PYTHONPATH=/repo/util

# Frontend
COPY frontend/manage.py /repo/frontend/manage.py
COPY frontend/api /repo/frontend/api
COPY frontend/node_configuration /repo/frontend/node_configuration
COPY frontend/frontend /repo/frontend/frontend
COPY frontend/webapp /repo/frontend/webapp

# Copy python dependencies to final build stage
COPY --from=py_build /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
# Copy webpack bundles to final build stage
COPY --from=node_build webapp/static/webapp/ /repo/frontend/webapp/static/webapp/

# Run migrations, start dev server
COPY frontend/docker/entrypoint.sh /repo/entrypoint.sh
CMD ["/repo/entrypoint.sh"]
