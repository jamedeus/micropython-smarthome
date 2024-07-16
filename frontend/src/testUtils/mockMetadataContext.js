export const edit_config_metadata = {
    "devices": {
        "mosfet": {
            "config_name": "mosfet",
            "class_name": "Mosfet",
            "dependencies": [
                "devices/Mosfet.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "mosfet",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "standard"
        },
        "http-get": {
            "config_name": "http-get",
            "class_name": "HttpGet",
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
            "dependencies": [
                "devices/Desktop_target.py",
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
            "class_name": "Dimmer",
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
        "dumb-relay": {
            "config_name": "dumb-relay",
            "class_name": "DumbRelay",
            "dependencies": [
                "devices/DumbRelay.py",
                "devices/Device.py",
                "core/Instance.py"
            ],
            "config_template": {
                "_type": "dumb-relay",
                "nickname": "placeholder",
                "default_rule": "placeholder",
                "pin": "placeholder",
                "schedule": {}
            },
            "rule_prompt": "standard"
        },
        "bulb": {
            "config_name": "bulb",
            "class_name": "Bulb",
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
            "rule_prompt": "float_range",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "si7021": {
            "config_name": "si7021",
            "class_name": "Si7021",
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
            "rule_prompt": "float_range",
            "rule_limits": [
                18,
                27
            ],
            "triggerable": false
        },
        "desktop": {
            "config_name": "desktop",
            "class_name": "DesktopTrigger",
            "dependencies": [
                "sensors/Desktop_trigger.py",
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
}
