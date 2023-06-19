import os
from Webrepl import Webrepl
from helper_functions import is_device, is_sensor

# Dependency relative paths for all device and sensor types, used by get_modules
dependencies = {
    'devices': {
        'dimmer': ["devices/Tplink.py", "devices/Device.py", "devices/DimmableLight.py"],
        'bulb': ["devices/Tplink.py", "devices/Device.py", "devices/DimmableLight.py"],
        'relay': ["devices/Relay.py", "devices/Device.py"],
        'dumb-relay': ["devices/DumbRelay.py", "devices/Device.py"],
        'desktop': ["devices/Desktop_target.py", "devices/Device.py"],
        'pwm': ["devices/LedStrip.py", "devices/Device.py", "devices/DimmableLight.py"],
        'mosfet': ["devices/Mosfet.py", "devices/Device.py"],
        'api-target': ["devices/ApiTarget.py", "devices/Device.py"],
        'wled': ["devices/Wled.py", "devices/Device.py", "devices/DimmableLight.py"]
    },
    'sensors': {
        'pir': ["sensors/MotionSensor.py", "sensors/Sensor.py"],
        'si7021': ["sensors/Thermostat.py", "sensors/Sensor.py"],
        'dummy': ["sensors/Dummy.py", "sensors/Sensor.py"],
        'switch': ["sensors/Switch.py", "sensors/Sensor.py"],
        'desktop': ["sensors/Desktop_trigger.py", "sensors/Sensor.py"],
    }
}

# Core modules, required regardless of configuration
core_modules = [
    "core/Config.py",
    "core/Group.py",
    "core/SoftwareTimer.py",
    "core/Api.py",
    "core/util.py",
    "core/main.py"
]


# Takes full config file, returns list of classes for each device and sensor type
def get_modules(config, repo_root):
    modules = []

    # Get lists of device and sensor types
    device_types = [config[device]['_type'] for device in config.keys() if is_device(device)]
    sensor_types = [config[sensor]['_type'] for sensor in config.keys() if is_sensor(sensor)]

    # Get dependencies for all device and sensor types
    for dtype in device_types:
        modules.extend(dependencies['devices'][dtype])
    for stype in sensor_types:
        modules.extend(dependencies['sensors'][stype])

    # Add core modules, remove duplicates without changing order
    modules.extend(core_modules)
    modules = list(dict.fromkeys(modules))

    # Convert to dict containing pairs of local:remote filesystem paths
    # Local path is uploaded to remote path on target ESP32
    modules = {os.path.join(repo_root, i): i.split("/")[1] for i in modules}

    return modules


# Takes target ip, password, config file dict, and modules dict
# Uploads config and modules to target IP
def provision(ip, password, config, modules):
    # Open conection, detect if node connected to network
    node = Webrepl(ip, password)
    if not node.open_connection():
        return {
            'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }

    try:
        # Upload config file
        node.put_file_mem(config, "config.json")

        # Upload all device/sensor + core modules modules
        # Node will automatically reboot after last module (main.py)
        [node.put_file(local, remote) for local, remote in modules.items()]
        node.close_connection()

    except TimeoutError:
        return {
            'message': 'Connection timed out - please press target node reset button, wait 30 seconds, and try again.',
            'status': 408
        }

    except AssertionError:
        return {
            'message': 'Failed due to filesystem error, please re-flash firmware.',
            'status': 409
        }

    return {
        'message': 'Upload complete.',
        'status': 200
    }
