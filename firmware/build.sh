#!/bin/bash

# See readme for current compatible idf version:
# https://github.com/micropython/micropython/blob/master/ports/esp32/README.md
MICROPYTHON_TAG="v1.23.0"
ESP_IDF_TAG="v5.0.4"

# Get path to directory containing script (firmware dir)
FIRMWARE_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Get sub paths
MANIFEST="$FIRMWARE_DIR/manifest.py"
ESP_IDF_DIR="$FIRMWARE_DIR/esp-idf"
MICROPYTHON_DIR="$FIRMWARE_DIR/micropython"
ESP32_PORT_DIR="$FIRMWARE_DIR/micropython/ports/esp32"


# Clone esp-idf devkit, check out branch compatible with micropython, install
clone_esp_idf() {
    git clone -b $ESP_IDF_TAG --recursive https://github.com/espressif/esp-idf.git
    cd "$ESP_IDF_DIR" || { printf "FATAL: Failed to clone esp-idf\n"; exit 1; }
    ./install.sh
    cd "$FIRMWARE_DIR" || { printf "FATAL: Failed to return to firmware dir\n"; exit 1; }
}


# Source esp-idf env vars required for micropython build
source_esp_idf() {
    source "$ESP_IDF_DIR/export.sh" || { printf "FATAL: Failed to source esp-idf\n"; exit 1; }
}


# Clone micropython repo, compile build tools
clone_micropython() {
    git clone --depth 1 -b $MICROPYTHON_TAG https://github.com/micropython/micropython.git
    cd "$MICROPYTHON_DIR" || { printf "FATAL: Failed to clone micropython\n"; exit 1; }
    make -C mpy-cross
    cd "$ESP32_PORT_DIR" || { printf "FATAL: Unable to find micropython esp32 port\n"; exit 1; }
    make submodules
    cd "$FIRMWARE_DIR" || { printf "FATAL: Failed to return to firmware dir\n"; exit 1; }
}


# Compile tailwind stylesheet, insert into html, convert to python module
# Module frozen into firmware, contains single variable with page contents
package_setup_page() {
    # Working copy (do not modify source)
    cp setup.html setup.html.tmp

    # Recompile tailwind stylesheet
    npx tailwindcss -o tailwind.css --minify

    # Insert tailwind.css into setup.html.tmp after <style> opening tag
    sed -i "/<style>/r tailwind.css" setup.html.tmp
    rm tailwind.css

    # Minify HTML - single line, remove comments, etc
    npx html-minifier \
        --collapse-whitespace \
        --remove-comments \
        --remove-optional-tags \
        --remove-redundant-attributes \
        --remove-empty-attributes \
        --remove-script-type-attributes \
        --remove-tag-whitespace \
        --use-short-doctype \
        --minify-js "{\"mangle\": {\"toplevel\": true}}" \
        setup.html.tmp -o setup.html.tmp

    # Prepend variable declaration + opening quotes, append closing quotes
    sed -i '1s;^;setup_page = """;' setup.html.tmp
    echo "\"\"\"" >> setup.html.tmp

    # Rename, move to build modules
    mv setup.html.tmp micropython/ports/esp32/modules/setup_page.py
}


# Generate self-signed SSL certificates used to serve the setup page over HTTPS
generate_ssl_certs() {
    openssl ecparam -name prime256v1 -genkey -noout -out key.der -outform DER
    openssl req -new -x509 -key key.der -out cert.der -outform DER -days 365 -nodes \
        -subj "/CN=micropython-smarthome/O=https:\/\/gitlab.com\/jamedeus\/micropython-smarthome"

    # Parse key and cert as hexadecimal, write to python vars
    key_hex=$(xxd -p key.der | tr -d '\n' | sed 's/\(..\)/\\x\1/g')
    cert_hex=$(xxd -p cert.der | tr -d '\n' | sed 's/\(..\)/\\x\1/g')
    echo "KEY = b\"${key_hex}\"" >> setup_ssl_certs.py
    echo "CERT = b\"${cert_hex}\"" >> setup_ssl_certs.py

    rm key.der cert.der
}


# Compile micropython firmware
# Updates existing build if present
build() {
    cd "$ESP32_PORT_DIR" || { printf "FATAL: Unable to find micropython esp32 port\n"; exit 1; }
    make submodules
    make BOARD=ESP32_GENERIC FROZEN_MANIFEST="$MANIFEST" || exit
    cp build-ESP32_GENERIC/firmware.bin ../../..
    cd "$FIRMWARE_DIR" || { printf "FATAL: Failed to return to firmware dir\n"; exit 1; }
}


# Remove existing build (if present), recompile
# Slower but necessary after deleteing modules (still in existing build)
fresh_build() {
    rm -rf "$ESP32_PORT_DIR/build-ESP32_GENERIC"
    build
}


# Must be in firmware dir
if [[ $(pwd) != "$FIRMWARE_DIR" ]]; then
    START_DIR=$(pwd)
    cd "$FIRMWARE_DIR" || { printf "FATAL: Failed to change to firmware dir\n"; exit 1; }
fi

# Clone dependencies if they don't exist
if [[ ! -d $ESP_IDF_DIR ]]; then
    clone_esp_idf
fi
if [[ ! -d $MICROPYTHON_DIR ]]; then
    clone_micropython
fi

# Set ESP IDF env vars
source_esp_idf

# Build setup page
package_setup_page

# Generate setup page SSL certs if they don't exist
if [[ ! -f $FIRMWARE_DIR/setup_ssl_certs.py ]]; then
    generate_ssl_certs
fi

# Update existing build unless user passed fresh arg
if [[ $1 == "f" || $1 == "--f" || $1 == "fresh" ]]; then
    fresh_build
else
    build
fi

# Return to starting dir
if [[ $START_DIR ]]; then
    cd "$START_DIR" || exit
fi
