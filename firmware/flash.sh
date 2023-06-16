#!/bin/bash

# Flash firmware binaries to the port specified in argument.
# Uses the latest release by default, accepts optional 2nd
# argument (path to binary) to flash a specific release.


# Get target port (or print error if arg omitted)
if [[ -e $1 ]]; then
    target=$1
else
    printf "Must pass target device:\n"
    printf "./flash.sh /dev/ttyUSB0\n"
    exit 1
fi

# Get firmware release (or default to latest if arg omitted)
if [[ $2 ]]; then
    if [[ -e $2 ]]; then
        firmware=$2
    else
        printf "ERROR: $2 not found\n"
        exit 1
    fi
else
    # Get latest firmware by version number (may break if renamed)
    firmware=`\ls firmware*.bin | sort -V | tail -n 1`
fi

# Flash esp32
printf "Flashing $firmware to $target\n\n"
esptool.py --port $target erase_flash && \
esptool.py --chip esp32 --port $target --baud 460800 write_flash -z 0x1000 $firmware || \
printf "\nERROR: Failed to flash $firmware to $target\n"
