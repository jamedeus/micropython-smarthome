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
        "floor": "0",
        "schedule_keywords": {}
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
        "device_type": "pwm",
        "schedule": {
            "09:00": 734,
            "11:00": 345,
            "20:00": 915
        },
        "min_bright": 0,
        "max_bright": 1023,
        "default_rule": 512,
        "nickname": "device1"
    },
    "device2": {
        "pin": 18,
        "device_type": "dumb-relay",
        "schedule": {
            "09:00": "enabled"
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

    # Original bug: Disabling a device while turned on did not turn off, but did flip state to False
    # This resulted in device staying on even after sensors turned other devices in group off. If
    # device was enabled while sensor conditions not met, it still would not be turned off because
    # state (False) matched correct action (turn off). This meant it was impossible to turn the light
    # off without triggering + reseting sensors (or using API).
    def test_regression_correct_state_when_re_enabled(self):
        # Get LedStrip instance
        led = self.config.find('device1')

        # Find group containing instance
        for g in self.config.groups:
            if led in g.targets:
                group = g
                break

        # Ensure enabled, simulate turning on
        led.enable()
        group.state = False
        group.apply_action(True)

        # Confirm LED turned on, LED state is correct, group state is correct
        self.assertEqual(led.pwm.duty(), led.current_rule)
        self.assertTrue(led.state)
        self.assertTrue(group.state)

        # Disable, should turn off automatically (before fix would stay on)
        led.disable()
        self.assertFalse(led.enabled)

        # Confirm turned off
        self.assertFalse(led.state)
        self.assertEqual(led.pwm.duty(), 0)

        # Simulate reset_timer expiring while disabled
        group.state = False

        # Re-enable to reproduce issue, before fix device would still be on
        led.enable()

        # Should be turned off
        self.assertFalse(led.state)
        self.assertEqual(led.pwm.duty(), 0)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_regression_turn_off_while_disabled(self):
        # Get relay instance
        relay = self.config.find('device2')

        # Find group containing instance
        for g in self.config.groups:
            if relay in g.targets:
                group = g
                break

        # Disable, simulate user turning on (cannot call send while disabled)
        relay.disable()
        relay.relay.value(1)
        self.assertFalse(relay.enabled)
        self.assertEqual(relay.relay.value(), 1)
        # State is uneffected when manually turned on
        self.assertFalse(relay.state)

        # Simulate triggered sensor turning group on
        group.state = False
        group.apply_action(True)
        # Relay state should change, now matches actual state (possible for loop to turn off)
        self.assertTrue(relay.state)

        # Simulate group turning off after sensor resets
        group.state = True
        group.apply_action(False)

        # Relay should now be turned off
        self.assertFalse(relay.state)
        self.assertEqual(relay.relay.value(), 0)

        # Simulate group turning on again - relay should NOT turn on
        group.apply_action(True)
        self.assertTrue(group.state)

        # Should still be off
        self.assertEqual(relay.relay.value(), 0)

        # State should be True even though device is disabled and off
        self.assertTrue(relay.state)
