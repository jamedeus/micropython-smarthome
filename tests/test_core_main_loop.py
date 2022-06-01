import unittest
from Config import Config



config_file = {
    "wifi": {
        "ssid": "jamnet",
        "password": "cjZY8PTa4ZQ6S83A"
    },
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0"
    },
    "sensor1": {
        "targets": [
            "device2"
        ],
        "type": "si7021",
        "schedule": {
            "10:00": 74,
            "22:00": 74
        },
        "pin": 15,
        "default_rule": 74,
    },
    "sensor2": {
        "type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 16,
        "default_rule": 1,
        "schedule": {}
    },
    "sensor3": {
        "type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 17,
        "default_rule": 1,
        "schedule": {}
    },
    "device1": {
        "pin": 4,
        "type": "pwm",
        "schedule": {
            "09:00": 734,
            "11:00": 345,
            "20:00": 915
        },
        "min": 0,
        "max": 1023,
        "default_rule": 512
    },
    "device2": {
        "pin": 18,
        "type": "dumb-relay",
        "schedule": {
            "09:00": "on"
        },
        "default_rule": "on"
    }
}



def check_sensor_conditions(group):
    # Store return value from each sensor in group
    conditions = []

    # Check conditions for all enabled sensors
    for sensor in group:
        if sensor.enabled:
            conditions.append(sensor.condition_met())

    return conditions



def determine_correct_action(conditions):
    # Determine action to apply to target devices: True = turn on, False = turn off, None = do nothing
    # Turn on: Requires only 1 sensor to return True
    # Turn off: ALL sensors to return False
    # Nothing: Requires 1 sensor to return None and 0 sensors returning True
    if True in conditions:
        action = True
    elif None in conditions:
        action = None
    else:
        action = False

    return action



def apply_action(group, action):
    # TODO consider re-introducing sensor.state - could then skip iterating devices if all states match action. Can also print "Motion detected" only when first detected
    # Issue: When device rules change, device's state is flipped to allow to take effect - this will not take effect if sensor.state blocks loop. Could change sensor.state?

    for device in group:
        # Do not turn device on/off if already on/off, or if device is disabled
        if device.enabled and not action == device.state:
            # int converts True to 1, False to 0
            success = device.send(int(action))

            # Only change device state if send returned True
            if success:
                device.state = action



class TestMainLoop(unittest.TestCase):
    def __init__(self):
        self.config = Config(config_file)

    def test_check_sensor_state(self):
        # Make sure state is False for all motion sensors
        for i in self.config.sensors:
            if i.sensor_type == "pir":
                i.motion = False

        # Confirm state is correct
        conditions = check_sensor_conditions(self.config.groups["group1"]["triggers"])
        self.assertEqual(conditions, [False, False])

        # Trigger only 1 sensor
        for i in self.config.sensors:
            if i.sensor_type == "pir":
                i.motion = True
                break

        # Confirm conditions are correct
        conditions = check_sensor_conditions(self.config.groups["group1"]["triggers"])
        self.assertEqual(conditions, [True, False])

        # Check si7021 condition
        conditions = check_sensor_conditions(self.config.groups["group2"]["triggers"])
        if self.config.sensors[1].fahrenheit() > 74:
            self.assertFalse(conditions[0])
        else:
            self.assertTrue(conditions[0])

    def test_determine_correct_action(self):
        action = determine_correct_action([True, False, False, False])
        self.assertTrue(action)

        action = determine_correct_action([False, False, True, False])
        self.assertTrue(action)

        action = determine_correct_action([False, False, False, False])
        self.assertFalse(action)

        action = determine_correct_action([True, False, False, None])
        self.assertTrue(action)

        action = determine_correct_action([False, False, False, None])
        self.assertEqual(action, None)

    def test_apply_action(self):
        apply_action(self.config.groups["group1"]["targets"], False)
        for i in self.config.devices:
            if i.device_type == "pwm":
                self.assertFalse(i.state)

        apply_action(self.config.groups["group1"]["targets"], True)
        for i in self.config.devices:
            if i.device_type == "pwm":
                self.assertTrue(i.state)

        apply_action(self.config.groups["group2"]["targets"], False)
        for i in self.config.devices:
            if i.device_type == "dumb-relay":
                self.assertFalse(i.state)

        apply_action(self.config.groups["group2"]["targets"], True)
        for i in self.config.devices:
            if i.device_type == "dumb-relay":
                self.assertTrue(i.state)
