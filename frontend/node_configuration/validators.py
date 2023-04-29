import json


# Receives full config entry from validateConfig view
# Determines correct validator and passes to validate_all
def validate_rules(instance):
    print(f"Validating {instance['nickname']} rules...")
    instance_type = instance['type']
    if instance_type == "dimmer" or instance_type == "bulb":
        return validate_all(instance, tplink_validator)
    elif instance_type == "pwm":
        return validate_all(instance, led_strip_validator, instance['min'], instance['max'])
    elif instance_type == "api-target":
        return validate_all(instance, api_target_validator)
    elif instance_type == "wled":
        return validate_all(instance, wled_validator)
    elif instance_type == "pir":
        return validate_all(instance, motion_sensor_validator)
    elif instance_type == "si7021":
        return validate_all(instance, thermostat_validator)
    elif instance_type == "dummy":
        return validate_all(instance, dummy_validator)
    elif instance_type in ["relay", "dumb-relay", "desktop", "mosfet", "switch"]:
        return validate_all(instance)
    else:
        return f"Invalid type {instance['type']}"


# Receives full config entry + type-specific validator
# Checks default_rule and all schedule rules
def validate_all(instance, special_validator=False, *args):
    # Check default rule
    valid = universal_validator(instance['default_rule'], special_validator, *args)
    if valid is not True:
        return f"{instance['nickname']}: Invalid default rule {instance['default_rule']}"

    # Check schedule rules
    for time in instance['schedule']:
        valid = universal_validator(instance['schedule'][time], special_validator, *args)
        if valid is not True:
            return f"{instance['nickname']}: Invalid schedule rule {instance['schedule'][time]}"

    return True


# Accepts single rule, optional type-specific validator
# Checks against universal rules first, then type validator if present
def universal_validator(rule, special_validator=False, *args):
    if str(rule).lower() == "enabled" or str(rule).lower() == "disabled":
        return True
    else:
        if special_validator:
            return special_validator(rule, *args)
        else:
            return False


# Takes dict containing 2 entries named "on" and "off"
# Both entries are lists containing a full API request
# "on" sent when self.send(1) called, "off" when self.send(0) called
def api_target_validator(rule):
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

    for i in rule:
        # Index must be "on" or "off"
        if not i == "on" and not i == "off":
            return False

        if not isinstance(rule[i], list):
            return False

        # "ignore" is not a valid command, it allows only using on/off and ignoring the other
        if rule[i][0] in ['reboot', 'clear_log', 'ignore'] and len(rule[i]) == 1:
            continue

        elif rule[i][0] in ['enable', 'disable'] and len(rule[i]) == 2 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
            continue

        elif rule[i][0] in ['condition_met', 'trigger_sensor'] and len(rule[i]) == 2 and rule[i][1].startswith("sensor"):
            continue

        elif rule[i][0] in ['enable_in', 'disable_in'] and len(rule[i]) == 3 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
            try:
                float(rule[i][2])
                continue
            except ValueError:
                return False

        elif rule[i][0] == 'set_rule' and len(rule[i]) == 3 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
            continue

        elif rule[i][0] == 'ir_key':
            if len(rule[i]) == 3 and type(rule[i][1]) == str and type(rule[i][2]) == str:
                continue
            elif len(rule[i]) == 1 and rule[i][0] == 'ignore':
                continue
            else:
                return False

        else:
            # Did not match any valid patterns
            return False

    else:
        # Iteration finished without a return False, rule is valid
        return True


# Requires int between min/max, or fade/<int>/<int>
def led_strip_validator(rule, min_bright, max_bright):
    try:
        if str(rule).startswith("fade"):
            # Parse parameters from rule
            cmd, target, period = rule.split("/")

            if int(period) < 0:
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
def tplink_validator(rule):
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
def wled_validator(rule):
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
def dummy_validator(rule):
    try:
        if rule.lower() == "on" or rule.lower() == "off":
            return True
        else:
            return False
    except AttributeError:
        return False


# Requires int or float
def motion_sensor_validator(rule):
    try:
        if rule is None:
            return 0
        # Prevent incorrectly accepting True and False (next condition casts to 1.0, 0.0 respectively)
        elif isinstance(rule, bool):
            return False
        else:
            # Confirm can cast to float
            if float(rule):
                return True
    except (ValueError, TypeError):
        return False


# Requires int or float between 65 and 90 (inclusive)
def thermostat_validator(rule):
    try:
        # Constrain to range 65-80
        if 65 <= float(rule) <= 80:
            return True
        else:
            return False
    except (ValueError, TypeError):
        return False
