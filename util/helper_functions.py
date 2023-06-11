import re


# Returns True if arg starts with "device" or "sensor", otherwise False
def is_device_or_sensor(string):
    return (string.startswith("device") or string.startswith("sensor"))


# Returns True if arg starts with "device", otherwise False
def is_device(string):
    return string.startswith("device")


# Returns True if arg starts with "sensor", otherwise False
def is_sensor(string):
    return string.startswith("sensor")


# Takes config file, param
def get_config_param_list(config, param):
    return [value[param] for key, value in config.items() if param in value]


# Returns True if arg matches IPv4 regex, otherwise False
def valid_ip(ip):
    return bool(re.match(r'^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$', ip))


# Returns True if arg matches HH:MM timestamp regex, otherwise False
def valid_timestamp(timestamp):
    return bool(re.match(r'^([0-1][0-9]|2[0-3]):[0-5][0-9]$', timestamp))
