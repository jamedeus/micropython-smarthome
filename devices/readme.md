# Devices Module

This module contains hardware drivers for all supported devices.

The metadata directory contains metadata used to integrate each class with various tools (config generation, provisioning, etc).

## Development

Adding new device types requires 2 files:
- A micropython device class which interfaces with the hardware and integrates it into the API
- A JSON metadata file used to integrate the device with client-side tooling

Some hardware devices (especially i2c devices) may require driver libraries that are not part of the micropython stdlib, these should be placed in [`lib/`](lib/).

### Naming Conventions

Devices are identified by 2 names:
- Class name: The literal class name from the micropython driver, written in CamelCase
- Config name: The string used for the config file `_type` parameter, written in lowercase with hyphens separating words

Both names are used in a mapping dict which controls which class is instantiated at boot time (see `hardware_classes` in [Config.py](core/Config.py)).

Two names are required because multiple hardware types can share a single class. For example, the [Tplink](devices/Tplink.py) class is used for both smart dimmers and smart bulbs, which have different API call syntax. The `_type` parameter determines which syntax is used in this case. This approach allows much more code reuse than maintaining separate classes for each.

### Sensor Class

All device classes must subclass [Device.py](devices/Device.py), which is itself a subclass of [Instance.py](core/Instance.py). These provide methods required to interface with the API, including `enable`, `disable`, `set_rule`, etc. These can be extended or overridden as needed.

All device classes **must** include a `send` method which accepts a boolean argument and contains the logic to toggle the physical device state. When the argument is True the device turns on, when False the device turns off. The `send` method should return:
- `True` when the device was turned on/off successfully
- `False` when the device failed to turn on/off

By default all devices support the rules `Enabled` and `Disabled`. If more rules are required the device must include a `validator` method. This method accepts a rule as argument, returns `False` if it is invalid, and returns the rule if it is valid. Returning a modified rule is encouraged in some situations - for example, a class which expects an integer rule should return `int(rule)` to avoid incorrectly accepting string representations of integers.

### Sensor Manifest

The JSON metadata must follow this syntax:
```
{
    "config_name": "",
    "class_name": "",
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

Parameters:
- `config_name`: The config file `_type` parameter, lowercase with hyphens between words.
- `class_name`: The name of the device class in your micropython file, CamelCase.
- `dependencies`: A list of relative paths to all dependencies. This should include your device class, the `Sensor.py` and `core/Instance.py` base classes. If your device requires a driver from `lib/` then it must also be included (see [Thermostat.json](sensors/metadata/Thermostat.json) for an example).
- `config_template`: A full template of the hardware-level config file for the device type.
    - All parameters in the example above are required, but more can be added (for example, an `ip` parameter for network devices).
    - The `placeholder` keyword indicates that the [config generator script](CLI/config_generator.py) should prompt the user for input.
    - The `_type` parameter must be pre-filled with the same value as `config_name`.
    - The `schedule` parameter must be empty
- `rule_prompt`: Determines which rule prompt is shown by the config generator script (in the future this will also determine configuration options in the web frontend). Available options:
    - `standard`: User may select "Enabled" or "Disabled"
    - `float_range`: User may select a float, "Enabled", or "Disabled"
    - `int_range`: User may select an integer, "Enabled", or "Disabled"
    - `int_or_fade`: User may select an integer, fade rule, "Enabled", or "Disabled"
    - `on_off`: User may select "On", "Off", "Enabled", or "Disabled"
- `rule_limits`: Required for devices which accept int/float rules, ignored for all others. Should contain 2 integers representing the minimum and maximum supported rules.

### Integrating with client-side tools

The following changes must be made when a new device class is added:
- [ ] [`Config.hardware_classes`](core/Config.py): Add the `_type` parameter as key and the class name as value
- [ ] [`firmware/manifest.py`](firmware/manifest.py): Add a module statement pointing to the new device class
- [ ] [`util/instance_validators.py`](util/instance_validators.py): Add a validator function for the new class, typically you can copy the validator method and return True instead of the rule user-selectable parameters

Once the above changes have been made, run the unit tests and fix anything that fails. At a minimum the module will need to be added to [`test_provision.py](tests/cli/test_provision.py) in the `test_provision_unit_tests` test case.
