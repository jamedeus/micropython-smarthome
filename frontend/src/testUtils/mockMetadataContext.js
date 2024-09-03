export const edit_config_metadata = {
    "devices": {
        "http-get": {
            "config_name": "http-get",
            "class_name": "HttpGet",
            "display_name": "HTTP Get Request",
            "dependencies": [
                "devices/HttpGet.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "http-get",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "uri": "placeholder",
                "on_path": "placeholder",
                "off_path": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "standard"
        },
        "pwm": {
            "config_name": "pwm",
            "class_name": "LedStrip",
            "display_name": "LED Strip",
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
            "rule_limits": [
                0,
                1023
            ]
        },
        "desktop": {
            "config_name": "desktop",
            "class_name": "DesktopTarget",
            "display_name": "Computer Screen",
            "dependencies": [
                "devices/DesktopTarget.py",
                "devices/HttpGet.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "desktop",
                "nickname": "placeholder",
                "ip": "placeholder",
                "default_rule": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "standard"
        },
        "tasmota-relay": {
            "config_name": "tasmota-relay",
            "class_name": "TasmotaRelay",
            "display_name": "Tasmota Smart Relay",
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
        },
        "dimmer": {
            "config_name": "dimmer",
            "class_name": "Tplink",
            "display_name": "TP Link Smart Dimmer",
            "dependencies": [
                "devices/Tplink.py",
                "devices/DimmableLight.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "dimmer",
                "nickname": "placeholder",
                "ip": "placeholder",
                "min_rule": "placeholder",
                "max_rule": "placeholder",
                "default_rule": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                100
            ]
        },
        "api-target": {
            "config_name": "api-target",
            "class_name": "ApiTarget",
            "display_name": "API command",
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
        },
        "relay": {
            "config_name": "relay",
            "class_name": "Relay",
            "display_name": "Relay",
            "dependencies": [
                "devices/Relay.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "relay",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "standard"
        },
        "bulb": {
            "config_name": "bulb",
            "class_name": "Tplink",
            "display_name": "TP Link Smart Bulb",
            "dependencies": [
                "devices/Tplink.py",
                "devices/DimmableLight.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "bulb",
                "nickname": "placeholder",
                "ip": "placeholder",
                "min_rule": "placeholder",
                "max_rule": "placeholder",
                "default_rule": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                100
            ]
        },
        "wled": {
            "config_name": "wled",
            "class_name": "Wled",
            "display_name": "WLED",
            "dependencies": [
                "devices/Wled.py",
                "devices/DimmableLight.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "wled",
                "nickname": "placeholder",
                "ip": "placeholder",
                "min_rule": "placeholder",
                "max_rule": "placeholder",
                "default_rule": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                255
            ]
        }
    },
    "sensors": {
        "switch": {
            "config_name": "switch",
            "class_name": "Switch",
            "display_name": "Switch",
            "dependencies": [
                "sensors/Switch.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "switch",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "standard",
            "triggerable": false
        },
        "dht22": {
            "config_name": "dht22",
            "class_name": "Dht22",
            "display_name": "DHT22 Temperature Sensor",
            "dependencies": [
                "sensors/Dht22.py",
                "sensors/Thermostat.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "dht22",
                "nickname": "placeholder",
                "units": "placeholder",
                "default_rule": "placeholder",
                "mode": "placeholder",
                "tolerance": "placeholder",
                "pin": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "thermostat",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "ld2410": {
            "config_name": "ld2410",
            "class_name": "MotionSensor",
            "display_name": "LD2410 Radar Sensor",
            "dependencies": [
                "sensors/MotionSensor.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "ld2410",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "float_range",
            "rule_limits": [
                0,
                60
            ],
            "triggerable": true
        },
        "si7021": {
            "config_name": "si7021",
            "class_name": "Si7021",
            "display_name": "SI7021 Temperature Sensor",
            "dependencies": [
                "sensors/Si7021.py",
                "sensors/Thermostat.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "si7021",
                "nickname": "placeholder",
                "units": "placeholder",
                "default_rule": "placeholder",
                "mode": "placeholder",
                "tolerance": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "thermostat",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "desktop": {
            "config_name": "desktop",
            "class_name": "DesktopTrigger",
            "display_name": "Computer Activity",
            "dependencies": [
                "sensors/DesktopTrigger.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "desktop",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "ip": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "standard",
            "triggerable": true
        },
        "pir": {
            "config_name": "pir",
            "class_name": "MotionSensor",
            "display_name": "PIR Motion Sensor",
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
            "rule_limits": [
                0,
                60
            ],
            "triggerable": true
        },
        "load-cell": {
            "config_name": "load-cell",
            "class_name": "LoadCell",
            "display_name": "Load Cell Pressure Sensor",
            "dependencies": [
                "sensors/LoadCell.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "load-cell",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin_data": "placeholder",
                "pin_clock": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "float_range",
            "rule_limits": [
                0,
                10000000
            ],
            "triggerable": false
        },
        "dummy": {
            "config_name": "dummy",
            "class_name": "Dummy",
            "display_name": "Dummy Sensor",
            "dependencies": [
                "sensors/Dummy.py",
                "sensors/Sensor.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "dummy",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "schedule": {},
                "targets": []
            },
            "rule_prompt": "on_off",
            "triggerable": true
        }
    }
};

export const api_card_metadata = {
    "devices": {
        "http-get": {
            "rule_prompt": "standard"
        },
        "pwm": {
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                0,
                1023
            ]
        },
        "desktop": {
            "rule_prompt": "standard"
        },
        "tasmota-relay": {
            "rule_prompt": "standard"
        },
        "dimmer": {
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                100
            ]
        },
        "api-target": {
            "rule_prompt": "api_target"
        },
        "relay": {
            "rule_prompt": "standard"
        },
        "bulb": {
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                100
            ]
        },
        "wled": {
            "rule_prompt": "int_or_fade",
            "rule_limits": [
                1,
                255
            ]
        }
    },
    "sensors": {
        "switch": {
            "rule_prompt": "standard",
            "triggerable": false
        },
        "dht22": {
            "rule_prompt": "thermostat",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "ld2410": {
            "rule_prompt": "float_range",
            "rule_limits": [
                0,
                60
            ],
            "triggerable": true
        },
        "si7021": {
            "rule_prompt": "thermostat",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "desktop": {
            "rule_prompt": "standard",
            "triggerable": true
        },
        "pir": {
            "rule_prompt": "float_range",
            "rule_limits": [
                0,
                60
            ],
            "triggerable": true
        },
        "load-cell": {
            "rule_prompt": "float_range",
            "rule_limits": [
                0,
                10000000
            ],
            "triggerable": false
        },
        "dummy": {
            "rule_prompt": "on_off",
            "triggerable": true
        }
    }
};
