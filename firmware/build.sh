#!/bin/bash


# Clone esp-idf devkit, check out branch compatible with micropython, install
clone_esp_idf() {
    git clone https://github.com/espressif/esp-idf.git
    cd esp-idf
    git checkout v4.4
    git submodule update --init --recursive
    ./install.sh
    cd ..
}


# Source esp-idf env vars required for micropython build
source_esp_idf() {
    cd esp-idf
    source export.sh
    cd ..
}


# Clone micropython repo, compile build tools
clone_micropython() {
    git clone --recurse-submodules https://github.com/micropython/micropython.git
    cd micropython
    make -C mpy-cross
    cd ports/esp32
    make submodules
    cd ../../..
}


# Copy project source to build modules dir
# Compiled to mpy and frozen into firmware
copy_repo() {
    target="`pwd`/micropython/ports/esp32/modules/"

    # Copy dependencies from firmware dir
    \cp _boot.py main.py setup.py $target

    # Copy dependencies from main dir
    cd ..
    \cp -f Api.py Config.py Group.py SoftwareTimer.py util.py $target

    # Copy device and sensor classes
    \cp -f devices/* sensors/* $target

    # Copy libraries
    \cp -rf lib $target

    cd firmware/
}


# Compile micropython firmware
# Append to existing build if present
build() {
    cd micropython/ports/esp32
    make BOARD=GENERIC
    cp build-GENERIC/firmware.bin ../../..
    cd ../../..
}


# Remove existing build (if present), recompile
# Slower but necessary after deleteing modules (still in existing build)
fresh_build() {
    rm -rf micropython/ports/esp32/build-GENERIC
    build
}


# Clone dependencies if they don't exist
if [[ ! -d esp-idf ]]; then
    clone_esp_idf
fi
if [[ ! -d micropython ]]; then
    clone_micropython
fi


# Copy project source to build modules dir, set env vars
copy_repo
source_esp_idf


# Update existing build unless user passed fresh arg
if [[ $1 == "f" || $1 == "--f" || $1 == "fresh" ]]; then
    fresh_build
else
    build
fi
