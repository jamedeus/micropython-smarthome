[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Command Line Tools

These tools can be used to create and manage ESP32 nodes from the command line, including all functionality of the web frontend.
* Send API commands and view responses
* Generate config files
* Edit existing config files
* Upload config files and their dependencies to new ESP32 nodes
* View ESP32 node logs remotely

The interactive menu displayed by [smarthome_cli.py](CLI/smarthome_cli.py) can be used to access all functions of the other scripts, no command line arguments are required.

For documentation on each script called by the interactive menu see [here](CLI/readme_advanced.md).

## Setup

The interactive menu can be called using pipenv or installed as a global CLI tool. Global installation is recommended if you plan to use the CLI tools heavily as this will allow them to be called from any directory.

### Pipenv (testing)

Install dependencies:
```
pipenv install
```

Then call the script using the virtual environment:
```
pipenv run CLI/smarthome_cli.py
```

### Global installation

Install the `smarthome_cli` package (includes all dependencies) by running this in the repository root:
```
pip install .
```

The interactive script can now be accessed from any directory by calling `smarthome_cli`.

## Configuration

A setup prompt will appear the first time `smarthome_cli` is run:
```
$ smarthome_cli

Setup:
? Set config file directory? (Y/n)
```

Follow the prompts to customize:
* Config file directory: The location where ESP32 config files will be saved
    * The default is fine in most cases
    * You do not need to remember this directory when using the interactive script
* Webrepl password: The password used to push updates to ESP32s
    * This must match the password set during ESP32 wifi setup (should be the same for all nodes)
* Django backend address: The [web frontend](frontend/README.md) base URL (optional)
    * If set changes made in the web frontend will automatically sync to CLI and vice versa

These can be changed at any time by calling `smarthome_cli` and selecting `Settings` at the main menu.

Settings are stored in `cli_config.json` inside your user config directory (usually `~/.config/smarthome_cli/cli_config.json` on unix, `AppData` on windows).

## Usage

An interactive menu will appear when [smarthome_cli](CLI/smarthome_cli.py) is called:
```
$ smarthome_cli

What would you like to do? (Use arrow keys)
 » API client
   Manage nodes
   Manage schedule keywords
   Settings
   Done
```

Each option displays a sub-menu:
* `API client`: Prompts user to select a target node, then displays an interactive menu used to make API calls
* `Manage nodes`: Contains options to generate config files, edit existing node config files, manage existing nodes, view logs, etc
* `Manage schedule keywords`: Contains options used to create, edit, and delete schedule keywords
* `Settings`: Contains configuration and django sync options

If a django backend is configured in `cli_config.json` the script will automatically syncronize with the django database:
* When the script is started current nodes and schedule keywords are downloaded from the backend and written to `cli_config.json`
* When nodes are created or deleted an API call is sent to the django backend
* When schedule keywords are created, edited, or deleted an API call is sent to the django backend
* When an existing node's IP is changed an API call is sent to the django backend

This ensures that changes made from CLI will appear on the web frontend and vice versa.

