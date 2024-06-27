# Firmware

Pre-built firmware binaries can be downloaded from [releases](https://gitlab.com/jamedeus/micropython-smarthome/-/releases).

## Dependencies

Building the firmware requires:
* git
* npm
* cmake
* openssl
* python venv module

On Ubuntu 24.04 these can be installed with:
```
sudo apt update
sudo apt install -y git npm cmake openssl python3.11-venv
```

Then install dependencies to build the setup page:
```
cd firmware
npm install -D
```

## Building firmware

The [build script](firmware/build.sh) compiles customized micropython ESP32 firmware containing source code for the entire project. This is primarily done to reduce memory usage (see the [official documentation](https://docs.micropython.org/en/latest/reference/manifest.html) for details).

The first time the script is run it will recursively clone the [micropython source](https://github.com/micropython/micropython.git) and [esp-idf](https://github.com/espressif/esp-idf.git), which requires 2.1 GB of disk space and may take a while. This will only happen once unless the directories are deleted.

To build the firmware simply run the script:
```
./build.sh
```

This will create `firmware/firmware.bin`, which can be flashed to an ESP32 with the flash script (see below).

When the script is run multiple times it will append new/changed files to the previous build. This is faster and won't cause problems unless source files were deleted (not just modified), in which case they will still be included in the next firmware build. Run a fresh build to fix this:
```
./build.sh fresh
# OR
./build.sh --f
```

This will delete the previous build and start from scratch.

## Flashing firmware

The [flash script](firmware/flash.sh) requires [esptool](https://pypi.org/project/esptool/), which can be installed with pip:
```
pip install esptool
```

To flash the most-recent build (`firmware/firmware.bin`) call the script with the path to your ESP32 UART:
```
./flash.sh /dev/ttyUSB0
```

To flash a specific firmware binary pass a path as the second argument:
```
./flash.sh /dev/ttyUSB0 firmware_0.1.bin
```

## Setup

After the firmware is flashed the ESP32 will broadcast an access point with an SSID starting with "Smarthome_Setup". Connect to this network and use the setup page to enter your wifi credentials and a webrepl password. The setup page should open automatically (captive portal), if it doesn't open `https://192.168.4.1` in your browser.

You will receive a self-signed certificate warning when the setup page loads, this is normal. The setup server uses self-signed SSL certificates to encrypt your wifi credentials (without this anything you enter on the form could easily be intercepted by anyone within wifi range). Click trust/proceed anyway to ignore the warning (varies depending on browser).

Once the ESP32 receives valid wifi credentials it will save them to a config file, reboot, and connect to your wifi network. Use the IP address that appears on the setup page to configure devices and sensors (you can configure these with the frontend or CLI tools).

iOS note: The SSL warning popup that appears right after connecting sometimes disappears after 10-15 seconds and does not appear again, preventing the setup page from being accessed. Click "Continue" at the top of the popup immediately to avoid this, or use a different device for setup (recommended).

<p align="center">
  <img src="https://gitlab.com/jamedeus/micropython-smarthome/-/raw/master/firmware/screenshots/setup_page.png" width="30%" alt="Setup page form">
  <img src="https://gitlab.com/jamedeus/micropython-smarthome/-/raw/master/firmware/screenshots/setup_complete.png" width="30%" alt="Setup complete">
</p>
