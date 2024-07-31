# Sensors Module

This module contains hardware drivers for all supported sensors.

The metadata directory contains metadata used to integrate each class with various tools (config generation, provisioning, etc).

## Development

Adding new sensor types requires 2 files:
- A micropython sensor class which interfaces with the hardware and integrates it into the API
- A JSON metadata file used to integrate the sensor with client-side tooling

Some hardware sensors (especially i2c devices) may require driver libraries that are not part of the micropython stdlib, these should be placed in [`lib/`](lib/).

### Naming Conventions

Sensors are identified by 2 names:
- Class name: The literal class name from the micropython driver, written in CamelCase
- Config name: The string used for the config file `_type` parameter, written in lowercase with hyphens separating words

Both names are used in a mapping dict which controls which class is instantiated at boot time (see `hardware_classes` in [Config.py](core/Config.py)).

Two names are required because multiple hardware types can share a single class. For example, the [Tplink](devices/Tplink.py) class is used for both smart dimmers and smart bulbs, which have different API call syntax. The `_type` parameter determines which syntax is used in this case. This approach allows much more code reuse than maintaining separate classes for each.

### Sensor Class

All sensor classes must subclass [Sensor.py](sensors/Sensor.py), which is itself a subclass of [Instance.py](core/Instance.py). These provide methods required to interface with the API, including `enable`, `disable`, `set_rule`, etc. These can be extended or overridden as needed.

All sensor classes **must** include a `condition_met` method, which determines when the sensor's targets are turned on and off. The `condition_met` method should return:
- `True` when targets should turn on
- `False` when targets should turn off
- `None` when no change is needed

Sensors may implement an optional `trigger` method which simulates the condition being met, causing target devices to turn on. This can only be called with the `trigger_sensor` API endpoint. If omitted the endpoint is disabled, which may be desirable in some cases - for example, triggering a Thermostat sensor would require arbitrarily changing the rule, which creates a confusing user experience (and already has its own endpoint). See [MotionSensor.py](sensors/MotionSensor.py) for an example trigger method.

By default all sensors support the rules `Enabled` and `Disabled`. If more rules are required the sensor must include a `validator` method. This method accepts a rule as argument, returns `False` if it is invalid, and returns the rule if it is valid. Returning a modified rule is encouraged in some situations - for example, a class which expects an integer rule should return `int(rule)` to avoid incorrectly accepting string representations of integers.

### Sensor Metadata

The JSON metadata must follow this syntax:
```
{
    "config_name": "",
    "class_name": "",
    "display_name": "",
    "description": "",
    "dependencies": [
        "sensors/Sensor.py",
        "core/Instance.py"
    ],
    "config_template": {
        "_type": "",
        "nickname": "placeholder",
        "default_rule": "placeholder",
        "schedule": {},
        "targets": []
    },
    "rule_prompt": "",
    "rule_limits": [],
    "triggerable": bool
}
```

Parameters:
- `config_name`: The config file `_type` parameter, lowercase with hyphens between words.
- `class_name`: The name of the sensor class in your micropython file, CamelCase.
- `display_name`: The name displayed on type select dropdown options in the web frontend.
- `dependencies`: A list of relative paths to all dependencies. This should include your sensor class, the `Sensor.py` and `core/Instance.py` base classes. If your sensor requires a driver from `lib/` then it must also be included (see [Thermostat.json](sensors/metadata/Thermostat.json) for an example).
- `config_template`: A full template of the hardware-level config file for the sensor type.
    - All parameters in the example above are required, but more can be added (for example, an `ip` parameter for network sensors).
    - The `placeholder` keyword indicates that the [config generator script](CLI/config_generator.py) should prompt the user for input.
    - The `_type` parameter must be pre-filled with the same value as `config_name`.
    - The `schedule` and `targets` parameters must be empty
- `rule_prompt`: Determines which rule prompt is shown by the config generator script (in the future this will also determine configuration options in the web frontend). Available options:
    - `standard`: User may select "Enabled" or "Disabled"
    - `float_range`: User may select a float, "Enabled", or "Disabled"
    - `int_range`: User may select an integer, "Enabled", or "Disabled"
    - `int_or_fade`: User may select an integer, fade rule, "Enabled", or "Disabled"
    - `on_off`: User may select "On", "Off", "Enabled", or "Disabled"
- `rule_limits`: Required for sensors which accept int/float rules, ignored for all others. Should contain 2 integers representing the minimum and maximum supported rules.
- `triggerable`: Bool, determines whether the `trigger_sensor` API endpoint is supported. If False the frontend trigger button will be disabled.

### Integrating with client-side tools

The following changes must be made when a new sensor class is added:
- [ ] [`Config.hardware_classes`](core/Config.py): Add the `_type` parameter as key and the class name as value
- [ ] [`firmware/manifest.py`](firmware/manifest.py): Add a module statement pointing to the new sensor class
- [ ] [`util/instance_validators.py`](util/instance_validators.py): Add a validator function for the new class, typically you can copy the validator method and return True instead of the rule user-selectable parameters

Once the above changes have been made, run the unit tests and fix anything that fails. At a minimum the module will need to be added to [`test_provision.py](tests/cli/test_provision.py) in the `test_provision_unit_tests` test case.
