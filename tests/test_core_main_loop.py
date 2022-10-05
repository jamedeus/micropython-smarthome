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
        "mode": "cool",
        "tolerance": 1,
        "nickname": "sensor1"
    },
    "sensor2": {
        "type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 16,
        "default_rule": 1,
        "schedule": {},
        "nickname": "sensor2"
    },
    "sensor3": {
        "type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 17,
        "default_rule": 1,
        "schedule": {},
        "nickname": "sensor3"
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
        "default_rule": 512,
        "nickname": "device1"
    },
    "device2": {
        "pin": 18,
        "type": "dumb-relay",
        "schedule": {
            "09:00": "on"
        },
        "default_rule": "enabled",
        "nickname": "device2"
    }
}



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
        conditions = self.config.groups[0].check_sensor_conditions()
        self.assertEqual(conditions, [False, False])

        # Trigger only 1 sensor
        for i in self.config.sensors:
            if i.sensor_type == "pir":
                i.motion = True
                break

        # Confirm conditions are correct
        conditions = self.config.groups[0].check_sensor_conditions()
        self.assertEqual(conditions, [True, False])

        # Check si7021 condition
        conditions = self.config.groups[1].check_sensor_conditions()
        if self.config.sensors[1].fahrenheit() > 75:
            self.assertTrue(conditions[0])
        elif self.config.sensors[1].fahrenheit() < 73:
            self.assertFalse(conditions[0])
        else:
            self.assertEqual(conditions[0], None)

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
        self.config.groups[0].apply_action(False)
        self.assertFalse(self.config.groups[0].targets[0].state)

        self.config.groups[0].apply_action(True)
        self.assertTrue(self.config.groups[0].targets[0].state)

        self.config.groups[1].apply_action(False)
        self.assertFalse(self.config.groups[1].targets[0].state)

        self.config.groups[1].apply_action(True)
        self.assertTrue(self.config.groups[1].targets[0].state)
