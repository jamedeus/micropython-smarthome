export const mockNodes1floor = {
    "1": [
        "Bathroom",
        "Kitchen",
        "Living Room"
    ]
};

export const mockNodes2floors = {
    "1": [
        "Bathroom",
        "Kitchen",
        "Living Room"
    ],
    "2": [
        "Thermostat",
        "Bedroom"
    ]
};

export const mockMacros = {
    "late": [
        {
            "ip": "192.168.1.100",
            "args": [
                "set_rule",
                "device1",
                "519"
            ],
            "node_name": "Bathroom",
            "target_name": "Bathroom LEDs",
            "action_name": "Set Rule 519"
        },
        {
            "ip": "192.168.1.100",
            "args": [
                "disable",
                "device2",
                ""
            ],
            "node_name": "Bathroom",
            "target_name": "Bathroom Lights",
            "action_name": "Disable"
        },
        {
            "ip": "192.168.1.101",
            "args": [
                "set_rule",
                "device1",
                "665"
            ],
            "node_name": "Kitchen",
            "target_name": "Cabinet Lights",
            "action_name": "Set Rule 665"
        },
        {
            "ip": "192.168.1.101",
            "args": [
                "disable",
                "device2",
                ""
            ],
            "node_name": "Kitchen",
            "target_name": "Overhead Lights",
            "action_name": "Disable"
        },
        {
            "ip": "192.168.1.103",
            "args": [
                "set_rule",
                "device1",
                "42"
            ],
            "node_name": "Bedroom",
            "target_name": "Lights",
            "action_name": "Set Rule 42"
        },
        {
            "ip": "192.168.1.103",
            "args": [
                "enable",
                "sensor2",
                ""
            ],
            "node_name": "Bedroom",
            "target_name": "Computer Sensor",
            "action_name": "Enable"
        },
        {
            "ip": "192.168.1.102",
            "args": [
                "set_rule",
                "device1",
                "42"
            ],
            "node_name": "Living Room",
            "target_name": "Overhead Lights",
            "action_name": "Set Rule 42"
        },
        {
            "ip": "192.168.1.102",
            "args": [
                "set_rule",
                "device2",
                "12"
            ],
            "node_name": "Living Room",
            "target_name": "Lamp",
            "action_name": "Set Rule 12"
        },
        {
            "ip": "192.168.1.100",
            "args": [
                "disable",
                "device3",
                ""
            ],
            "node_name": "Bathroom",
            "target_name": "Entry Light",
            "action_name": "Disable"
        },
        {
            "ip": "192.168.1.103",
            "args": [
                "set_rule",
                "device3",
                "193"
            ],
            "node_name": "Bedroom",
            "target_name": "Bias lights",
            "action_name": "Set Rule 193"
        }
    ],
    "bright": [
        {
            "ip": "192.168.1.103",
            "args": [
                "set_rule",
                "device1",
                "98"
            ],
            "node_name": "Bedroom",
            "target_name": "Lights",
            "action_name": "Set Rule 98"
        },
        {
            "ip": "192.168.1.100",
            "args": [
                "disable",
                "device1",
                ""
            ],
            "node_name": "Bathroom",
            "target_name": "Bathroom LEDs",
            "action_name": "Disable"
        },
        {
            "ip": "192.168.1.100",
            "args": [
                "enable",
                "device2",
                ""
            ],
            "node_name": "Bathroom",
            "target_name": "Bathroom Lights",
            "action_name": "Enable"
        },
        {
            "ip": "192.168.1.100",
            "args": [
                "enable",
                "device3",
                ""
            ],
            "node_name": "Bathroom",
            "target_name": "Entry Light",
            "action_name": "Enable"
        },
        {
            "ip": "192.168.1.101",
            "args": [
                "disable",
                "device1",
                ""
            ],
            "node_name": "Kitchen",
            "target_name": "Cabinet Lights",
            "action_name": "Disable"
        },
        {
            "ip": "192.168.1.101",
            "args": [
                "enable",
                "device2",
                ""
            ],
            "node_name": "Kitchen",
            "target_name": "Overhead Lights",
            "action_name": "Enable"
        },
        {
            "ip": "192.168.1.102",
            "args": [
                "set_rule",
                "device1",
                "100"
            ],
            "node_name": "Living Room",
            "target_name": "Overhead Lights",
            "action_name": "Set Rule 100"
        },
        {
            "ip": "192.168.1.102",
            "args": [
                "set_rule",
                "device2",
                "100"
            ],
            "node_name": "Living Room",
            "target_name": "Lamp",
            "action_name": "Set Rule 100"
        }
    ]
};
