def is_device(string):
    try:
        return string.startswith("device")
    except AttributeError:
        return False


def is_sensor(string):
    try:
        return string.startswith("sensor")
    except AttributeError:
        return False


def is_device_or_sensor(string):
    try:
        return (string.startswith("device") or string.startswith("sensor"))
    except AttributeError:
        return False
