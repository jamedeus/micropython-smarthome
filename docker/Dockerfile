# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REPO_DIR="/repo/"
ENV CONFIG_DIR="/repo/config/"
ENV NODE_PASSWD="password"
WORKDIR /repo

COPY docker/requirements.txt /repo/requirements.txt
COPY frontend/manage.py /repo/frontend/manage.py
COPY frontend/api /repo/frontend/api
COPY frontend/node_configuration /repo/frontend/node_configuration
COPY frontend/frontend /repo/frontend/frontend
COPY lib /repo/lib
COPY devices /repo/devices
COPY sensors /repo/sensors
COPY ir-remote /repo/ir-remote
COPY Api.py /repo/Api.py
COPY Config.py /repo/Config.py
COPY Group.py /repo/Group.py
COPY SoftwareTimer.py /repo/SoftwareTimer.py
COPY boot.py /repo/boot.py

RUN pip install -r requirements.txt

CMD ["python", "frontend/manage.py", "runserver", "0:8456"]
