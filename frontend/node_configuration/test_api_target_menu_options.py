from django.test import TestCase
from .get_api_target_menu_options import convert_config_to_api_target_options
from .views import get_api_target_menu_options
from .models import Node

# Large JSON objects, helper functions
from .unit_test_helpers import (
    create_test_nodes,
    create_config_and_node_from_json
)


# Test function that generates JSON used to populate API target set_rule menu
class ApiTargetMenuOptionsTest(TestCase):
    def test_empty_database(self):
        # Should return empty template when no Nodes exist
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}})

    def test_from_api_frontend(self):
        # Create nodes
        create_test_nodes()

        # Options that should be returned for these test nodes
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "Test1": "192.168.1.123",
                "Test2": "192.168.1.124",
                "Test3": "192.168.1.125"
            },
            "self-target": {},
            "Test1": {
                "device1": {
                    "display": "Cabinet Lights (pwm)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Overhead Lights (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Motion Sensor (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "ignore": {
                    "display": "Ignore action"
                }
            },
            "Test2": {
                "device1": {
                    "display": "Air Conditioner (api-target)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Lights (api-target)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Thermostat (si7021)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule"
                    ]
                },
                "ir_key": {
                    "display": "Ir Blaster",
                    "options": [
                        "ac"
                    ],
                    "keys": {
                        "ac": [
                            "start",
                            "stop",
                            "off"
                        ]
                    }
                },
                "ignore": {
                    "display": "Ignore action"
                }
            },
            "Test3": {
                "device1": {
                    "display": "Bathroom LEDs (pwm)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Bathroom Lights (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device3": {
                    "display": "Entry Light (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Motion Sensor (Bath) (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "sensor2": {
                    "display": "Motion Sensor (Entry) (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "ignore": {
                    "display": "Ignore action"
                }
            }
        }

        # Request options with no argument (used by Api frontend)
        options = get_api_target_menu_options()

        # Should return valid options for each device and sensor of all existing nodes
        self.assertEqual(options, expected_options)

    def test_from_edit_config(self):
        # Create nodes
        create_test_nodes()

        # Options that should be returned for these test nodes
        expected_options = {
            "addresses": {
                "self-target": "192.168.1.123",
                "Test2": "192.168.1.124",
                "Test3": "192.168.1.125"
            },
            "self-target": {
                "device1": {
                    "display": "Cabinet Lights (pwm)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Overhead Lights (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Motion Sensor (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "ignore": {
                    "display": "Ignore action"
                }
            },
            "Test2": {
                "device1": {
                    "display": "Air Conditioner (api-target)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Lights (api-target)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Thermostat (si7021)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule"
                    ]
                },
                "ir_key": {
                    "display": "Ir Blaster",
                    "options": [
                        "ac"
                    ],
                    "keys": {
                        "ac": [
                            "start",
                            "stop",
                            "off"
                        ]
                    }
                },
                "ignore": {
                    "display": "Ignore action"
                }
            },
            "Test3": {
                "device1": {
                    "display": "Bathroom LEDs (pwm)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device2": {
                    "display": "Bathroom Lights (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "device3": {
                    "display": "Entry Light (tasmota-relay)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "turn_on",
                        "turn_off"
                    ]
                },
                "sensor1": {
                    "display": "Motion Sensor (Bath) (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "sensor2": {
                    "display": "Motion Sensor (Entry) (pir)",
                    "options": [
                        "enable",
                        "disable",
                        "enable_in",
                        "disable_in",
                        "set_rule",
                        "reset_rule",
                        "trigger_sensor"
                    ]
                },
                "ignore": {
                    "display": "Ignore action"
                }
            }
        }

        # Request options with friendly name as argument (used by edit_config)
        options = get_api_target_menu_options('Test1')

        # Should return valid options for each device and sensor of all existing nodes, except Test1
        # Should include Test1's options in self-target section, should not be in main section
        self.assertEqual(options, expected_options)

    # Original bug: IR Blaster options always included both TV and AC, even if only one configured.
    # Fixed in 8ab9367b, now only includes available options.
    def test_regression_ir_blaster(self):
        # Base config with no IR Blaster options
        config = {
            'metadata': {
                'id': 'ir_test',
                'location': 'Bedroom',
                'floor': '2'
            },
            'wifi': {
                'ssid': 'wifi',
                'password': '1234'
            }
        }

        # IR Blaster configs with all possible combinations of targets
        no_target_config = {
            'pin': '19',
            'target': []
        }
        ac_target_config = {
            'pin': '19',
            'target': ['ac']
        }
        tv_target_config = {
            'pin': '19',
            'target': ['tv']
        }
        both_target_config = {
            'pin': '19',
            'target': ['ac', 'tv']
        }

        # No targets: All options should be removed
        config['ir_blaster'] = no_target_config
        expected_options = {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}}

        # Create, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for AC-only config
        config['ir_blaster'] = ac_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ir_key": {
                    "display": "Ir Blaster",
                    "options": [
                        "ac"
                    ],
                    "keys": {
                        "ac": [
                            "start",
                            "stop",
                            "off"
                        ]
                    }
                },
                "ignore": {
                    "display": "Ignore action"
                }
            }
        }

        # Create AC-only config, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for TV-only config
        config['ir_blaster'] = tv_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ir_key": {
                    "display": "Ir Blaster",
                    "options": [
                        "tv"
                    ],
                    "keys": {
                        "tv": [
                            "power",
                            "vol_up",
                            "vol_down",
                            "mute",
                            "up",
                            "down",
                            "left",
                            "right",
                            "enter",
                            "settings",
                            "exit",
                            "source"
                        ]
                    }
                },
                "ignore": {
                    "display": "Ignore action"
                }
            }
        }

        # Create TV-only config, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for config with both TV and AC, same as before bug fix
        config['ir_blaster'] = both_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ir_key": {
                    "display": "Ir Blaster",
                    "options": [
                        "tv",
                        "ac"
                    ],
                    "keys": {
                        "tv": [
                            "power",
                            "vol_up",
                            "vol_down",
                            "mute",
                            "up",
                            "down",
                            "left",
                            "right",
                            "enter",
                            "settings",
                            "exit",
                            "source"
                        ],
                        "ac": [
                            "start",
                            "stop",
                            "off"
                        ]
                    }
                },
                "ignore": {
                    "display": "Ignore action"
                }
            }
        }

        # Create config with both TV and AC, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

    # Original bug: It was possible to set ApiTarget to turn itself on/off, resulting in
    # an infinite loop. These commands are no longer included for api-target instances
    # while self-targeting. Fixed in b8b8b0bf.
    def test_regression_self_target_infinite_loop(self):
        # Create nodes
        create_test_nodes()

        # ApiTarget options self-target section does not include turn_on or turn_off (infinite loop)
        expected_options = {
            "device1": {
                "display": "Air Conditioner (api-target)",
                "options": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule"
                ]
            },
            "device2": {
                "display": "Lights (api-target)",
                "options": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule"
                ]
            },
            "sensor1": {
                "display": "Thermostat (si7021)",
                "options": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule"
                ]
            },
            "ir_key": {
                "display": "Ir Blaster",
                "options": [
                    "ac"
                ],
                "keys": {
                    "ac": [
                        "start",
                        "stop",
                        "off"
                    ]
                }
            },
            "ignore": {
                "display": "Ignore action"
            }
        }

        # Request options for node with ApiTarget, confirm no turn_on/turn_off
        options = get_api_target_menu_options('Test2')
        self.assertEqual(options['self-target'], expected_options)

    # Original bug: The self-target conditional in get_api_target_menu_options contained a
    # dict comprehension intended to remove turn_on and turn_off from api-target instances,
    # but it also removed all instances with types other than api-target. Fixed in 069e6b29.
    def test_regression_self_target_missing_other_instances(self):
        # Create nodes
        create_test_nodes()

        # Request options for node with ApiTarget, confirm options exist for all instances
        options = get_api_target_menu_options('Test2')
        self.assertIn('device1', options['self-target'].keys())
        self.assertEqual(
            'Air Conditioner (api-target)',
            options['self-target']['device1']['display']
        )
        self.assertIn('sensor1', options['self-target'].keys())
        self.assertEqual(
            'Thermostat (si7021)',
            options['self-target']['sensor1']['display']
        )
        self.assertIn('ir_key', options['self-target'].keys())
        self.assertEqual(
            'Ir Blaster',
            options['self-target']['ir_key']['display']
        )
        self.assertIn('ignore', options['self-target'].keys())

    # Original bug: Function that adds endpoints used conditional with hard-coded sensor
    # types to determine if trigger_sensor was supported. When new non-triggerable sensors
    # were added they incorrectly received trigger_sensor option. Now checks triggerable
    # param in metadata object to determine if endpoint compatible.
    def test_regression_check_metadata(self):
        # Create test config with new non-triggerable type
        config = {
            'metadata': {},
            'wifi': {},
            'sensor1': {
                'nickname': 'Thermostat',
                '_type': 'dht22'
            }
        }

        # Pass to function, confirm options does not contain trigger_sensor
        options = convert_config_to_api_target_options(config.copy())
        self.assertNotIn('trigger_sensor', options['sensor1']['options'])

        # Change sensor to a triggerable type, confirm options include trigger_sensor
        config['sensor1']['_type'] = 'pir'
        options = convert_config_to_api_target_options(config)
        self.assertIn('trigger_sensor', options['sensor1']['options'])
