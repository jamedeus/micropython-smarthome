import json
from functools import wraps
from helper_functions import is_device_or_sensor, is_sensor


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


@add_schedule_rule_validator(["relay", "dumb-relay", "desktop", "mosfet", "switch"])
@add_default_rule_validator(["relay", "dumb-relay", "desktop", "mosfet", "switch"])
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

    # "ignore" is not a valid command, it allows only using on/off and ignoring the other
    if rule[0] in ['reboot', 'clear_log', 'ignore'] and len(rule) == 1:
        return True

    elif rule[0] in ['enable', 'disable', 'reset_rule'] and len(rule) == 2 and is_device_or_sensor(rule[1]):
        return True

    elif rule[0] in ['condition_met', 'trigger_sensor'] and len(rule) == 2 and is_sensor(rule[1]):
        return True

    elif rule[0] in ['turn_on', 'turn_off'] and len(rule) == 2 and rule[1].startswith("device"):
        return True

    elif rule[0] in ['enable_in', 'disable_in'] and len(rule) == 3 and is_device_or_sensor(rule[1]):
        try:
            float(rule[2])
            return True
        except ValueError:
            return False

    elif rule[0] == 'set_rule' and len(rule) == 3 and is_device_or_sensor(rule[1]):
        return True

    elif rule[0] == 'ir_key':
        if len(rule) == 3 and type(rule[1]) == str and type(rule[2]) == str:
            return True
        else:
            return False

    else:
        # Did not match any valid patterns
        return False


# Requires int between min/max, or fade/<int>/<int>
@add_schedule_rule_validator(['pwm'])
@add_generic_validator
@add_default_rule_validator(['pwm'])
def led_strip_validator(rule, **kwargs):
    # TODO KeyError (missing min/max args)
    min_bright = kwargs['min_bright']
    max_bright = kwargs['max_bright']

    # Validate min/max brightness limits
    try:
        if int(min_bright) > int(max_bright):
            return 'PWM min cannot be greater than max'
        elif int(min_bright) < 0 or int(max_bright) < 0:
            return 'PWM limits cannot be less than 0'
        elif int(min_bright) > 1023 or int(max_bright) > 1023:
            return 'PWM limits cannot be greater than 1023'
    except ValueError:
        return 'Invalid PWM limits, both must be int between 0 and 1023'

    # Validate rule
    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0 or int(target) < 0:
                return False

            if int(min_bright) <= int(target) <= int(max_bright):
                return True
            else:
                return False

        elif isinstance(rule, bool):
            return False

        elif int(min_bright) <= int(rule) <= int(max_bright):
            return True

        else:
            return False

    except (ValueError, TypeError):
        return False


# Requires int between 1 and 100 (inclusive), or fade/<int>/<int>
# TODO max/min args
@add_schedule_rule_validator(['dimmer', 'bulb'])
@add_generic_validator
@add_default_rule_validator(['dimmer', 'bulb'])
def tplink_validator(rule, **kwargs):
    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0:
                return False

            if 0 <= int(target) <= 100:
                return True
            else:
                return False

        # Reject "False" before reaching conditional below (would cast False to 0 and accept as valid rule)
        elif isinstance(rule, bool):
            return False

        elif 0 <= int(rule) <= 100:
            return True

        else:
            return False

    except (ValueError, TypeError):
        return False


# Requires int between 1 and 255 (inclusive)
# TODO max/min args
@add_schedule_rule_validator(['wled'])
@add_generic_validator
@add_default_rule_validator(['wled'])
def wled_validator(rule, **kwargs):
    try:
        # Reject "False" before reaching conditional below (would cast False to 0 and accept as valid rule)
        if isinstance(rule, bool):
            return False

        elif 1 <= int(rule) <= 255:
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
@add_schedule_rule_validator(['pir'])
@add_generic_validator
@add_default_rule_validator(['pir'])
def motion_sensor_validator(rule, **kwargs):
    try:
        if rule is None:
            return True
        # Prevent incorrectly accepting True and False (next condition casts to 1.0, 0.0 respectively)
        elif isinstance(rule, bool):
            return False
        else:
            # Confirm can cast to float
            if float(rule):
                return True
    except (ValueError, TypeError):
        return False


# Requires int or float between 65 and 80 (inclusive)
# Also validates tolerance, must be int or float between 0.1 and 10
@add_schedule_rule_validator(['si7021'])
@add_generic_validator
@add_default_rule_validator(['si7021'])
def thermostat_validator(rule, **kwargs):
    # Validate tolerance
    # TODO KeyError (missing tolerance)
    try:
        if not 0.1 <= float(kwargs['tolerance']) <= 10.0:
            return 'Thermostat tolerance out of range (0.1 - 10.0)'
    except ValueError:
        return 'Thermostat tolerance must be int or float'

    # Validate rule
    try:
        # Constrain to range 65-80
        if 65 <= float(rule) <= 80:
            return True
        else:
            return False
    except (ValueError, TypeError):
        return False
