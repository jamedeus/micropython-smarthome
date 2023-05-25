#!/bin/bash

if [[ $1 == "upload" ]]; then
    python3 provision.py -c tests/config.json -ip 192.168.1.213
    sleep 30
fi

python3 -m unittest discover -s tests -p client_test*.py
