[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Command Line Tools

These tools can be used to create and manage ESP32 nodes from the command line, including all functionality of the web frontend.
* Send API commands and view responses
* Generate config files
* Edit existing config files
* Upload config files and their dependencies to new ESP32 nodes
* View ESP32 node logs remotely

The interactive menu displayed by [`smarthome_cli.py`](CLI/smarthome_cli.py) can be used to access all functions of the other scripts, no command line arguments are required.

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

## Interactive prompt

An interactive menu appears when [`smarthome_cli`](CLI/smarthome_cli.py) is called:
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

### Command line arguments

The script supports command line arguments as a shortcut instead of going throught the interactive prompt. This can be useful for power users or for scripting.

#### API commands

Call with `--api` to go directly to the interactive API prompt:
```
$ smarthome_cli --api
? Select target node (Use arrow keys)
 » kitchen
   bedroom
   living-room
```

To run a single command with no interactive prompt use the following syntax:
```
smarthome_cli --api <target> <command> [args]
```
* `target` must be an IP address or friendly name of an existing node from `cli_config.json`.
* `command` must be a valid API endpoint (prints full list of options if missing).
* `args` are required for some endpoints (see endpoint options for syntax).

This can be very useful for scripting or bash aliases.

#### Config generator

The `--config` argument skips the menu and opens the config generation prompt:
```
$ smarthome_cli --config
? Enter a descriptive name for this node:
```

To edit an existing config file add its path as the second argument:
```
$ smarthome_cli --config ~/.config/smarthome_cli/config_files/bedroom.json
Editing existing config:
...
```

Finished config files will be saved to the `config_directory` set in `cli_config.json`.

Note: The user will not be prompted to upload config files when finished. Use the [interactive menu](#interactive-prompt) to be automatically prompted.

#### Provisioner

Config files can be uploaded to nodes with no interactive prompt using the `--provision` argument, which requires additional arguments.

To reprovision all existing nodes in `cli_config.json` pass `--all` as the second argument:
```
$ smarthome_cli --provision --all
```

To reprovision a single node pass its name as the second argument:
```
$ smarthome_cli --provision bedroom
```

Specify an arbitrary config file path with `--config` and an arbitrary IPv4 address with `--ip`:
```
$ smarthome_cli --provision --config thermostat.json --ip 192.168.1.123
```
* This will add the node to `cli_config.json` just like the interactive script.

To upload firmware unit tests to an arbitrary IP use `--test`:
```
$ pipenv run CLI/smarthome_cli.py --provision --test 192.168.1.123
```
* NOTE: This does not work when smarthome_cli is installed globally (package doesn't include tests), the [`smarthome_cli.py`](CLI/smarthome_cli.py) script in the repo must be called directly.
* See [Firmware test documentation](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/tests?ref_type=heads#firmware) for details about running tests.
