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
