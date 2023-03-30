# syntax=docker/dockerfile:1
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

# Vanilla database, migrations applied, no configs/nodes
# Persists between sessions if volume used, or can mount in external db
COPY docker/default-db.sqlite3 /repo/frontend/db.sqlite3

# Install dependencies
COPY docker/requirements.txt /repo/requirements.txt
RUN pip install -r requirements.txt

CMD ["python", "frontend/manage.py", "runserver", "0:8456"]
