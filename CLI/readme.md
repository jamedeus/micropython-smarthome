[![pipeline status](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/pipeline.svg)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)
[![CLI tool coverage report](https://gitlab.com/jamedeus/micropython-smarthome/badges/master/coverage.svg?job=test_cli&key_text=CLI+Coverage&key_width=90)](https://gitlab.com/jamedeus/micropython-smarthome/-/commits/master)

# Command Line Tools

These tools expose all functionality of the [web app](frontend/README.md) from the command line. They can be configured to syncronize data with the web app, or used standalone with no webapp.

The main [`smarthome_cli.py`](CLI/smarthome_cli.py) script displays an interactive menu which can be used to:
* Send API commands to ESP32 nodes and view responses
* Generate new ESP32 config files
* Edit existing ESP32 config files
* Upload config files and dependencies to ESP32 nodes over wifi
* Manage schedule keywords (used to bulk-manage ESP32 schedule rules)
* View ESP32 node logs over wifi

Many of these functions can also be used non-interactively by calling `smarthome_cli` with command line arguments, which can be useful for scripting.

The other modules in this directory are imported by `smarthome_cli` and generally shouldn't be used on their own, see [here](CLI/readme_advanced.md) for detailed documentation.

## Setup

Dependencies can be installed using pipenv (less conventient), or the whole package can be installed as a global CLI tool.

### Global installation

Install the `smarthome_cli` package (includes all dependencies) by running this in the repository root directory:
```
pip install .
```

The interactive script can now be accessed from any directory by calling `smarthome_cli`.

### Pipenv (testing)

Install dependencies:
```
pipenv install
```

Then call the script using the virtual environment:
```
pipenv run CLI/smarthome_cli.py
```

## Configuration

A setup prompt will appear the first time `smarthome_cli` is called, all questions are optional:
```
$ smarthome_cli

Setup:
? Set config file directory? Yes
? Enter absolute path to config directory /home/vm/.config/smarthome_cli/config_files
? Set webrepl password? Yes
? Enter password (must match password entered during node setup) password
? Automatically sync config with web frontend? Yes
? Enter django address: https://smarthome.lan
Setup complete
```

Follow these prompts to customize:
* **Config file directory**: The location where ESP32 config files will be saved
    * The default is fine in most cases
    * You do not need to remember this directory when using the interactive script
* **Webrepl password**: The password used to push updates to ESP32s
    * This must match the password set during ESP32 wifi setup (should be the same for all nodes)
* **Django address**: The [web frontend](frontend/README.md) base URL (optional)
    * If this is set changes made in the web app will automatically sync to CLI and vice versa

Settings can be changed at any time by calling `smarthome_cli` and selecting `Settings` at the main menu.

Configuration is stored in `cli_config.json` inside your user config directory (usually `~/.config/smarthome_cli/cli_config.json` on unix, `AppData` on windows).

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

Each option displays a sub-menu when selected, see below for details.

### Api client

When selected you will be prompted to select an existing node or enter an IP address:
```
What would you like to do? API client
? Select target node (Use arrow keys)
 » kitchen
   bedroom
   living-room
   Enter node IP
   Done
```

After selecting a node the script will display a status object with the current state of all devices and sensors. This is updated after each API call.

The second prompt shows all API endpoints supported by the target node:
```
? Select command (Use arrow keys)
 » reboot
   disable
   disable_in
   enable
   enable_in
   set_rule
   increment_rule
   reset_rule
   reset_all_rules
   get_schedule_rules
   add_rule
   remove_rule
   save_rules
   get_schedule_keywords
   add_schedule_keyword
   remove_schedule_keyword
   save_schedule_keywords
   get_attributes
   clear_log
   condition_met
   trigger_sensor
   turn_on
   turn_off
   set_gps_coords
   Done
```

Some of these require arguments (eg `set_rule`) and will display additional prompts. Once a complete API call is entered the response will be shown:
```
? Select command turn_on
? Select device or sensor device1
{
    "On": "device1"
}
 Press any key to continue...
```

After each command you will be taken back to the endpoint selection, allowing multiple commands to be sent to a single node. Select `Done` to exit the loop and go back to the main menu.

### Manage nodes

The manage nodes menu contains options to generate and edit config files, upload config files, change node IP addresses, delete nodes, and view ESP32 logs:
```
What would you like to do? Manage nodes
? Manage nodes (Use arrow keys)
 » Create new node
   Edit existing node config
   Reupload config to node
   Upload config file from disk
   Change existing node IP
   Delete existing node
   View node log
   Done
```

Each option will display additional prompts and instructions when selected.

After generating a new config file you will be prompted to enter an IP address to upload it to. This is optional, the config will be saved to disk and can be uploaded later by selecting `Upload config file from disk`.

When a node's IP is changed it's config file will be uploaded to the new IP, but the existing node will not be affected (remember to unplug it). This also applies to deleted nodes.

Viewing logs can be useful for debugging. The log is downloaded over webrepl and displayed in a pager (press `q` to exit). Once the pager is exited you will have the option to write the log to disk.

### Manage schedule keywords

Schedule keywords are aliases for HH:MM timestamps and can be used instead of timestamps in node schedule rules. Keyword rules can be added during config generation or with API calls to existing nodes. Using schedule keywords allows rules on multiple nodes to be changed with a single action. This is similar to the concept of scenes except that they trigger automatically at a certain time of day.

The schedule keywords prompt allows keywords to be created, edited, or deleted:
```
What would you like to do? Manage schedule keywords
? Manage schedule keywords (Use arrow keys)
 » Add new schedule keyword
   Edit schedule keyword
   Delete schedule keyword
   Done
```

Changes are automatically sent to all existing nodes, which will immediately update their schedule rules.

### Settings

The settings option can be used to change values set during initial setup, plus additional options if a django backend is configured:
```
What would you like to do? Settings
? Settings menu (Use arrow keys)
 » Set django address
   Sync nodes and keywords from django
   Download all config files from django
   Change config directory
   Change webrepl password
   Done
```

See [configuration](#configuration) for details about django address, config directory, and webrepl password.

The `Sync nodes and keywords from django` option updates `cli_config.json` with the current contents of the django database. This happens automatically on startup and usually doesn't need to be called manually.

The `Download all config files from django` option writes config files for all existing nodes to the config directory set in `cli_config.json`. This is more expensive and does not happen automatically. You may want to do this after initial setup, but it is not required - when a config file is missing (eg when trying to upload it) a prompt will appear asking if you want to download it from django.

#### Django syncronization

If a django address is configured in `cli_config.json` the script will automatically syncronize with the webapp:
* When the script is started current nodes and schedule keywords are downloaded from the backend and written to `cli_config.json`
* When nodes are created or deleted an API call is sent to the django backend
* When schedule keywords are created, edited, or deleted an API call is sent to the django backend
* When an existing node's IP is changed an API call is sent to the django backend

This ensures that changes made from the command line will appear on the web app and vice versa.

## Command line arguments

The `smarthome_cli` script supports command line arguments as a shortcut instead of going through the interactive prompt. This can be useful for power users or for scripting.

### API commands

The `--api` argument goes directly to the interactive API prompt:
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
* `command` must be a valid API endpoint.
* `args` are required for some endpoints.

Calling `smarthome_cli --api <target>` with no command will print a full list of endpoint options and their required arguments.

This can be very useful for scripting or bash aliases.

### Config generator

The `--config` argument skips the menu and opens the config generation prompt:
```
$ smarthome_cli --config
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

To edit an existing config file add its path as the second argument:
```
$ smarthome_cli --config ~/.config/smarthome_cli/config_files/bedroom.json
Editing existing config:
...
```

Finished config files will be saved to the `config_directory` set in `cli_config.json`.

Note: The user will not be prompted to upload config files when finished. Use the [interactive menu](#interactive-prompt) to be automatically prompted, or use the provision arguments below.

### Provisioner

Config files can be uploaded to nodes with no interactive prompt using the `--provision` argument (requires additional arguments).

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
* If a django backend is configured this will also create the node in the django database.

To upload firmware unit tests to an arbitrary IP use `--test`:
```
$ pipenv run CLI/smarthome_cli.py --provision --test 192.168.1.123
```
* NOTE: This does not work when smarthome_cli is installed globally (package doesn't include tests), the [`smarthome_cli.py`](CLI/smarthome_cli.py) script in the repo must be called directly.
* See [Firmware test documentation](https://gitlab.com/jamedeus/micropython-smarthome/-/tree/master/tests?ref_type=heads#firmware) for details about running tests.

### Bash completions

To install bash completions for all of the commands above copy this line:
```
sudo cp CLI/bash_completion/* /etc/bash_completion.d/
```

The changes will take effect after opening a new shell.

Note: Bash completion will not work if `~/.config/smarthome_cli/cli_config.json` does not exist (see below).
