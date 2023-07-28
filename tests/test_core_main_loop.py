import unittest
from unittest.mock import patch
import webrepl
from Api import app
from Config import Config
from main import start_loop


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
        "_type": "si7021",
        "schedule": {
            "10:00": 74,
            "22:00": 74
        },
        "default_rule": 74,
        "mode": "cool",
        "tolerance": 1,
        "nickname": "sensor1"
    },
    "sensor2": {
        "_type": "pir",
        "targets": [
            "device1"
        ],
        "pin": 16,
        "default_rule": 1,
        "schedule": {},
        "nickname": "sensor2"
    },
    "sensor3": {
        "_type": "pir",
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
        "_type": "pwm",
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
        "_type": "dumb-relay",
        "schedule": {
            "09:00": "enabled"
        },
        "default_rule": "enabled",
        "nickname": "device2"
    }
}


class TestMainLoop(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Instantiate Config object, run all setup steps except API calls
        cls.config = Config(config_file, delay_setup=True)
        cls.config.instantiate_peripherals()
        cls.config.build_queue()
        cls.config.build_groups()

    # TODO prevent running on micropython
    def test_01_start_loop(self):
        # Confirm webrepl not started
        self.assertEqual(webrepl.listen_s, None)

        # Mock Config init to return existing Config object
        # Mock asyncio.run to return immediately (instead of infinite loop)
        with patch('main.Config', return_value=self.config), \
             patch('main.asyncio.run'):

            # Run function
            start_loop()

        # Confirm API received correct config, webrepl started
        self.assertEqual(app.config, self.config)
        self.assertIsNotNone(webrepl.listen_s)

    # Original bug: Disabling a device while turned on did not turn off, but did flip state to False
    # This resulted in device staying on even after sensors turned other devices in group off. If
    # device was enabled while sensor conditions not met, it still would not be turned off because
    # state (False) matched correct action (turn off). This meant it was impossible to turn the light
    # off without triggering + reseting sensors (or using API).
    def test_02_regression_correct_state_when_re_enabled(self):
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
    def test_03_regression_turn_off_while_disabled(self):
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
