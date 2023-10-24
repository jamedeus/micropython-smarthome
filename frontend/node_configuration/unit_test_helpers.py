import os
import json
import shutil
import struct
import tempfile
from django.conf import settings
from django.test import Client, TestCase
from .models import Config, Node
from validation_constants import config_templates
from helper_functions import get_cli_config, write_cli_config, load_unit_test_config


# Subclass Client, add default for content_type arg
class JSONClient(Client):
    def post(self, path, data=None, content_type='application/json', **extra):
        return super().post(path, data, content_type, **extra)


# Subclass TestCase, back up cli_config.json contents, replace with
# template, restore after tests. Prevents tests modifying production.
class TestCaseBackupRestore(TestCase):
    # Get path to cli_config.json
    cli_config_path = os.path.join(settings.REPO_DIR, 'CLI', 'cli_config.json')

    # Create temp directory to back up existing config files
    backup_path = os.path.join(tempfile.gettempdir(), 'smarthome_config_file_backups')
    if not os.path.exists(backup_path):
        os.mkdir(backup_path)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Back up cli_config.json to class attribute
        with open(cls.cli_config_path, 'r') as file:
            cls.original_cli_config_backup = json.load(file)

        # Delete from disk, replace with template
        os.remove(cls.cli_config_path)
        write_cli_config(get_cli_config())

        # Move existing config dir to tmp, create blank dir for tests
        cls.backup_dir = shutil.move(settings.CONFIG_DIR, cls.backup_path)
        os.mkdir(settings.CONFIG_DIR)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Write cli_config.json backup back to disk
        with open(cls.cli_config_path, 'w') as file:
            json.dump(cls.original_cli_config_backup, file)

        # Delete test config files, move originals back
        shutil.rmtree(settings.CONFIG_DIR)
        shutil.move(cls.backup_dir, settings.CONFIG_DIR)


# Get directory containing unit_test_helpers.py
file_dir = os.path.dirname(os.path.realpath(__file__))

# Binary contents of test config file, used as payload in simulated Webrepl connections
binary_unit_test_config = json.dumps(load_unit_test_config()).encode()

# Used to track current position in binary_unit_test_config (read function called multiple times)
# A mutable object must be used for scope reasons, can't use int (would reset each call)
simulated_read_position = [0]


# Replaces websocket.read method in mock
# Feeds bytes from binary_unit_test_config to Webrepl.get_file and Webrepl.get_file_mem
def simulate_read_file_over_webrepl(size):
    # Client verifying signature, return expected bytes (WB00)
    if size == 4:
        return b'WB\x00\x00'

    # Client requested remaining filesize
    if size == 2:
        # Return 00 if no data left
        if simulated_read_position[0] >= len(binary_unit_test_config):
            return b'\x00\x00'

        # Otherwise return length of unread data
        remaining_size = len(binary_unit_test_config) - simulated_read_position[0]
        return struct.pack("<H", remaining_size)

    # Slice requested size starting from first un-read byte, increment counter to index of last byte in slice
    data = binary_unit_test_config[simulated_read_position[0]:simulated_read_position[0] + size]
    simulated_read_position[0] += size
    return data


# Helper function to create test node from any config object
def create_config_and_node_from_json(config_json, ip='192.168.1.123'):
    friendly_name = config_json['metadata']['id']
    filename = f'{friendly_name.lower()}.json'

    with open(os.path.join(settings.CONFIG_DIR, filename), 'w') as file:
        json.dump(config_json, file)

    node = Node.objects.create(friendly_name=friendly_name, ip=ip, floor=config_json['metadata']['floor'])
    config = Config.objects.create(config=config_json, filename=filename, node=node)

    return config, node


# Helper function to create test nodes with known values
def create_test_nodes():
    create_config_and_node_from_json(test_config_1, '192.168.1.123')
    create_config_and_node_from_json(test_config_2, '192.168.1.124')
    create_config_and_node_from_json(test_config_3, '192.168.1.125')


# Deletes files written to disk by create_test_nodes
def clean_up_test_nodes():
    for i in range(1, 4):
        try:
            os.remove(os.path.join(settings.CONFIG_DIR, f'test{i}.json'))
        except FileNotFoundError:
            pass


# Replaces provision view to simulate partially successful reupload_all
def simulate_reupload_all_partial_success(ip, password, config, modules):
    if config == test_config_2:
        return {
            'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }
    else:
        return {
            'message': 'Upload complete.',
            'status': 200
        }


# Replaces provision view to simulate one node failing for each possible reason in reupload_all
def simulate_reupload_all_fail_for_different_reasons(ip, password, config, modules):
    if config == test_config_1:
        return {
            'message': 'Connection timed out - please press target node reset button, wait 30 seconds, and try again.',
            'status': 408
        }
    if config == test_config_2:
        return {
            'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }
    if config == test_config_3:
        return {
            'message': 'Failed due to filesystem error, please re-flash firmware.',
            'status': 409
        }


# Replaces Webrepl.put_file to simulate uploading to a node with no /lib directory
def simulate_first_time_upload(self, src_file, dst_file):
    if dst_file.startswith('lib'):
        raise AssertionError


# Replaces Webrepl.put_file to simulate uploading to a node with corrupt filesystem
def simulate_corrupt_filesystem_upload(self, src_file, dst_file):
    if not dst_file.startswith('lib'):
        raise AssertionError


# Simulated input from user creating config with frontend
# Used by GenerateConfigFileTests, DeleteConfigTests, DuplicateDetectionTests
request_payload = {
    "metadata": {
        "id": "Unit Test Config",
        "floor": "0",
        "location": "build pipeline",
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    "wifi": {
        "ssid": "mynetwork",
        "password": "hunter2"
    },
    "ir_blaster": {
        "pin": "23",
        "target": [
            "tv"
        ]
    },
    "device1": {
        "_type": "dimmer",
        "nickname": "Overhead",
        "ip": "192.168.1.105",
        "min_rule": "1",
        "max_rule": "100",
        "default_rule": "100",
        "schedule": {
            "08:00": "100",
            "22:00": "35"
        }
    },
    "device2": {
        "_type": "bulb",
        "nickname": "Lamp",
        "ip": "192.168.1.106",
        "min_rule": "1",
        "max_rule": "100",
        "default_rule": "75",
        "schedule": {
            "08:00": "100",
            "22:00": "35"
        }
    },
    "device3": {
        "_type": "tasmota-relay",
        "nickname": "Porch Light",
        "ip": "192.168.1.107",
        "default_rule": "enabled",
        "schedule": {
            "06:00": "disabled",
            "18:00": "enabled"
        }
    },
    "device4": {
        "_type": "dumb-relay",
        "nickname": "Fan",
        "default_rule": "disabled",
        "pin": "18",
        "schedule": {}
    },
    "device5": {
        "_type": "desktop",
        "nickname": "Screen",
        "ip": "192.168.1.150",
        "default_rule": "enabled",
        "schedule": {
            "08:00": "enabled",
            "22:00": "disabled"
        }
    },
    "device6": {
        "_type": "pwm",
        "nickname": "Cabinet Lights",
        "min_rule": "0",
        "max_rule": "1023",
        "default_rule": "721",
        "pin": "26",
        "schedule": {}
    },
    "device7": {
        "_type": "mosfet",
        "nickname": "Humidifier",
        "default_rule": "disabled",
        "pin": "19",
        "schedule": {}
    },
    "device8": {
        "_type": "wled",
        "nickname": "TV Bias Lights",
        "ip": "192.168.1.110",
        "min_rule": "1",
        "max_rule": "255",
        "default_rule": "128",
        "schedule": {
            "08:00": "100"
        }
    },
    "device9": {
        "_type": "api-target",
        "nickname": "Remote Control",
        "ip": "127.0.0.1",
        "default_rule": "{\"on\":[\"ir_key\",\"tv\",\"power\"],\"off\":[\"ir_key\",\"tv\",\"power\"]}",
        "schedule": {
            "22:00": "{\"on\":[\"ir_key\",\"tv\",\"power\"],\"off\":[\"ir_key\",\"tv\",\"power\"]}"
        }
    },
    "sensor1": {
        "_type": "pir",
        "nickname": "Motion",
        "default_rule": "5",
        "pin": "4",
        "schedule": {
            "08:00": "5",
            "22:00": "1"
        },
        "targets": [
            "device1",
            "device2",
            "device5",
            "device6"
        ]
    },
    "sensor2": {
        "_type": "switch",
        "nickname": "Switch",
        "default_rule": "enabled",
        "pin": "5",
        "schedule": {},
        "targets": [
            "device4",
            "device7"
        ]
    },
    "sensor3": {
        "_type": "dummy",
        "nickname": "Override",
        "default_rule": "on",
        "schedule": {
            "06:00": "on",
            "18:00": "off"
        },
        "targets": [
            "device3"
        ]
    },
    "sensor4": {
        "_type": "desktop",
        "nickname": "Activity",
        "default_rule": "enabled",
        "ip": "192.168.1.150",
        "schedule": {
            "08:00": "enabled",
            "22:00": "disabled"
        },
        "targets": [
            "device1",
            "device2",
            "device5",
            "device6"
        ]
    },
    "sensor5": {
        "_type": "si7021",
        "nickname": "Temperature",
        "default_rule": "71",
        "mode": "cool",
        "tolerance": "3",
        "schedule": {
            "08:00": "73",
            "22:00": "69"
        },
        "targets": [
            "device4",
            "device7"
        ]
    }
}


# Full test configs used to create fake Configs + Nodes (see create_test_nodes)
# See test_config_1_edit_context etc for context objects generated when editing each config
test_config_1 = {
    "metadata": {
        "id": "Test1",
        "location": "Inside cabinet above microwave",
        "floor": "1",
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    "wifi": {
        "ssid": "mynetwork",
        "password": "hunter2"
    },
    "device1": {
        "_type": "pwm",
        "nickname": "Cabinet Lights",
        "pin": "4",
        "min_rule": "0",
        "max_rule": "1023",
        "default_rule": 1023,
        "schedule": {
            "22:00": "1023",
            "22:01": "fade/256/7140",
            "00:00": "fade/32/7200",
            "05:00": "Disabled"
        }
    },
    "device2": {
        "_type": "tasmota-relay",
        "nickname": "Overhead Lights",
        "ip": "192.168.1.217",
        "default_rule": "enabled",
        "schedule": {
            "05:00": "enabled",
            "22:00": "disabled"
        }
    },
    "sensor1": {
        "_type": "pir",
        "nickname": "Motion Sensor",
        "pin": "15",
        "default_rule": "2",
        "targets": [
            "device1",
            "device2"
        ],
        "schedule": {
            "10:00": "2",
            "22:00": "2"
        }
    }
}


test_config_2 = {
    "metadata": {
        "id": "Test2",
        "location": "Bedroom",
        "floor": "2",
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    "wifi": {
        "ssid": "mynetwork",
        "password": "hunter2"
    },
    "device1": {
        "nickname": "Air Conditioner",
        "_type": "api-target",
        "ip": "192.168.1.124",
        "default_rule": {
            "on": [
                "ir_key",
                "ac",
                "start"
            ],
            "off": [
                "ir_key",
                "ac",
                "stop"
            ]
        },
        "schedule": {
            "10:00": {
                "on": [
                    "ir_key",
                    "ac",
                    "start"
                ],
                "off": [
                    "ir_key",
                    "ac",
                    "stop"
                ]
            },
            "00:00": {
                "on": [
                    "ir_key",
                    "ac",
                    "stop"
                ],
                "off": [
                    "ir_key",
                    "ac",
                    "stop"
                ]
            }
        }
    },
    "sensor1": {
        "_type": "si7021",
        "nickname": "Thermostat",
        "mode": "cool",
        "tolerance": "0.5",
        "default_rule": 74,
        "targets": [
            "device1"
        ],
        "schedule": {}
    },
    "ir_blaster": {
        "nickname": "",
        "pin": "19",
        "target": [
            "ac"
        ]
    }
}


test_config_3 = {
    "metadata": {
        "id": "Test3",
        "location": "Inside cabinet under sink",
        "floor": "1",
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    "wifi": {
        "ssid": "mynetwork",
        "password": "hunter2"
    },
    "device1": {
        "_type": "pwm",
        "nickname": "Bathroom LEDs",
        "pin": "4",
        "min_rule": "0",
        "max_rule": "1023",
        "default_rule": 0,
        "schedule": {
            "22:00": "1023",
            "22:01": "fade/256/7140",
            "00:00": "fade/32/7200",
            "05:00": "Disabled"
        }
    },
    "device2": {
        "_type": "tasmota-relay",
        "nickname": "Bathroom Lights",
        "ip": "192.168.1.239",
        "default_rule": "enabled",
        "schedule": {
            "05:00": "enabled",
            "22:00": "disabled"
        }
    },
    "device3": {
        "_type": "tasmota-relay",
        "nickname": "Entry Light",
        "ip": "192.168.1.202",
        "default_rule": "enabled",
        "schedule": {
            "05:00": "enabled",
            "23:00": "disabled"
        }
    },
    "sensor1": {
        "_type": "pir",
        "nickname": "Motion Sensor (Bath)",
        "pin": "15",
        "default_rule": "2",
        "targets": [
            "device1",
            "device2"
        ],
        "schedule": {
            "10:00": "2",
            "22:00": "2"
        }
    },
    "sensor2": {
        "_type": "pir",
        "nickname": "Motion Sensor (Entry)",
        "pin": "16",
        "default_rule": "1",
        "targets": [
            "device3"
        ],
        "schedule": {
            "00:00": "1"
        }
    }
}


# Full context objects returned by edit_config view for each of the 3 test configs
test_config_1_edit_context = {
    "NAME": "Test1",
    "TITLE": "Editing Test1",
    "IP": "192.168.1.123",
    "FILENAME": "test1.json",
    "config": {
        "metadata": {
            "id": "Test1",
            "location": "Inside cabinet above microwave",
            "floor": "1",
            "schedule_keywords": {
                "sunrise": "06:00",
                "sunset": "18:00"
            }
        },
        "wifi": {
            "ssid": "mynetwork",
            "password": "hunter2"
        },
        "device1": {
            "type": "pwm",
            "nickname": "Cabinet Lights",
            "pin": "4",
            "min_rule": "0",
            "max_rule": "1023",
            "default_rule": 1023,
            "schedule": {
                "22:00": "1023",
                "22:01": "fade/256/7140",
                "00:00": "fade/32/7200",
                "05:00": "Disabled"
            },
            "metadata": {
                "config_name": "pwm",
                "class_name": "LedStrip",
                "dependencies": [
                    "devices/LedStrip.py",
                    "devices/DimmableLight.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "pwm",
                    "nickname": "placeholder",
                    "min_rule": "placeholder",
                    "max_rule": "placeholder",
                    "default_rule": "placeholder",
                    "pin": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "int_or_fade",
                "rule_limits": [0, 1023]
            }
        },
        "device2": {
            "type": "tasmota-relay",
            "nickname": "Overhead Lights",
            "ip": "192.168.1.217",
            "default_rule": "enabled",
            "schedule": {
                "05:00": "enabled",
                "22:00": "disabled"
            },
            "metadata": {
                "config_name": "tasmota-relay",
                "class_name": "TasmotaRelay",
                "dependencies": [
                    "devices/TasmotaRelay.py",
                    "devices/HttpGet.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "tasmota-relay",
                    "nickname": "placeholder",
                    "ip": "placeholder",
                    "default_rule": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "standard"
            }
        },
        "sensor1": {
            "type": "pir",
            "nickname": "Motion Sensor",
            "pin": "15",
            "default_rule": "2",
            "targets": [
                "device1",
                "device2"
            ],
            "schedule": {
                "10:00": "2",
                "22:00": "2"
            },
            "metadata": {
                "config_name": "pir",
                "class_name": "MotionSensor",
                "dependencies": [
                    "sensors/MotionSensor.py",
                    "sensors/Sensor.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "pir",
                    "nickname": "placeholder",
                    "default_rule": "placeholder",
                    "pin": "placeholder",
                    "schedule": {},
                    "targets": []
                },
                "rule_prompt": "float_range",
                "rule_limits": [0, 60]
            }
        }
    },
    "api_target_options": {
        "addresses": {
            "self-target": "192.168.1.123",
            "Test2": "192.168.1.124",
            "Test3": "192.168.1.125"
        },
        "self-target": {
            "device1-Cabinet Lights (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Overhead Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        },
        "Test2": {
            "device1-Air Conditioner (api-target)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Thermostat (si7021)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule"
            ],
            "ir_blaster-Ir Blaster": {
                "ac": [
                    "start",
                    "stop",
                    "off"
                ]
            },
            "ignore": {}
        },
        "Test3": {
            "device1-Bathroom LEDs (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Bathroom Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device3-Entry Light (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (Bath) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "sensor2-Motion Sensor (Entry) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        }
    },
    "templates": config_templates
}


test_config_2_edit_context = {
    "NAME": "Test2",
    "TITLE": "Editing Test2",
    "IP": "192.168.1.124",
    "FILENAME": "test2.json",
    "config": {
        "metadata": {
            "id": "Test2",
            "location": "Bedroom",
            "floor": "2",
            "schedule_keywords": {
                "sunrise": "06:00",
                "sunset": "18:00"
            }
        },
        "wifi": {
            "ssid": "mynetwork",
            "password": "hunter2"
        },
        "device1": {
            "nickname": "Air Conditioner",
            "type": "api-target",
            "ip": "192.168.1.124",
            "default_rule": "{\"on\": [\"ir_key\", \"ac\", \"start\"], \"off\": [\"ir_key\", \"ac\", \"stop\"]}",
            "schedule": {
                "10:00": "{\"on\": [\"ir_key\", \"ac\", \"start\"], \"off\": [\"ir_key\", \"ac\", \"stop\"]}",
                "00:00": "{\"on\": [\"ir_key\", \"ac\", \"stop\"], \"off\": [\"ir_key\", \"ac\", \"stop\"]}"
            },
            "metadata": {
                "config_name": "api-target",
                "class_name": "ApiTarget",
                "dependencies": [
                    "devices/ApiTarget.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "api-target",
                    "nickname": "placeholder",
                    "ip": "placeholder",
                    "default_rule": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "api_target"
            }
        },
        "sensor1": {
            "type": "si7021",
            "nickname": "Thermostat",
            "mode": "cool",
            "tolerance": "0.5",
            "default_rule": 74,
            "targets": [
                "device1"
            ],
            "schedule": {},
            "metadata": {
                "config_name": "si7021",
                "class_name": "Thermostat",
                "dependencies": [
                    "sensors/Thermostat.py",
                    "sensors/Sensor.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "si7021",
                    "nickname": "placeholder",
                    "default_rule": "placeholder",
                    "mode": "placeholder",
                    "tolerance": "placeholder",
                    "schedule": {},
                    "targets": []
                },
                "rule_prompt": "float_range",
                "rule_limits": [65, 80]
            }
        },
        "ir_blaster": {
            "nickname": "",
            "pin": "19",
            "target": [
                "ac"
            ]
        }
    },
    "api_target_options": {
        "addresses": {
            "self-target": "192.168.1.124",
            "Test1": "192.168.1.123",
            "Test3": "192.168.1.125"
        },
        "self-target": {
            "device1-Air Conditioner (api-target)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule"
            ],
            "sensor1-Thermostat (si7021)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule"
            ],
            "ir_blaster-Ir Blaster": {
                "ac": [
                    "start",
                    "stop",
                    "off"
                ]
            },
            "ignore": {}
        },
        "Test1": {
            "device1-Cabinet Lights (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Overhead Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        },
        "Test3": {
            "device1-Bathroom LEDs (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Bathroom Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device3-Entry Light (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (Bath) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "sensor2-Motion Sensor (Entry) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        }
    },
    "templates": config_templates
}


test_config_3_edit_context = {
    "NAME": "Test3",
    "TITLE": "Editing Test3",
    "IP": "192.168.1.125",
    "FILENAME": "test3.json",
    "config": {
        "metadata": {
            "id": "Test3",
            "location": "Inside cabinet under sink",
            "floor": "1",
            "schedule_keywords": {
                "sunrise": "06:00",
                "sunset": "18:00"
            }
        },
        "wifi": {
            "ssid": "mynetwork",
            "password": "hunter2"
        },
        "device1": {
            "type": "pwm",
            "nickname": "Bathroom LEDs",
            "pin": "4",
            "min_rule": "0",
            "max_rule": "1023",
            "default_rule": 0,
            "schedule": {
                "22:00": "1023",
                "22:01": "fade/256/7140",
                "00:00": "fade/32/7200",
                "05:00": "Disabled"
            },
            "metadata": {
                "config_name": "pwm",
                "class_name": "LedStrip",
                "dependencies": [
                    "devices/LedStrip.py",
                    "devices/DimmableLight.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "pwm",
                    "nickname": "placeholder",
                    "min_rule": "placeholder",
                    "max_rule": "placeholder",
                    "default_rule": "placeholder",
                    "pin": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "int_or_fade",
                "rule_limits": [0, 1023]
            }
        },
        "device2": {
            "type": "tasmota-relay",
            "nickname": "Bathroom Lights",
            "ip": "192.168.1.239",
            "default_rule": "enabled",
            "schedule": {
                "05:00": "enabled",
                "22:00": "disabled"
            },
            "metadata": {
                "config_name": "tasmota-relay",
                "class_name": "TasmotaRelay",
                "dependencies": [
                    "devices/TasmotaRelay.py",
                    "devices/HttpGet.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "tasmota-relay",
                    "nickname": "placeholder",
                    "ip": "placeholder",
                    "default_rule": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "standard"
            }
        },
        "device3": {
            "type": "tasmota-relay",
            "nickname": "Entry Light",
            "ip": "192.168.1.202",
            "default_rule": "enabled",
            "schedule": {
                "05:00": "enabled",
                "23:00": "disabled"
            },
            "metadata": {
                "config_name": "tasmota-relay",
                "class_name": "TasmotaRelay",
                "dependencies": [
                    "devices/TasmotaRelay.py",
                    "devices/HttpGet.py",
                    "devices/Device.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "tasmota-relay",
                    "nickname": "placeholder",
                    "ip": "placeholder",
                    "default_rule": "placeholder",
                    "schedule": {}
                },
                "rule_prompt": "standard"
            }
        },
        "sensor1": {
            "type": "pir",
            "nickname": "Motion Sensor (Bath)",
            "pin": "15",
            "default_rule": "2",
            "targets": [
                "device1",
                "device2"
            ],
            "schedule": {
                "10:00": "2",
                "22:00": "2"
            },
            "metadata": {
                "config_name": "pir",
                "class_name": "MotionSensor",
                "dependencies": [
                    "sensors/MotionSensor.py",
                    "sensors/Sensor.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "pir",
                    "nickname": "placeholder",
                    "default_rule": "placeholder",
                    "pin": "placeholder",
                    "schedule": {},
                    "targets": []
                },
                "rule_prompt": "float_range",
                "rule_limits": [0, 60]
            }
        },
        "sensor2": {
            "type": "pir",
            "nickname": "Motion Sensor (Entry)",
            "pin": "16",
            "default_rule": "1",
            "targets": [
                "device3"
            ],
            "schedule": {
                "00:00": "1"
            },
            "metadata": {
                "config_name": "pir",
                "class_name": "MotionSensor",
                "dependencies": [
                    "sensors/MotionSensor.py",
                    "sensors/Sensor.py",
                    "core/Instance.py"
                ],
                "config_template": {
                    "_type": "pir",
                    "nickname": "placeholder",
                    "default_rule": "placeholder",
                    "pin": "placeholder",
                    "schedule": {},
                    "targets": []
                },
                "rule_prompt": "float_range",
                "rule_limits": [0, 60]
            }
        }
    },
    "api_target_options": {
        "addresses": {
            "self-target": "192.168.1.125",
            "Test1": "192.168.1.123",
            "Test2": "192.168.1.124"
        },
        "self-target": {
            "device1-Bathroom LEDs (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Bathroom Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device3-Entry Light (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (Bath) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "sensor2-Motion Sensor (Entry) (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        },
        "Test1": {
            "device1-Cabinet Lights (pwm)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "device2-Overhead Lights (tasmota-relay)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Motion Sensor (pir)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "trigger_sensor"
            ],
            "ignore": {}
        },
        "Test2": {
            "device1-Air Conditioner (api-target)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule",
                "turn_on",
                "turn_off"
            ],
            "sensor1-Thermostat (si7021)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule"
            ],
            "ir_blaster-Ir Blaster": {
                "ac": [
                    "start",
                    "stop",
                    "off"
                ]
            },
            "ignore": {}
        }
    },
    "templates": config_templates
}
