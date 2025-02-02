# Devices Module

This module contains hardware drivers for all supported devices.

Metadata for each device can be found in [util/metadata/devices](util/metadata/devices).

## Development

Adding new device types requires 2 files:
- A micropython device class which interfaces with the hardware and integrates it into the API
- A JSON metadata file used to integrate the device with client-side tools (web frontend and CLI tools)

Some hardware devices (especially i2c devices) may require driver libraries that are not part of the micropython stdlib, these should be placed in [`lib/`](lib/).

### Naming Conventions

Devices are identified by 2 names:
- Class name: The literal class name from the micropython driver, written in CamelCase
- Config name: The string used for the config file `_type` parameter, written in lowercase with hyphens separating words

Both names are used in a mapping dict that controls which class is instantiated at boot time. The mapping dict is built when firmware is compiled (see [lib/build_hardware_classes.py](lib/build_hardware_classes.py)) and frozen into the firmware.

Two names are required because multiple hardware types can share a single class. For example, the [Tplink](devices/Tplink.py) class is used for both smart dimmers and smart bulbs, which have different API call syntax. The `_type` parameter determines which syntax is used in this case. This approach allows much more code reuse than maintaining separate classes for each.

### Device Class

All device classes must subclass [Device.py](devices/Device.py), which is itself a subclass of [Instance.py](core/Instance.py). These provide methods required to interface with the API, including `enable`, `disable`, `set_rule`, etc. These can be extended or overridden as needed.

#### Send method

All device classes **must** include a `send` method which accepts a boolean argument and contains the logic to toggle the physical device state. When the argument is True the device turns on, when False the device turns off. The `send` method should return:
- `True` when the device was turned on/off successfully
- `False` when the device failed to turn on/off

#### Device rules

By default all devices support the rules `Enabled` and `Disabled`. If more rules are required the device must include a `validator` method. This method accepts a rule as argument, returns `False` if it is invalid, and returns the rule if it is valid. Returning a modified rule is encouraged in some situations - for example, a class which expects an integer rule should return `int(rule)` to avoid incorrectly accepting string representations of integers.

### Device Metadata

Metadata files must have the same name as the corresponding class (eg `Wled.py` and `Wled.json`) and should be placed in [util/metadata/devices](util/metadata/devices). Adding a metadata file to this directory will automatically integrate the device type with all client-side tools - no changes are needed in the webapp or CLI tool code.

The JSON metadata must follow this syntax:
```
{
    "config_name": "",
    "class_name": "",
    "display_name": "",
    "description": "",
    "dependencies": [
        "devices/Device.py",
        "core/Instance.py"
    ],
    "config_template": {
        "_type": "",
        "nickname": "placeholder",
        "default_rule": "placeholder",
        "schedule": {}
    },
    "rule_prompt": "",
    "rule_limits": []
}
```

#### Parameters

- `config_name`: The config file `_type` parameter, lowercase with hyphens between words.
- `class_name`: The name of the device class in your micropython file, CamelCase.
- `display_name`: The name displayed on config generator type select options (CLI and web frontend).
- `dependencies`: A list of relative paths to all dependencies. This should include your device class, the `Device.py` and `core/Instance.py` base classes. If your device requires a driver from `lib/` then it must also be included (see [Thermostat.json](sensors/metadata/Thermostat.json) for an example).
- `config_template`: A full template of the hardware-level config file for the device type.
    - All parameters in the example above are required, but more can be added (for example, an `ip` parameter for network devices).
    - The `placeholder` keyword indicates that the [config generator script](CLI/config_generator.py) should prompt the user for input.
    - The `_type` parameter must be pre-filled with the same value as `config_name`.
    - The `schedule` parameter must be empty
- `rule_prompt`: Determines which rule prompt is shown by the CLI and web config generators, which input appears on the web frontend, and which [rule validator](util/instance_validators.py) function the config validator will use for this device. Available options:
    - `standard`: User may select "Enabled" or "Disabled"
    - `float_range`: User may select a float, "Enabled", or "Disabled"
    - `int_range`: User may select an integer, "Enabled", or "Disabled"
    - `int_or_fade`: User may select an integer, fade rule, "Enabled", or "Disabled"
    - `on_off`: User may select "On", "Off", "Enabled", or "Disabled"
- `rule_limits`: Required for devices which accept int/float rules, ignored for all others. Should contain 2 integers representing the minimum and maximum supported rules.

### Integrating into firmware

Add a module statement to [`firmware/manifest.py`](firmware/manifest.py) pointing to the new device class. If the metadata `dependencies` key contains additional libraries add a module statement for each of them too. These modules will be compiled into the firmware the next time it is build.

Before building the firmware run all unit tests (including the CLI and frontend tests) and fix anything that fails. At a minimum the module will need to be added to:
- [`test_provision.py`](tests/cli/test_provision.py) in the `test_provision_unit_tests` test case.
- [django unit test constants](frontend/api/unit_test_helpers.py) in the `instance_metadata` object.
- [react unit test mock metadata](frontend/src/testUtils/mockMetadataContext.js) in the `edit_config_metadata` and `api_card_metadata` objects.

See [here](firmware/readme.md) for firmware build instructions.
