[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Command Line Tools

These tools enable full management of smarthome nodes from the command line, duplicating all frontend functionality.

Tools:
* [api_client.py](CLI/api_client.py): Send API commands and view responses
* [config_generator.py](CLI/config_generator.py): Generate new config files, edit existing config files
* [provision.py](CLI/provision.py): Upload config files and all their dependencies to new nodes
* [smarthome_cli.py](CLI/smarthome_cli.py): Interactive menu containing functionality of all other scripts

Most users will only need [smarthome_cli.py](CLI/smarthome_cli.py), which contains all functionality and is much more user-friendly. The other scripts are older and require command line arguments, but they might still be useful for power users.

## Setup

Install the CLI tools package (includes all dependencies):
```
pip install CLI/
```

The interactive script can now be accessed from any directory by calling `smarthome_cli`.

A setup prompt will appear the first time the script is run:
```
$ smarthome_cli

Setup:
? Set config file directory? (Y/n)
```

This allows you to customize:
* Config file directory: The location where ESP32 config files will be saved
    * Using the default is fine in most cases
* Webrepl password: The password used to push updates to ESP32s
    * This must match the password set during ESP32 wifi setup (should be the same for all nodes)
* Django backend address: The [web frontend](frontend/README.md) base URL (optional)
    * If set changes made in the web frontend will automatically sync to CLI and vice versa

These can be changed at any time by calling `smarthome_cli` and selecting `Settings` at the main menu.

Settings are stored in `cli_config.json` inside your site-packages directory (this will be moved somewhere that makes more sense eventually).

### Advanced

To install bash completions for scripts which take command line arguments copy this line:
```
sudo cp CLI/bash_completion/* /etc/bash_completion.d/
```

The changes will take effect after opening a new shell.

## Usage

Simply call [smarthome_cli.py](CLI/smarthome_cli.py) to display the interactive menu:
```
$ pipenv run CLI/smarthome_cli.py

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

## Advanced Users

### API Client

The API client supports all available endpoints and options. The basic syntax is:
```
./CLI/api_client.py <target> <command> [args]
```
* `target` must be an IP address or friendly name of an existing node from `cli_config.json`.
* `command` must be a valid API endpoint. Run the client with no command to see a full list of options.
* `args` are required for some endpoints, example syntax is shown if the client is run without a required argument.

The API client has extensive context-dependent bash completions:
* Suggests existing node names for first argument
* Suggests all endpoints for second argument
* Suggests device and sensor IDs for endpoints which require a device or sensor argument

When called with no arguments an interactive menu is displayed, allowing the user to select a target node and API endpoint:
```
$ ./api_client.py
? Select target node (Use arrow keys)
 » bathroom
   kitchen
   living-room
   Enter node IP
   Done
```

### Config Generator

Note: The config generator menu can also be accessed through [smarthome_cli.py](CLI/smarthome_cli.py), which also walks the user through uploading the config file to an ESP32 node. Configs generated with `config_generator.py` must be provisioned manually.

The config generator runs an interactive [questionary-based](https://questionary.readthedocs.io/en/stable/) menu used to generate config files. Simply call the script and follow the prompts:
```
$ ./CLI/config_generator.py
? Enter a descriptive name for this node: Example
? Enter floor number: 2
? Enter a brief note about the node's physical location: CLI Readme
?
Add instances? (Use arrow keys)
 » Device
   Sensor
   IR Blaster
   Done
```

The script can also be used to edit an existing config file by passing a path as argument:
```
./CLI/config_generator.py config_files/example.json
```

The config generator has no bash completions, everything is in the interactive menu.

### Provision

The provisioning script accepts multiple command line flags
* `--all`: Re-provision all nodes listed in `cli_config.json`
    * No other args are required if this option is used
* `--config`: Expects relative path to the config file to be uploaded
* `--ip`: Accepts IPv4 address that will receive the upload
* `--password`: Expects a webrepl password for the target node
    * Optional, reads password from `cli_config.json` if omitted
* `--test`: Expects an IPv4 address that will receive unit tests
    * See [Firmware test documentation](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/tests?ref_type=heads#firmware) for details

The provision script can also send over-the-air updates to existing nodes (rather than flashing new firmware). Simply call the script with the node's friendly name (from `cli_config.json`) as argument. The IP and config file specified in `cli_config.json` will be used automatically.

Example usage:
```
# Upload to new node
./CLI/provision.py --ip 192.168.1.123 --config config_files/node1.json --password example

# Upload to new node using default password
./CLI/provision.py --ip 192.168.1.123 --config config_files/node1.json

# Upload unit tests
./CLI/provision.py --test 192.168.1.123

# Re-provision all nodes
./CLI/provision.py --all

# Re-provision a single node
./CLI/provision.py node1
```

When a new node is successfully provisioned it will be automatically added to `cli_config.json`.
