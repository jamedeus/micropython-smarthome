# Expected get_status response for test config 1
config1_status_object = {
    'metadata': {
        'id': 'Test1',
        'floor': '1',
        'location': 'Inside cabinet above microwave',
        'ir_blaster': False,
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'current_rule': 2.0,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device1',
                'device2'
            ],
            'schedule': {
                '10:00': '2',
                '22:00': '2'
            },
            'scheduled_rule': 2.0,
            'nickname': 'Motion Sensor',
            'condition_met': True
        }
    },
    'devices': {
        'device1': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'pwm',
            'schedule': {
                '00:00': 'fade/32/7200',
                '05:00': 'Disabled',
                '22:01': 'fade/256/7140',
                '22:00': '1023'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Cabinet Lights',
            'turned_on': True,
            'max_rule': 1023,
            'min_rule': 0
        },
        'device2': {
            'current_rule': 'enabled',
            'enabled': True,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '22:00': 'disabled'
            },
            'scheduled_rule': 'enabled',
            'nickname': 'Overhead Lights',
            'turned_on': True
        }
    }
}


# Expected API frontend context for test config 1
config1_api_context = {
    'metadata': {
        'id': 'Test1',
        'floor': '1',
        'location': 'Inside cabinet above microwave',
        'ir_blaster': False,
        'ip': '192.168.1.123',
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'current_rule': 2.0,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device1',
                'device2'
            ],
            'schedule': {
                '10:00': '2',
                '22:00': '2'
            },
            'scheduled_rule': 2.0,
            'nickname': 'Motion Sensor',
            'condition_met': True
        }
    },
    'devices': {
        'device1': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'pwm',
            'schedule': {
                '00:00': 'fade/32/7200',
                '05:00': 'Disabled',
                '22:01': 'fade/256/7140',
                '22:00': '1023'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Cabinet Lights',
            'turned_on': True,
            'max_rule': 1023,
            'min_rule': 0,
        },
        'device2': {
            'current_rule': 'enabled',
            'enabled': True,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '22:00': 'disabled'
            },
            'scheduled_rule': 'enabled',
            'nickname': 'Overhead Lights',
            'turned_on': True,
        }
    }
}


# Expected get_status response for test config 2
config2_status_object = {
    'metadata': {
        'id': 'Test2',
        'floor': '2',
        'location': 'Bedroom',
        'ir_blaster': True,
        'ir_targets': [
            'tv',
            'ac'
        ],
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'humid': -6,
            'scheduled_rule': 74,
            'enabled': True,
            'targets': [
                'device1'
            ],
            'nickname': 'Thermostat',
            'condition_met': False,
            'schedule': {},
            'current_rule': 74,
            'temp': -52.32999,
            'type': 'si7021',
            'units': 'fahrenheit'
        }
    },
    'devices': {
        'device1': {
            'current_rule': {
                'on': [
                    'ir_key',
                    'ac',
                    'start'
                ],
                'off': [
                    'ir_key',
                    'ac',
                    'stop'
                ]
            },
            'enabled': True,
            'type': 'api-target',
            'schedule': {
                '10:00': {
                    'on': [
                        'ir_key',
                        'ac',
                        'start'
                    ],
                    'off': [
                        'ir_key',
                        'ac',
                        'stop'
                    ]
                },
                '00:00': {
                    'on': [
                        'ir_key',
                        'ac',
                        'stop'
                    ],
                    'off': [
                        'ir_key',
                        'ac',
                        'stop'
                    ]
                }
            },
            'scheduled_rule': {
                'on': [
                    'ir_key',
                    'ac',
                    'start'
                ],
                'off': [
                    'ir_key',
                    'ac',
                    'stop'
                ]
            },
            'nickname': 'Air Conditioner',
            'turned_on': False
        }
    }
}


# Expected API frontend context for test config 2
config2_api_context = {
    'metadata': {
        'id': 'Test2',
        'floor': '2',
        'location': 'Bedroom',
        'ir_blaster': True,
        'ir_targets': [
            'tv',
            'ac'
        ],
        'ir_macros': {
            'macro1': [
                'tv power 500 1',
                'tv vol_up 15 10',
            ],
            'macro2': [
                'ac ON 0 1'
            ]
        },
        'ip': '192.168.1.124',
        'thermostat': True,
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'humid': -6.0,
            'scheduled_rule': 74.0,
            'enabled': True,
            'targets': [
                'device1'
            ],
            'nickname': 'Thermostat',
            'condition_met': False,
            'schedule': {

            },
            'current_rule': 74.0,
            'temp': -52.32999,
            'type': 'si7021',
            'units': 'fahrenheit'
        }
    },
    'devices': {
        'device1': {
            'current_rule': '{"on": ["ir_key", "ac", "start"], "off": ["ir_key", "ac", "stop"]}',
            'enabled': True,
            'type': 'api-target',
            'schedule': {
                '10:00': '{"on": ["ir_key", "ac", "start"], "off": ["ir_key", "ac", "stop"]}',
                '00:00': '{"on": ["ir_key", "ac", "stop"], "off": ["ir_key", "ac", "stop"]}'
            },
            'scheduled_rule': {
                'on': [
                    'ir_key',
                    'ac',
                    'start'
                ],
                'off': [
                    'ir_key',
                    'ac',
                    'stop'
                ]
            },
            'nickname': 'Air Conditioner',
            'turned_on': False
        }
    },
    'api_target_options': {
        "device1": {
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
    }
}


# Expected ir_get_existing_macros response for test config 2
config2_existing_macros = {
    'macro1': [
        'tv power 500 1',
        'tv vol_up 15 10',
    ],
    'macro2': [
        'ac ON 0 1'
    ]
}


# Expected get_status response for test config 3
config3_status_object = {
    'metadata': {
        'id': 'Test3',
        'floor': '1',
        'location': 'Inside cabinet under sink',
        'ir_blaster': False,
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'current_rule': 2,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device1',
                'device2'
            ],
            'schedule': {
                '10:00': '2',
                '22:00': '2'
            },
            'scheduled_rule': 2,
            'nickname': 'Motion Sensor (Bath)',
            'condition_met': True
        },
        'sensor2': {
            'current_rule': 1,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device3'
            ],
            'schedule': {
                '00:00': '1'
            },
            'scheduled_rule': 1,
            'nickname': 'Motion Sensor (Entry)',
            'condition_met': False
        }
    },
    'devices': {
        'device1': {
            'current_rule': 256,
            'enabled': True,
            'type': 'pwm',
            'schedule': {
                '00:00': 'fade/32/7200',
                '05:00': 'Disabled',
                '22:01': 'fade/256/7140',
                '22:00': '1023'
            },
            'scheduled_rule': 256,
            'nickname': 'Bathroom LEDs',
            'turned_on': True,
            'max_rule': 1023,
            'min_rule': 0
        },
        'device3': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '23:00': 'disabled'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Entry Light',
            'turned_on': False
        },
        'device2': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '22:00': 'disabled'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Bathroom Lights',
            'turned_on': True
        }
    }
}


# Expected API frontend context for test config 3
config3_api_context = {
    'metadata': {
        'id': 'Test3',
        'floor': '1',
        'location': 'Inside cabinet under sink',
        'ir_blaster': False,
        'ip': '192.168.1.215',
        "schedule_keywords": {
            "sunrise": "06:00",
            "sunset": "18:00"
        }
    },
    'sensors': {
        'sensor1': {
            'current_rule': 2.0,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device1',
                'device2'
            ],
            'schedule': {
                '10:00': '2',
                '22:00': '2'
            },
            'scheduled_rule': 2.0,
            'nickname': 'Motion Sensor (Bath)',
            'condition_met': True
        },
        'sensor2': {
            'current_rule': 1.0,
            'enabled': True,
            'type': 'pir',
            'targets': [
                'device3'
            ],
            'schedule': {
                '00:00': '1'
            },
            'scheduled_rule': 1.0,
            'nickname': 'Motion Sensor (Entry)',
            'condition_met': False
        }
    },
    'devices': {
        'device1': {
            'current_rule': 256,
            'enabled': True,
            'type': 'pwm',
            'schedule': {
                '00:00': 'fade/32/7200',
                '05:00': 'Disabled',
                '22:01': 'fade/256/7140',
                '22:00': '1023'
            },
            'scheduled_rule': 256,
            'nickname': 'Bathroom LEDs',
            'turned_on': True,
            'max_rule': 1023,
            'min_rule': 0
        },
        'device3': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '23:00': 'disabled'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Entry Light',
            'turned_on': False
        },
        'device2': {
            'current_rule': 'disabled',
            'enabled': False,
            'type': 'tasmota-relay',
            'schedule': {
                '05:00': 'enabled',
                '22:00': 'disabled'
            },
            'scheduled_rule': 'disabled',
            'nickname': 'Bathroom Lights',
            'turned_on': True
        }
    }
}
