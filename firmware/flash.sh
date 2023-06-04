#!/bin/bash

if [[ -e $1 ]]; then
    esptool.py --port $1 erase_flash && \
    esptool.py --chip esp32 --port $1 --baud 460800 write_flash -z 0x1000 firmware.bin || \
    printf "\nERROR: Failed to flash device $1\n"
else
    printf "Must pass target device:\n"
    printf "./flash.sh /dev/ttyUSB0\n"
    exit 1
fi
