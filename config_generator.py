#!/usr/bin/python3

templates = {
    "device" : {
        "Dimmer" : {
            "type": "dimmer",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Bulb" : {
            "type": "bulb",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "Relay" : {
            "type": "relay",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "DumbRelay" : {
            "type": "dumb-relay",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "DesktopTarget" : {
            "type": "desktop",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        },

        "LedStrip" : {
            "type": "pwm",
            "default_rule": "placeholder",
            "min": 0,
            "max": 1023,
            "pin": "placeholder",
            "schedule": {}
        },

        "Mosfet" : {
            "type": "mosfet",
            "default_rule": "placeholder",
            "pin": "placeholder",
            "schedule": {}
        },

        "ApiTarget" : {
            "type": "api-target",
            "ip": "placeholder",
            "default_rule": "placeholder",
            "schedule": {}
        }
    },

    "sensor" : {
        "MotionSensor" : {
            "type": "pir",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "DesktopTrigger" : {
            "type": "desktop",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Thermostat" : {
            "type": "si7021",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Dummy" : {
            "type": "dummy",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        },

        "Switch" : {
            "type": "switch",
            "pin": "placeholder",
            "default_rule": "placeholder",
            "targets": [],
            "schedule": {}
        }
    }
}



def initial_prompt():
    while True:
        print("Which category?")
        print(" [1] Device")
        print(" [2] Sensor")
        choice = input()
        print()

        if choice == "1":
            return "device"
        elif choice == "2":
            return "sensor"

        else:
            print("\nERROR: Please enter a number and press enter.\n")



def select_type(category):
    options = enumerate(templates[category], 1)
    choices = enumerate(templates[category], 1)

    while True:
        print(f"Select {category} type")
        for counter, option in options:
            print(f" [{counter}] {option}")

        choice = input()
        print()

        try:
            if int(choice) in range(1, len(templates[category]) + 1):
                for i in choices:
                    if int(choice) == i[0]:
                        return i[1]

            else:
                raise ValueError

        except ValueError:
            print("\nERROR: Please enter a number and press enter.\n")



def configure(category, module):
    config = templates[category][module]

    for i in config:
        if config[i] == "placeholder":
            print(f"{i} = ", end='')
            config[i] = input()
            print()

    while True:
        print("Would you like to add schedule rules?")
        print(" [1] Yes")
        print(" [2] No")
        choice = input()
        print()

        if choice == "1":
            break
        elif choice == "2":
            return config
        else:
            print("\nERROR: Please enter a number and press enter.\n")

    import re

    while True:
        print("Rule time (HH:MM): ", end='')
        timestamp = input()

        if re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", timestamp):
            print("Enter rule: ", end='')
            rule = input()
            config["schedule"][timestamp] = rule
        else:
            print("\nInvalid timestamp format - must be HH:MM, no am/pm\n")
            continue

        while True:
            print("\nAdd another rule?")
            print(" [1] Yes")
            print(" [2] No")
            choice = input()
            print()

            if choice == "1":
                break
            elif choice == "2":
                return config
            else:
                print("\nERROR: Please enter a number and press enter.\n")

        continue



category = initial_prompt()
module = select_type(category)
config = configure(category, module)

import json
print(json.dumps(config, indent=4))
