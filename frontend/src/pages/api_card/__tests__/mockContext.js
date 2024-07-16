// NOTE: Does not include metadata, see frontend/src/testUtils/mockMetadataContext.js
export const mockContext = {
    "status": {
        "metadata": {
            "next_reload": "3:46",
            "ir_blaster": false,
            "location": "Bedroom",
            "floor": 2,
            "id": "Thermostat",
            "schedule_keywords": {
                "sleep": "23:00",
                "morning": "08:00",
                "sunset": "20:56",
                "relax": "20:00",
                "sunrise": "05:36"
            }
        },
        "devices": {
            "device1": {
                "schedule": {},
                "scheduled_rule": "disabled",
                "enabled": false,
                "turned_on": false,
                "nickname": "Humidifier",
                "default_rule": "enabled",
                "current_rule": "disabled",
                "type": "mosfet"
            },
            "device2": {
                "current_rule": "enabled",
                "enabled": true,
                "type": "http-get",
                "turned_on": false,
                "schedule": {},
                "scheduled_rule": "enabled",
                "nickname": "Heater",
                "default_rule": "enabled"
            },
            "device3": {
                "current_rule": 767,
                "enabled": true,
                "type": "pwm",
                "turned_on": true,
                "schedule": {
                    "morning": 1023,
                    "relax": "fade/512/1800",
                    "sleep": "disabled"
                },
                "scheduled_rule": 1023,
                "min_rule": 0,
                "nickname": "Accent lights",
                "max_rule": 1023,
                "default_rule": 767
            },
            "device4": {
                "current_rule": "enabled",
                "enabled": true,
                "type": "desktop",
                "turned_on": false,
                "schedule": {
                    "morning": "enabled",
                    "sleep": "disabled"
                },
                "scheduled_rule": "enabled",
                "nickname": "Computer screen",
                "default_rule": "enabled"
            },
            "device5": {
                "current_rule": "enabled",
                "enabled": true,
                "type": "tasmota-relay",
                "turned_on": false,
                "schedule": {},
                "scheduled_rule": "enabled",
                "nickname": "Stairway lights",
                "default_rule": "enabled"
            },
            "device6": {
                "current_rule": 100,
                "enabled": true,
                "type": "dimmer",
                "turned_on": true,
                "schedule": {
                    "morning": "fade/100/900",
                    "relax": "fade/69/1800",
                    "sleep": "fade/37/900"
                },
                "scheduled_rule": 100,
                "min_rule": 1,
                "nickname": "Overhead lights",
                "max_rule": 100,
                "default_rule": 100
            },
            "device7": {
                "current_rule": {
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
                "enabled": true,
                "type": "api-target",
                "turned_on": true,
                "schedule": {},
                "scheduled_rule": {
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
                "nickname": "Air Conditioner",
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
                }
            },
            "device8": {
                "current_rule": "disabled",
                "enabled": false,
                "type": "dumb-relay",
                "turned_on": true,
                "schedule": {},
                "scheduled_rule": "enabled",
                "nickname": "Fan",
                "default_rule": "enabled"
            },
            "device9": {
                "current_rule": 100,
                "enabled": true,
                "type": "bulb",
                "turned_on": true,
                "schedule": {
                    "morning": "fade/100/900",
                    "relax": "fade/72/1800",
                    "sleep": "disabled"
                },
                "scheduled_rule": 100,
                "min_rule": 1,
                "nickname": "Lamp",
                "max_rule": 100,
                "default_rule": 100
            },
            "device10": {
                "current_rule": 255,
                "enabled": true,
                "type": "wled",
                "turned_on": false,
                "schedule": {
                    "morning": "fade/255/900",
                    "sleep": 25,
                    "relax": "fade/128/1800"
                },
                "scheduled_rule": 255,
                "min_rule": 1,
                "nickname": "Bias lights",
                "max_rule": 255,
                "default_rule": 255
            },
        },
        "sensors": {
            "sensor1": {
                "scheduled_rule": "enabled",
                "enabled": true,
                "targets": [
                    "device10",
                    "device3",
                    "device4",
                    "device6",
                    "device9"
                ],
                "nickname": "Door switch",
                "condition_met": false,
                "default_rule": "enabled",
                "current_rule": "enabled",
                "schedule": {},
                "type": "switch"
            },
            "sensor2": {
                "humid": 72.53317,
                "temp": 72.07256,
                "units": "fahrenheit",
                "scheduled_rule": 72,
                "enabled": true,
                "targets": [
                    "device7",
                    "device8"
                ],
                "nickname": "Motion",
                "condition_met": true,
                "default_rule": 74,
                "current_rule": 70,
                "schedule": {
                    "morning": 68,
                    "relax": 72
                },
                "type": "dht22"
            },
            "sensor3": {
                "humid": 72.53317,
                "temp": 22.26253,
                "units": "celsius",
                "scheduled_rule": 20,
                "enabled": true,
                "targets": [
                    "device2",
                    "device1"
                ],
                "nickname": "Motion",
                "condition_met": false,
                "default_rule": 20,
                "current_rule": 20,
                "schedule": {
                    "morning": 23,
                    "sleep": 20
                },
                "type": "si7021"
            },
            "sensor4": {
                "scheduled_rule": "enabled",
                "enabled": true,
                "targets": [
                    "device4",
                    "device10",
                    "device6"
                ],
                "nickname": "Computer activity",
                "condition_met": false,
                "default_rule": "enabled",
                "current_rule": "enabled",
                "schedule": {
                    "morning": "enabled",
                    "sleep": "disabled"
                },
                "type": "desktop"
            },
            "sensor5": {
                "scheduled_rule": 10,
                "enabled": true,
                "targets": [
                    "device5",
                    "device3",
                    "device9"
                ],
                "nickname": "Motion",
                "condition_met": true,
                "default_rule": 10,
                "current_rule": 10,
                "schedule": {
                    "morning": 10,
                    "sleep": 1
                },
                "type": "pir"
            },
            "sensor6": {
                "scheduled_rule": "on",
                "enabled": true,
                "targets": [
                    "device6"
                ],
                "nickname": "Sunrise",
                "condition_met": true,
                "default_rule": "on",
                "current_rule": "on",
                "schedule": {
                    "sunrise": "on",
                    "sunset": "off"
                },
                "type": "dummy"
            },
        }
    },
    "target_ip": "192.168.1.100",
    "recording": false,
    "api_target_options": {
        "device1": {
            "device1": {
                "display": "Bias Lights (wled)",
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
                "display": "HTPC (desktop)",
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
            "device2": {
                "display": "TV (api-target)",
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
        }
    }
};
