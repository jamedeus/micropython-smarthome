#!/bin/bash

if [[ $1 == "upload" ]]; then
    python3 ../../CLI/provision.py --c client_test_config.json --ip 192.168.1.213
    sleep 30
fi

cd ../..
python3 -m unittest discover -v -s tests/client/ -p client_test*.py
cd tests/client/
