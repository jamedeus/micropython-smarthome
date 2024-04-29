[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Command Line Tools

These tools enable full management of smarthome nodes from the command line, duplicating all frontend functionality.

Tools:
* [api_client.py](CLI/api_client.py): Send API commands and view responses
* [config_generator.py](CLI/config_generator.py): Generate new config files, edit existing config files
* [provision.py](CLI/provision.py): Upload config files and all their dependencies to new nodes

## Setup

The [util module](util/) must be installed before using the CLI tools:
```
pip3 install -e util/
```

To install the bash completions simply copy them to the global directory:
```
sudo cp CLI/bash_completion/* /etc/bash_completion.d/
```

The changes will take effect after opening a new shell.

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

## Config Generator

The config generator runs an interactive [questionary-based](https://questionary.readthedocs.io/en/stable/) menu used to generate config files. Simply call the script and follow the prompts:
```
$ ./CLI/config_generator.py
? Enter a descriptive name for this node: Example
? Enter floor number: 2
? Enter a brief note about the node's physical location: CLI Readme
? Enter wifi SSID (2.4 GHz only): mynet
? Enter wifi password: *****************
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
