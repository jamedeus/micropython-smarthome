# Writing new sensor classes

All new sensor classes must subclass [Sensor.py](sensors/Sensor.py), which is itself a subclass of [Instance.py](core/Instance.py). These provide methods required to interface with the API, including `enable`, `disable`, `set_rule`, etc. These can be extended or overridden as needed.

All sensor classes **must** include a `condition_met` method, which determines when the sensor's targets are turned on and off. The `condition_met` method should return:
- `True` when targets should turn on
- `False` when targets should turn off
- `None` when no change is needed

By default all sensors support the rules `Enabled` and `Disabled`. If more rules are required the sensor must include a `validator` method. This method accepts a rule as argument, returns `False` if it is invalid, and returns the rule if it is valid. Returning a modified rule is encouraged in some situations - for example, a class which expects an integer rule should return `int(rule)` to avoid incorrectly accepting string representations of integers.

## Configuration

Config file syntax for the new sensor must be specified in the `config_templates` dict in [`util/validation_constants.py`](util/validation_constants.py). The sensor class name (CamelCase) must be used as the key. The `_type` parameter should contain the same name in lowercase with hyphens separating words. This parameter is read at boot to determine which class will be instantiated.

## Integrating new sensor classes

The following changes must be made when a new sensor class is added:
- [ ] [`CLI/config_generator.py`](CLI/config_generator.py): Add the sensor's `_type` parameter to the correct conditional in `default_rule_prompt_router` and `schedule_rule_prompt_router`
- [ ] [`Config.hardware_classes`](core/Config.py): Add the `_type` parameter as key and the class name as value
- [ ] [`firmware/manifest.py`](firmware/manifest.py): Add a module statement pointing to the new sensor class
- [ ] [`util/instance_validators.py`](util/instance_validators.py): Add a validator function for the new class, typically you can copy the validator method and return True instead of the rule
- [ ] [`util/provision_tools.py`](util/provision_tools.py): Add the `_type` parameter as key in the dependencies dict with a list of dependency modules as value
- [ ] [`util/validation_constants.py`](util/validation_constants.py): Add the class name as key in the config_templates dict and a full config template as value, using `placeholder` for all user-selectable parameters

Once the above changes have been made, run the unit tests and fix anything that fails. At a minimum the module will need to be added to [`test_provision.py](tests/cli/test_provision.py) in the `test_provision_unit_tests` test case.
