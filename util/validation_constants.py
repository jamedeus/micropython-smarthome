# All valid ESP32 pins, excluding input-only
valid_device_pins = (
    '4',
    '13',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33'
)


# All valid ESP32 pins, including input-only
valid_sensor_pins = (
    '4',
    '5',
    '13',
    '14',
    '15',
    '16',
    '17',
    '18',
    '19',
    '21',
    '22',
    '23',
    '25',
    '26',
    '27',
    '32',
    '33',
    '34',
    '35',
    '36',
    '39'
)


# Required keys for all config files
valid_config_keys = {
    "metadata": {
        "id": "",
        "location": "",
        "floor": "",
        "schedule_keywords": ""
    },
    "wifi": {
        "ssid": "",
        "password": ""
    }
}


# Config skeletons for all device and sensor types
config_templates = {
    "device": {
        "Dimmer": {
            "_type": "dimmer",
            "nickname": "placeholder",
            "ip": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Bulb": {
            "_type": "bulb",
            "nickname": "placeholder",
            "ip": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Relay": {
            "_type": "relay",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "DumbRelay": {
            "_type": "dumb-relay",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "DesktopTarget": {
            "_type": "desktop",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "LedStrip": {
            "_type": "pwm",
            "nickname": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "Mosfet": {
            "_type": "mosfet",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "ApiTarget": {
            "_type": "api-target",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Wled": {
            "_type": "wled",
            "nickname": "placeholder",
            "ip": "placeholder",
            "min_bright": "placeholder",
            "max_bright": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },
    },

    "sensor": {
        "MotionSensor": {
            "_type": "pir",
            "nickname": "placeholder",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "schedule": {},
            "targets": []
        },

        "DesktopTrigger": {
            "_type": "desktop",
            "nickname": "placeholder",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {},
            "targets": []
        },

        "Thermostat": {
            "_type": "si7021",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "mode": "placeholder",
            "tolerance": "placeholder",
            "schedule": {},
            "targets": []
        },

        "Dummy": {
            "_type": "dummy",
            "nickname": "placeholder",
            "default_rule": "placeholder",
            "schedule": {},
            "targets": []
        },

        "Switch": {
            "_type": "switch",
            "nickname": "placeholder",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "schedule": {},
            "targets": []
        }
    }
}


# Options for each supported IR Blaster target device, used to populate ApiTarget menu
ir_blaster_options = {
    "tv": ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'],
    "ac": ['start', 'stop', 'off']
}


# API endpoints supported with device as target instance
# Used to populate options for ApiTarget rules
device_endpoints = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off']


# API endpoints supported with sensor as target instance
# Used to populate options for ApiTarget rules
sensor_endpoints = ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']
