import os
from Webrepl import Webrepl
from api_endpoints import reboot
from helper_functions import is_device, is_sensor, get_device_and_sensor_metadata


# Returns dict containing dependency lists for all device and sensor types
# Devices are in "devices" subsection, keyed by _type parmater
# Sensors are in "sensors" subsection, keyed by _type parmater
def build_dependencies_dict():
    dependencies = {
        'devices': {},
        'sensors': {}
    }

    # Get dict with contents of all device and sensor metadata files
    metadata = get_device_and_sensor_metadata()

    # Iterate device metadata, add each dependency list to dict
    for _type, value in metadata['devices'].items():
        dependencies['devices'][_type] = value['dependencies']

    # Iterate sensor metadata, add each dependency list to dict
    for _type, value in metadata['sensors'].items():
        dependencies['sensors'][_type] = value['dependencies']

    return dependencies


# Combine dependency relative paths from all device and sensor metadatas, used by get_modules
dependencies = build_dependencies_dict()

# Core module relative paths, required regardless of configuration
core_modules = [
    "core/Config.py",
    "core/Group.py",
    "core/SoftwareTimer.py",
    "core/Api.py",
    "core/util.py",
    "core/main.py"
]


# Takes full config file dict, path to repository root
# Returns dict of local:remote filesystem paths with all dependencies
# Dict iterated by provision to upload files
def get_modules(config, repo_root):
    modules = []

    # Get lists of device and sensor types
    device_types = [config[device]['_type'] for device in config.keys() if is_device(device)]
    sensor_types = [config[sensor]['_type'] for sensor in config.keys() if is_sensor(sensor)]

    # Add dependencies for each device and sensor type to modules list
    for dtype in device_types:
        modules.extend(dependencies['devices'][dtype])
    for stype in sensor_types:
        modules.extend(dependencies['sensors'][stype])

    # Add IrBlaster if configured
    if 'ir_blaster' in config.keys():
        modules.append("devices/IrBlaster.py")

    # Add core modules, remove duplicates without changing order
    modules.extend(core_modules)
    modules = list(dict.fromkeys(modules))

    # Convert to dict containing pairs of local:remote filesystem paths
    # Local path is uploaded to remote path on target ESP32
    modules = {os.path.join(repo_root, i): i.split("/")[1] for i in modules}

    return modules


# Takes target ip, password, config file dict, and modules dict
# Upload config file + all modules in dict to target IP
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

        # Upload all device/sensor + core modules
        [node.put_file(local, remote) for local, remote in modules.items()]
        node.close_connection()

        # Reboot node via API call
        reboot(ip, [])

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
