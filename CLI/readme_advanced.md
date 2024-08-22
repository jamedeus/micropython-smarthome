[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Legacy tools

This page documents individual tools called by the interactive menus in [`smarthome_cli`](CLI/smarthome_cli.py). These were originally standalone tools but have been deprecated in favor of the more user-friendly combined script. All of the arguments documented below can also be passed to `smarthome_cli` (see [here](CLI/readme.md#command-line-arguments) for details). This page is mostly retained for development documentation.

Tools:
* [`api_client.py`](CLI/api_client.py): Send API commands and view responses
* [`config_generator.py`](CLI/config_generator.py): Generate new config files, edit existing config files
* [`provision.py`](CLI/provision.py): Upload config files and all their dependencies to new nodes

## Setup

Install dependencies and activate the venv:
```
pipenv install --dev
pipenv shell
```

In addition to PyPi packages this also adds the [`util`](util/) package to the python path, which contains several modules imported by these tools.

Once the venv is activated tools can be called directly as scripts:
```
./api_client.py
./config_generator.py
./provision.py
```

### Bash completions

To install bash completions for scripts which take command line arguments copy this line:
```
sudo cp CLI/bash_completion/* /etc/bash_completion.d/
```

The changes will take effect after opening a new shell.

Note: Bash completion will not work if `~/.config/smarthome_cli/cli_config.json` does not exist (see below).

### Configuration

Names of existing ESP32 nodes are stored in `~/.config/smarthome_cli/cli_config.json`. This file will be created automatically the first time a node is provisioned, or when `smarthome_cli.py` is called.

Config syntax:
```
{
  "nodes": {
    "node-friendly-name": "192.168.1.123"
  },
  "schedule_keywords": {
    "sunrise": "06:00",
    "sunset": "18:00"
  },
  "webrepl_password": "password",
  "config_directory": "/home/user/.config/smarthome_cli/config_files",
  "django_backend": "http://127.0.0.1:8999",
  "ignore_ssl_errors": false
}
```

Keys:
* `nodes`: Contains node names as keys and IPs as values. Names can be used as CLI arguments for `api_client.py` and `provision.py` (see below).
* `schedule_keywords`: Contains keyword names as values and timestamps (HH:MM) as values. These are automatically added to new config files.
* `webrepl_password`: The password used to upload config files to ESP32 nodes. This must match the password set during ESP32 wifi setup and should be the same for all ESP32 nodes.
* `config_directory`: The location where ESP32 config files are stored.
* `django_backend`: Optional, address of a django web app to syncronize with.
    * If set current django database contents will be requested each time a CLI tool is called.
    * When nodes or keywords are created or deleted using CLI tools the same changes will be made in the django database.
* `ignore_ssl_errors`: Optional, skips SSL certificate verification if true (allows using https with self-signed certificates)

The config file can be modified using the settings menu in `CLI/smarthome_cli.py`.

# Tools

## API Client

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

## Config Generator

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

Finished config files will be written to the `config_directory` specified in `cli_config.json`. By default this is `~/.config/smarthome_cli/config_files/`.

The script can also be used to edit an existing config file by passing a path as argument:
```
./CLI/config_generator.py ~/.config/smarthome_cli/config_files/example.json
```

The config generator has no bash completions, everything is in the interactive menu.

## Provision

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
./CLI/provision.py --ip 192.168.1.123 --config ~/.config/smarthome_cli/config_files/node1.json --password example

# Upload to new node using default password
./CLI/provision.py --ip 192.168.1.123 --config ~/.config/smarthome_cli/config_files/node1.json

# Upload unit tests
./CLI/provision.py --test 192.168.1.123

# Re-provision all nodes
./CLI/provision.py --all

# Re-provision a single node
./CLI/provision.py node1
```

When a new node is successfully provisioned it will be automatically added to `cli_config.json`.
