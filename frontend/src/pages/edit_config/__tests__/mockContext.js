// NOTE: Does not include metadata, see frontend/src/testUtils/mockMetadataContext.js
// api_target_options moved to separate apiTargetOptionsContext (avoid duplication)
export const newConfigContext = {
    "TITLE": "Create New Config",
    "config": {
        "metadata": {
            "id": "",
            "floor": "",
            "location": ""
        },
        "schedule_keywords": {
            "morning": "08:00",
            "sleep": "23:00",
            "sunrise": "06:00",
            "sunset": "18:00",
            "relax": "20:00"
        }
    },
    "edit_existing": false,
    "ir_blaster_targets": [
        "samsung_tv",
        "whynter_ac"
    ]
};

export const existingConfigContext = {
    "IP": "192.168.1.100",
    "NAME": "All devices and sensors",
    "TITLE": "Editing All devices and sensors",
    "FILENAME": "all-devices-and-sensors.json",
    "edit_existing": true,
    "ir_blaster_targets": [
        "samsung_tv",
        "whynter_ac"
    ],
    "config": {
        "metadata": {
            "id": "All devices and sensors",
            "floor": 404,
            "location": "unit tests",
            "gps": {
                "lat": "-77.8401068",
                "lon": "166.6425345"
            }
        },
        "schedule_keywords": {
            "morning": "08:00",
            "sleep": "23:00",
            "sunrise": "06:00",
            "sunset": "18:00",
            "relax": "20:00"
        },
        "sensor1": {
            "_type": "switch",
            "nickname": "Door switch",
            "default_rule": "enabled",
            "pin": "21",
            "schedule": {},
            "targets": [
                "device9",
                "device2",
                "device3",
                "device5",
                "device8"
            ]
        },
        "ir_blaster": {
            "pin": "13",
            "target": [
                "samsung_tv"
            ]
        },
        "sensor2": {
            "_type": "dht22",
            "nickname": "Temp sensor",
            "units": "fahrenheit",
            "default_rule": 74,
            "mode": "cool",
            "tolerance": 1,
            "pin": "27",
            "schedule": {
                "morning": 68,
                "relax": 72,
                "12:00": "disabled"
            },
            "targets": [
                "device6",
                "device7"
            ]
        },
        "sensor3": {
            "_type": "si7021",
            "nickname": "Thermostat",
            "units": "celsius",
            "default_rule": 20,
            "mode": "heat",
            "tolerance": 1,
            "schedule": {
                "morning": 23,
                "sleep": 20
            },
            "targets": [
                "device1"
            ]
        },
        "sensor4": {
            "_type": "desktop",
            "nickname": "Computer activity",
            "default_rule": "enabled",
            "ip": "192.168.1.200",
            "schedule": {
                "morning": "enabled",
                "sleep": "disabled"
            },
            "targets": [
                "device3",
                "device9",
                "device5"
            ]
        },
        "sensor5": {
            "_type": "pir",
            "nickname": "Motion",
            "default_rule": 10,
            "pin": "26",
            "schedule": {
                "morning": 10,
                "sleep": 1
            },
            "targets": [
                "device4",
                "device2",
                "device8"
            ]
        },
        "device1": {
            "_type": "http-get",
            "nickname": "Heater",
            "default_rule": "enabled",
            "uri": "http://192.168.1.250",
            "on_path": "api/heat_on",
            "off_path": "api/heat_off",
            "schedule": {}
        },
        "device2": {
            "_type": "pwm",
            "nickname": "Accent lights",
            "min_rule": 32,
            "max_rule": 1023,
            "default_rule": 767,
            "pin": "18",
            "schedule": {
                "morning": 1023,
                "relax": "fade/512/1800",
                "sleep": "disabled"
            }
        },
        "device3": {
            "_type": "desktop",
            "nickname": "Computer screen",
            "ip": "192.168.1.200",
            "default_rule": "enabled",
            "schedule": {
                "morning": "enabled",
                "sleep": "disabled"
            }
        },
        "device4": {
            "_type": "tasmota-relay",
            "nickname": "Stairway lights",
            "ip": "192.168.1.212",
            "default_rule": "enabled",
            "schedule": {}
        },
        "device5": {
            "_type": "dimmer",
            "nickname": "Overhead lights",
            "ip": "192.168.1.211",
            "min_rule": 27,
            "max_rule": 100,
            "default_rule": 100,
            "schedule": {
                "morning": "fade/100/900",
                "relax": "fade/69/1800",
                "sleep": "fade/37/900"
            }
        },
        "device6": {
            "_type": "api-target",
            "nickname": "Air conditioner",
            "ip": "192.168.1.104",
            "default_rule": {
                "on": [
                    "ir_key",
                    "ac",
                    "start"
                ],
                "off": [
                    "ir_key",
                    "ac",
                    "off"
                ]
            },
            "schedule": {
                "morning": {
                    "on": [
                        "ir_key",
                        "ac",
                        "start"
                    ],
                    "off": [
                        "ir_key",
                        "ac",
                        "off"
                    ]
                }
            }
        },
        "device7": {
            "_type": "relay",
            "nickname": "Fan",
            "default_rule": "enabled",
            "pin": "16",
            "schedule": {}
        },
        "device8": {
            "_type": "bulb",
            "nickname": "Lamp",
            "ip": "192.168.1.205",
            "min_rule": 1,
            "max_rule": 100,
            "default_rule": 72,
            "schedule": {
                "morning": "fade/100/900",
                "relax": "fade/72/1800",
                "sleep": "disabled"
            }
        },
        "device9": {
            "_type": "wled",
            "nickname": "Bias lights",
            "ip": "192.168.1.233",
            "min_rule": 1,
            "max_rule": 255,
            "default_rule": 255,
            "schedule": {
                "morning": "fade/255/900",
                "sleep": 25,
                "relax": "fade/128/1800"
            }
        },
        "sensor6": {
            "_type": "dummy",
            "nickname": "Sunrise",
            "default_rule": "on",
            "schedule": {
                "sunrise": "on",
                "sunset": "off"
            },
            "targets": [
                "device5"
            ]
        }
    }
};

// Shared by all mock configs
export const apiTargetOptionsContext = {
    "addresses": {
        "self-target": "127.0.0.1",
        "Bathroom": "192.168.1.100",
        "Kitchen": "192.168.1.101",
        "Living Room": "192.168.1.102",
        "Bedroom": "192.168.1.103",
        "Thermostat": "192.168.1.104"
    },
    "self-target": {},
    "Bathroom": {
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
        "ignore": {
            "display": "Ignore action"
        }
    },
    "Kitchen": {
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
        "ignore": {
            "display": "Ignore action"
        }
    },
    "Living Room": {
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
        "sensor2": {
            "display": "Sunset Sensor (dummy)",
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
        "device1": {
            "display": "Overhead Lights (dimmer)",
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
            "display": "Lamp (bulb)",
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
            "display": "Porch Light (tasmota-relay)",
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
        "ignore": {
            "display": "Ignore action"
        }
    },
    "Thermostat": {
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
    },
    "Bedroom": {
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
        "device1": {
            "display": "Lights (dimmer)",
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
            "display": "Bias lights (wled)",
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
        "sensor2": {
            "display": "Override (dummy)",
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
};
