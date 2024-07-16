import json
from math import isnan
from functools import wraps
from helper_functions import (
    is_device_or_sensor,
    is_sensor,
    is_device,
    fahrenheit_to_celsius,
    kelvin_to_celsius
)


# Map device and sensor types to validators for both default
# and schedule rules. Each key contains a dict with 'default'
# and 'schedule' keys to access each function.
validator_map = {}


# Receives full config entry, tests default_rule and all schedule
# rules with validator functions looked up in validator_map.
# Returns True or error message
def validate_rules(instance):
    print(f"Validating {instance['nickname']} rules...")

    try:
        default_validator = validator_map[instance['_type']]['default']
        schedule_validator = validator_map[instance['_type']]['schedule']
    except KeyError:
        return f'Invalid type {instance["_type"]}'

    # Validate default rule
    valid = default_validator(instance['default_rule'], **instance)
    if valid is False:
        return f"{instance['nickname']}: Invalid default rule {instance['default_rule']}"
    # If validator returns own error, return as-is
    elif valid is not True:
        return valid

    # Validate shedule rules
    for time in instance['schedule']:
        if not time:
            return f"{instance['nickname']}: Missing schedule rule timestamp"

        valid = schedule_validator(instance['schedule'][time], **instance)

        if valid is False:
            return f"{instance['nickname']}: Invalid schedule rule {instance['schedule'][time]}"
        # If validator returns own error, return as-is
        elif valid is not True:
            return valid

    return True


# Adds decorated function to validator_map default key
# for all types specified in type_list
def add_default_rule_validator(type_list):
    def _add_schedule_rule_validator(func):
        for i in type_list:
            if i not in validator_map:
                validator_map[i] = {'default': '', 'schedule': ''}
            validator_map[i]['default'] = func
        return func
    return _add_schedule_rule_validator


# Adds decorated function to validator_map schedule key
# for all types specified in type_list
def add_schedule_rule_validator(type_list):
    def _add_schedule_rule_validator(func):
        for i in type_list:
            if i not in validator_map.keys():
                validator_map[i] = {'default': '', 'schedule': ''}
            validator_map[i]['schedule'] = func
        return func
    return _add_schedule_rule_validator


# Returns wrapped function that accepts enabled and
# disabled in addition to own rules
def add_generic_validator(func):
    @wraps(func)
    def wrapper(rule, **kwargs):
        if generic_validator(rule):
            return True
        else:
            return func(rule, **kwargs)
    return wrapper


@add_schedule_rule_validator(["tasmota-relay", "dumb-relay", "desktop", "mosfet", "switch", "http-get"])
@add_default_rule_validator(["tasmota-relay", "dumb-relay", "desktop", "mosfet", "switch", "http-get"])
def generic_validator(rule, **kwargs):
    if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
        return True
    else:
        return False


# Takes dict containing 2 entries named "on" and "off"
# Both entries are lists containing a full API request
# "on" sent when self.send(1) called, "off" when self.send(0) called
@add_schedule_rule_validator(['api-target'])
@add_generic_validator
@add_default_rule_validator(['api-target'])
def api_target_validator(rule, **kwargs):
    if isinstance(rule, str):
        try:
            # Convert string rule to dict (if received from API)
            rule = json.loads(rule)
        except (TypeError, ValueError):
            return False

    if not isinstance(rule, dict):
        return False

    # Reject if more than 2 sub-rules
    if not len(rule) == 2:
        return False

    # Iterate over each sub-rule
    for i in rule:
        # Index must be "on" or "off"
        if i not in ["on", "off"]:
            return False

        # Check against all valid sub-rule patterns
        if not is_valid_api_sub_rule(rule[i]):
            return False

    else:
        # Iteration finished without a return False, rule is valid
        return True


# Takes ApiTarget sub-rule, return True if valid False if invalid
def is_valid_api_sub_rule(rule):
    if not isinstance(rule, list):
        return False

    # Endpoints that require no args
    # "ignore" is not a valid command, it allows only using on/off and ignoring the other
    if rule[0] in ['reboot', 'clear_log', 'ignore'] and len(rule) == 1:
        return True

    # Endpoints that require a device or sensor arg
    elif rule[0] in ['enable', 'disable', 'reset_rule'] and len(rule) == 2 and is_device_or_sensor(rule[1]):
        return True

    # Endpoints that require a sensor arg
    elif rule[0] in ['condition_met', 'trigger_sensor'] and len(rule) == 2 and is_sensor(rule[1]):
        return True

    # Endpoints that require a device arg
    elif rule[0] in ['turn_on', 'turn_off'] and len(rule) == 2 and is_device(rule[1]):
        return True

    # Endpoints that require a device/sensor arg and int/float arg
    elif rule[0] in ['enable_in', 'disable_in'] and len(rule) == 3 and is_device_or_sensor(rule[1]):
        try:
            float(rule[2])
            return True
        except ValueError:
            return False

    # Endpoint requires a device/sensor arg and rule arg
    # Rule arg not validated (device/sensor type not known), client returns error if invalid
    elif rule[0] == 'set_rule' and len(rule) == 3 and is_device_or_sensor(rule[1]):
        return True

    # Endpoint requires IR target and IR key args
    # Target and keys not validated (configured codes not known), client returns error if invalid
    elif rule[0] == 'ir_key':
        if len(rule) == 3 and type(rule[1]) == str and type(rule[2]) == str:
            return True
        else:
            return False

    else:
        # Did not match any valid patterns
        return False


# Takes configured min_rule and max_rule, absolute limits for device
# Returns True if valid, error if invalid
def min_max_rule_validator(min_rule, max_rule, device_min, device_max):
    try:
        if int(min_rule) > int(max_rule):
            return 'min_rule cannot be greater than max_rule'
        elif int(min_rule) < device_min or int(max_rule) < device_min:
            return f'Rule limits cannot be less than {device_min}'
        elif int(min_rule) > device_max or int(max_rule) > device_max:
            return f'Rule limits cannot be greater than {device_max}'
        else:
            return True
    except ValueError:
        return f'Invalid rule limits, both must be int between {device_min} and {device_max}'


# Requires int between min/max, or fade/<int>/<int>
@add_schedule_rule_validator(['pwm'])
@add_generic_validator
@add_default_rule_validator(['pwm'])
def led_strip_validator(rule, **kwargs):
    try:
        min_rule = kwargs['min_rule']
        max_rule = kwargs['max_rule']
        valid = min_max_rule_validator(min_rule, max_rule, 0, 1023)
        if valid is not True:
            return valid
    except KeyError:
        return 'LedStrip missing required min_rule and/or max_rule property'

    # Validate rule
    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0 or int(target) < 0:
                return False

            if int(min_rule) <= int(target) <= int(max_rule):
                return True
            else:
                return False

        elif isinstance(rule, bool):
            return False

        elif int(min_rule) <= int(rule) <= int(max_rule):
            return True

        else:
            return False

    except (ValueError, TypeError):
        return False


# Requires int between 1 and 100 (inclusive), or fade/<int>/<int>
@add_schedule_rule_validator(['dimmer', 'bulb'])
@add_generic_validator
@add_default_rule_validator(['dimmer', 'bulb'])
def tplink_validator(rule, **kwargs):
    try:
        # Validate rule limits
        min_rule = kwargs['min_rule']
        max_rule = kwargs['max_rule']
        valid = min_max_rule_validator(min_rule, max_rule, 1, 100)
        if valid is not True:
            return valid
    except KeyError:
        return 'Tplink missing required min_rule and/or max_rule property'

    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0:
                return False

            elif int(min_rule) <= int(target) <= int(max_rule):
                return True
            else:
                return False

        # Reject "False" before reaching conditional below (would cast False to 0 and accept as valid rule)
        elif isinstance(rule, bool):
            return False

        elif int(min_rule) <= int(rule) <= int(max_rule):
            return True

        else:
            return False

    except (ValueError, TypeError):
        return False


# Requires int between 1 and 255 (inclusive), or fade/<int>/<int>
@add_schedule_rule_validator(['wled'])
@add_generic_validator
@add_default_rule_validator(['wled'])
def wled_validator(rule, **kwargs):
    try:
        # Validate rule limits
        min_rule = kwargs['min_rule']
        max_rule = kwargs['max_rule']
        valid = min_max_rule_validator(min_rule, max_rule, 1, 255)
        if valid is not True:
            return valid
    except KeyError:
        return 'Wled missing required min_rule and/or max_rule property'

    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0:
                return False

            elif int(min_rule) <= int(target) <= int(max_rule):
                return True
            else:
                return False

        # Reject "False" before reaching conditional below (would cast False to 0 and accept as valid rule)
        if isinstance(rule, bool):
            return False

        elif int(min_rule) <= int(rule) <= int(max_rule):
            return True

        else:
            return False

    except (ValueError, TypeError):
        return False


# Requires on or off (in addition to enabled/disabled checked previously)
# Needs on and off because rule is only factor determining if condition is met,
# without it would never turn targets off (condition not checked while disabled)
@add_schedule_rule_validator(['dummy'])
@add_generic_validator
@add_default_rule_validator(['dummy'])
def dummy_validator(rule, **kwargs):
    try:
        if rule.lower() == "on" or rule.lower() == "off":
            return True
        else:
            return False
    except AttributeError:
        return False


# Requires int or float
@add_schedule_rule_validator(['load-cell'])
@add_generic_validator
@add_default_rule_validator(['load-cell'])
def load_cell_validator(rule, **kwargs):
    try:
        # Prevent accepting NaN (is valid float but breaks comparison)
        if isnan(float(rule)):
            return False
        else:
            return True
    except (ValueError, TypeError):
        return False


# Requires int, float, or None
@add_schedule_rule_validator(['pir'])
@add_generic_validator
@add_default_rule_validator(['pir'])
def motion_sensor_validator(rule, **kwargs):
    try:
        if rule is None:
            return True
        # Prevent incorrectly accepting True and False (last condition casts to 1.0, 0.0 respectively)
        elif isinstance(rule, bool):
            return False
        # Prevent accepting NaN (is valid float but breaks arithmetic)
        elif isnan(float(rule)):
            return False
        else:
            # Confirm can cast to float
            if float(rule):
                return True
    except (ValueError, TypeError):
        return False


# Requires int or float rule between 18 and 27 celsius (inclusive)
# If units param is not celsius rule will be converted to correct units
# Also validates tolerance, (int/float between 0.1 and 10), mode, and units
@add_schedule_rule_validator(['si7021', 'dht22'])
@add_generic_validator
@add_default_rule_validator(['si7021', 'dht22'])
def thermostat_validator(rule, **kwargs):
    # Validate tolerance
    try:
        if not 0.1 <= float(kwargs['tolerance']) <= 10.0:
            return 'Thermostat tolerance out of range (0.1 - 10.0)'
    except ValueError:
        return 'Thermostat tolerance must be int or float'
    except KeyError:
        return 'Thermostat missing required tolerance property'

    # Validate mode
    if kwargs['mode'] not in ['heat', 'cool']:
        return 'Thermostat mode must be either "heat" or "cool"'

    # Validate units
    units = kwargs['units']
    if units not in ['fahrenheit', 'celsius', 'kelvin']:
        return 'Thermostat units must be "fahrenheit", "celsius", or "kelvin"'

    # Validate rule
    try:
        # Convert rule to celsius if using other units
        if units == 'fahrenheit':
            rule = fahrenheit_to_celsius(float(rule))
        elif units == 'kelvin':
            rule = kelvin_to_celsius(float(rule))

        # Constrain to range 18-27 (celsius)
        if 18 <= float(rule) <= 27:
            return True
        else:
            return False
    except (ValueError, TypeError):
        return False
