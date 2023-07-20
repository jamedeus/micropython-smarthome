# syntax=docker/dockerfile:1

# Build: sudo docker build -t smarthome_mock_receiver:0.1 . -f Dockerfile

FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mock_command_receiver.py .
CMD ["python3", "mock_command_receiver.py"]
