'''Contains functions used to validate instance (device and sensor) sections in
ESP32 config files.
'''

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


def validate_rules(instance):
    '''Receives full config entry, validates default_rule and all schedule
    rules by passing them to validator functions in validator_map dict.
    Returns True if all rules are valid, error string if any are invalid.
    '''
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
    if valid is not True:
        return valid

    # Validate shedule rules
    for time in instance['schedule']:
        if not time:
            return f"{instance['nickname']}: Missing schedule rule timestamp"

        valid = schedule_validator(instance['schedule'][time], **instance)

        if valid is False:
            return f"{instance['nickname']}: Invalid schedule rule {instance['schedule'][time]}"
        # If validator returns own error, return as-is
        if valid is not True:
            return valid

    return True


def add_default_rule_validator(type_list):
    '''Adds decorated function to validator_map default key for all types
    specified in type_list arg (list of config_name values from metadata).
    '''
    def _add_schedule_rule_validator(func):
        for i in type_list:
            if i not in validator_map:  # pragma: no branch
                validator_map[i] = {'default': '', 'schedule': ''}
            validator_map[i]['default'] = func
        return func
    return _add_schedule_rule_validator


def add_schedule_rule_validator(type_list):
    '''Adds decorated function to validator_map schedule key for all types
    specified in type_list arg (list of config_name values from metadata).
    '''
    def _add_schedule_rule_validator(func):
        for i in type_list:
            if i not in validator_map:  # pragma: no cover
                validator_map[i] = {'default': '', 'schedule': ''}
            validator_map[i]['schedule'] = func
        return func
    return _add_schedule_rule_validator


def add_generic_validator(func):
    '''Returns wrapped function that accepts "enabled" and "disabled" in
    addition to rules accepted by the decorated function.
    '''
    @wraps(func)
    def wrapper(rule, **kwargs):
        if generic_validator(rule):
            return True
        return func(rule, **kwargs)
    return wrapper


@add_schedule_rule_validator([
    "tasmota-relay",
    "dumb-relay",
    "desktop",
    "mosfet",
    "switch",
    "http-get"
])
@add_default_rule_validator([
    "tasmota-relay",
    "dumb-relay",
    "desktop",
    "mosfet",
    "switch",
    "http-get"
])
def generic_validator(rule, **kwargs):
    '''Accepts "enabled" and "disabled" rules'''

    if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
        return True
    return False


@add_schedule_rule_validator(['api-target'])
@add_generic_validator
@add_default_rule_validator(['api-target'])
def api_target_validator(rule, **kwargs):
    '''Takes complete api-target rule dict with "on" and "off" keys, each
    containing a list with parameters for a single API call. Returns True if
    syntax correct and both API calls are valid.
    '''
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

    # Iteration finished without a return False, rule is valid
    return True


def is_valid_api_sub_rule(rule):
    '''Takes api-target sub-rule (list of parameters for a single API call).
    Returns True if API call is valid, False if syntax is incorrect.
    '''
    if not isinstance(rule, list):
        return False

    # Endpoints that require no args
    # "ignore" is not a valid command, it allows only using on/off and ignoring the other
    if rule[0] in ['reboot', 'clear_log', 'ignore'] and len(rule) == 1:
        return True

    # Endpoints that require a device or sensor arg
    if rule[0] in ['enable', 'disable', 'reset_rule'] and len(rule) == 2 and is_device_or_sensor(rule[1]):
        return True

    # Endpoints that require a sensor arg
    if rule[0] in ['condition_met', 'trigger_sensor'] and len(rule) == 2 and is_sensor(rule[1]):
        return True

    # Endpoints that require a device arg
    if rule[0] in ['turn_on', 'turn_off'] and len(rule) == 2 and is_device(rule[1]):
        return True

    # Endpoints that require a device/sensor arg and int/float arg
    if rule[0] in ['enable_in', 'disable_in'] and len(rule) == 3 and is_device_or_sensor(rule[1]):
        try:
            float(rule[2])
            return True
        except ValueError:
            return False

    # Endpoint requires a device/sensor arg and rule arg
    # Rule arg not validated (device/sensor type not known), client returns error if invalid
    if rule[0] == 'set_rule' and len(rule) == 3 and is_device_or_sensor(rule[1]):
        return True

    # Endpoint requires IR target and IR key args
    # Target and keys not validated (configured codes not known), client returns error if invalid
    if rule[0] == 'ir_key':
        return len(rule) == 3 and isinstance(rule[1], str) and isinstance(rule[2], str)

    # Did not match any valid patterns
    return False


def min_max_rule_validator(min_rule, max_rule, device_min, device_max):
    '''Takes min_rule and max_rule from config file, absolute limits for
    device type (from metadata). Retuns True if min_rule and max_rule are
    valid, returns error string if invalid.
    '''
    try:
        if int(min_rule) > int(max_rule):
            return 'min_rule cannot be greater than max_rule'
        if int(min_rule) < device_min or int(max_rule) < device_min:
            return f'Rule limits cannot be less than {device_min}'
        if int(min_rule) > device_max or int(max_rule) > device_max:
            return f'Rule limits cannot be greater than {device_max}'
        return True
    except ValueError:
        return f'Invalid rule limits, both must be int between {device_min} and {device_max}'


@add_schedule_rule_validator(['pwm'])
@add_generic_validator
@add_default_rule_validator(['pwm'])
def led_strip_validator(rule, **kwargs):
    '''Takes rule value, min_rule kwarg, max_rule kwarg.

    Returns True if rule is int between min_rule and max_rule, or if rule has
    "fade/<int>/<int>" syntax where first int is between min_rule and max_rule.

    Returns False if rule is invalid or min_rule/max_rule are invalid.
    '''
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
            _, target, period = rule.split("/")

            # Reject fade rule if duration is negative
            if int(period) < 0:
                return False

            # Accept fade rule if target within min_rule - max_rule range
            if int(min_rule) <= int(target) <= int(max_rule):
                return True

            # Reject fade rule if target outside min_rule - max_rule range
            return False

        # Reject "False" before reaching conditional below
        # (would cast False to 0 and accept as valid rule)
        if isinstance(rule, bool):
            return False

        # Accept rule if within min_rule - max_rule range (inclusive)
        if int(min_rule) <= int(rule) <= int(max_rule):
            return True

        # Reject rule if outside min_rule - max_rule range
        return False
    except (ValueError, TypeError):
        return False


@add_schedule_rule_validator(['dimmer', 'bulb'])
@add_generic_validator
@add_default_rule_validator(['dimmer', 'bulb'])
def tplink_validator(rule, **kwargs):
    '''Takes rule value, min_rule kwarg, max_rule kwarg.

    Returns True if rule is int between min_rule and max_rule, or if rule has
    "fade/<int>/<int>" syntax where first int is between min_rule and max_rule.

    Returns False if rule is invalid or min_rule/max_rule are invalid.
    '''
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
            _, target, period = rule.split("/")

            # Reject fade rule if duration is negative
            if int(period) < 0:
                return False

            # Accept fade rule if target within min_rule - max_rule range
            if int(min_rule) <= int(target) <= int(max_rule):
                return True

            # Reject fade rule if target outside min_rule - max_rule range
            return False

        # Reject "False" before reaching conditional below
        # (would cast False to 0 and accept as valid rule)
        if isinstance(rule, bool):
            return False

        # Accept rule if within min_rule - max_rule range (inclusive)
        if int(min_rule) <= int(rule) <= int(max_rule):
            return True

        # Reject rule if outside min_rule - max_rule range
        return False
    except (ValueError, TypeError):
        return False


@add_schedule_rule_validator(['wled'])
@add_generic_validator
@add_default_rule_validator(['wled'])
def wled_validator(rule, **kwargs):
    '''Takes rule value, min_rule kwarg, max_rule kwarg.

    Returns True if rule is int between min_rule and max_rule, or if rule has
    "fade/<int>/<int>" syntax where first int is between min_rule and max_rule.

    Returns False if rule is invalid or min_rule/max_rule are invalid.
    '''
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
            _, target, period = rule.split("/")

            # Reject fade rule if duration is negative
            if int(period) < 0:
                return False

            # Accept fade rule if target within min_rule - max_rule range
            if int(min_rule) <= int(target) <= int(max_rule):
                return True

            # Reject fade rule if target outside min_rule - max_rule range
            return False

        # Reject "False" before reaching conditional below
        # (would cast False to 0 and accept as valid rule)
        if isinstance(rule, bool):
            return False

        # Accept rule if within min_rule - max_rule range (inclusive)
        if int(min_rule) <= int(rule) <= int(max_rule):
            return True

        # Reject rule if outside min_rule - max_rule range
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
    '''Accepts "on" or "off" rules
    '''
    try:
        if rule.lower() == "on" or rule.lower() == "off":
            return True
        return False
    except AttributeError:
        return False


@add_schedule_rule_validator(['pir', 'ld2410', 'load-cell'])
@add_generic_validator
@add_default_rule_validator(['pir', 'ld2410', 'load-cell'])
def int_or_float_validator(rule, **kwargs):
    '''Accepts int or float, rejects all other types.'''
    try:
        # Prevent incorrectly accepting True and False (last condition casts
        # to 1.0 and 0.0 respectively)
        if isinstance(rule, bool):
            return False

        # Prevent accepting NaN (is valid float but breaks arithmetic)
        if isnan(float(rule)):
            return False

        # Confirm can cast to float
        float(rule)
        return True
    except (ValueError, TypeError):
        return False


@add_schedule_rule_validator(['si7021', 'dht22'])
@add_generic_validator
@add_default_rule_validator(['si7021', 'dht22'])
def thermostat_validator(rule, **kwargs):
    '''Takes rule and thermostat config params (units, mode, tolerance).

    Accepts int or float rule between 18 and 27 celsius (inclusive). If units
    param is not "celsius" rule is converted from configured units to celsius.

    Returns error string if units is not "fahrenheit", "celsius", or "kelvin".
    Returns error string if mode is not "heat" or "cool".
    Returns error string if tolerance is less than 0.1 or greater than 10.0.
    Returns error string if thermostat params missing or have incorrect type.
    '''

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

        # Return True if rule is between 18 and 27, otherwise False
        return 18 <= float(rule) <= 27
    except (ValueError, TypeError):
        return False
