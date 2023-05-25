#!/bin/bash

printf "Running database migrations...\n"
python frontend/manage.py migrate
printf "\nStarting server...\n"
python frontend/manage.py runserver 0:8456
