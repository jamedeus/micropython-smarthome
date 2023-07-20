import os
import json
import network
import unittest
import uasyncio as asyncio
import SoftwareTimer
from Config import Config
from Api import app

# Get IP address
ip = network.WLAN(network.STA_IF).ifconfig()[0]


config_file = {
    "wifi": {
        "ssid": "jamnet",
        "password": "cjZY8PTa4ZQ6S83A"
    },
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0",
        "schedule_keywords": {
            'sunrise': '06:00',
            'sunset': '18:00'
        }
    },
    "sensor1": {
        "targets": [
            "device1"
        ],
        "_type": "si7021",
        "schedule": {
            "10:00": 74,
            "22:00": 74
        },
        "default_rule": 70,
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
        "_type": "switch",
        "nickname": "Test",
        "pin": "18",
        "default_rule": "enabled",
        "targets": [],
        "schedule": {}
    },
    "sensor4": {
        "_type": "desktop",
        "nickname": "test",
        "ip": "192.168.1.216",
        "default_rule": "enabled",
        "targets": [],
        "schedule": {}
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
    "ir_blaster": {
        "pin": 32,
        "target": "tv"
    }
}

# Instantiate config object, pass to API
config = Config(config_file)
app.config = config


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.device1 = config.find("device1")
        cls.sensor1 = config.find("sensor1")
        cls.sensor2 = config.find("sensor2")
        cls.sensor3 = config.find("sensor3")
        cls.sensor4 = config.find("sensor4")

    async def request(self, msg):
        reader, writer = await asyncio.open_connection(ip, 8123)
        try:
            writer.write('{}\n'.format(json.dumps(msg)).encode())
            await writer.drain()
            res = await reader.read(1200)
        except OSError:
            pass
        try:
            response = json.loads(res)
        except ValueError:
            return "Error: Unable to decode response"
        writer.close()
        await writer.wait_closed()

        return response

    def send_command(self, cmd):
        return asyncio.run(self.request(cmd))

    def test_01_status(self):
        response = self.send_command(['status'])
        self.assertIsInstance(response, dict)

    def test_02_enable(self):
        # Disable target device (might succeed incorrectly if it's already enabled)
        self.device1.disable()
        # Enable with API command
        response = self.send_command(['enable', 'device1'])
        self.assertTrue(self.device1.enabled)
        self.assertEqual(response, {'Enabled': 'device1'})

    def test_03_disable(self):
        # Enable target device (might succeed incorrectly if it's already disabled)
        self.device1.enable()
        # Disable with API command
        response = self.send_command(['disable', 'device1'])
        self.assertFalse(self.device1.enabled)
        self.assertEqual(response, {'Disabled': 'device1'})

    def test_04_enable_in(self):
        # Cancel all SoftwareTimers created by API
        SoftwareTimer.timer.cancel("API")
        # Disable target device (might succeed incorrectly if it's already enabled)
        self.device1.disable()
        # Send API command to enable in 5 minutes
        response = self.send_command(['enable_in', 'device1', '5'])
        self.assertEqual(response, {'Enabled': 'device1', 'Enable_in_seconds': 300.0})
        # SoftwareTimer queue should now contain entry set by "API"
        self.assertIn("API", str(SoftwareTimer.timer.schedule))
        # Device should still be disabled since timer hasn't expired yet
        self.assertFalse(self.device1.enabled)

    def test_05_disable_in(self):
        # Cancel all SoftwareTimers created by API
        SoftwareTimer.timer.cancel("API")
        # Enable target device (might succeed incorrectly if it's already disabled)
        self.device1.enable()
        # Send API command to disable in 5 minutes
        response = self.send_command(['disable_in', 'device1', '5'])
        self.assertEqual(response, {'Disable_in_seconds': 300.0, 'Disabled': 'device1'})
        # SoftwareTimer queue should now contain entry set by "API"
        self.assertIn("API", str(SoftwareTimer.timer.schedule))
        # Device should still be enabled since timer hasn't expired yet
        self.assertTrue(self.device1.enabled)

    def test_06_set_rule(self):
        # Set to valid rule 5
        response = self.send_command(['set_rule', 'sensor2', '5'])
        self.assertEqual(self.sensor2.current_rule, 5.0)
        self.assertEqual(response, {'sensor2': '5'})

        # Attempt to set invalid rule True
        response = self.send_command(['set_rule', 'sensor2', 'True'])
        self.assertEqual(self.sensor2.current_rule, 5.0)
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

        # Set url-encoded fade rule
        response = self.send_command(['set_rule', 'device1', 'fade%2F50%2F3600'])
        self.assertEqual(self.sensor2.current_rule, 5.0)
        self.assertEqual(response, {'device1': 'fade/50/3600'})
        # Cancel timer to prevent actually fading
        SoftwareTimer.timer.cancel('device1_fade')

    def test_07_increment_rule(self):
        # Set known starting values
        self.device1.current_rule = 512
        self.sensor1.current_rule = 70

        # Increment PWM by both positive and negative numbers
        response = self.send_command(['increment_rule', 'device1', '-12'])
        self.assertEqual(response, {'device1': 500})
        self.assertEqual(self.device1.current_rule, 500)
        response = self.send_command(['increment_rule', 'device1', '50'])
        self.assertEqual(response, {'device1': 550})
        self.assertEqual(self.device1.current_rule, 550)

        # Increment SI7021 by both float and integer
        response = self.send_command(['increment_rule', 'sensor1', '0.5'])
        self.assertEqual(response, {'sensor1': 70.5})
        self.assertEqual(self.sensor1.current_rule, 70.5)
        response = self.send_command(['increment_rule', 'sensor1', '3'])
        self.assertEqual(response, {'sensor1': 73.5})
        self.assertEqual(self.sensor1.current_rule, 73.5)

        # Attempt to increment rule of an instance that does not support int/float rules
        response = self.send_command(['increment_rule', 'sensor3', '1'])
        self.assertEqual(response, {'ERROR': 'Unsupported target, must accept int or float rule'})

        # Attempt to increment to an invalid rule
        response = self.send_command(['increment_rule', 'sensor1', '100'])
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

    def test_08_reset_rule(self):
        # Set placeholder rule
        self.device1.set_rule(1)
        # Call reset API command
        response = self.send_command(['reset_rule', 'device1'])
        self.assertEqual(
            response,
            {
                'device1': 'Reverted to scheduled rule',
                'current_rule': self.device1.scheduled_rule
            }
        )
        self.assertEqual(self.device1.current_rule, self.device1.scheduled_rule)

    def test_09_reset_all_rules(self):
        # Set placeholder rules
        self.device1.set_rule(78)
        self.sensor1.set_rule(78)
        self.sensor2.set_rule(78)
        # Call API command
        response = self.send_command(['reset_all_rules'])
        self.assertEqual(
            response,
            {
                "New rules": {
                    "device1": self.device1.scheduled_rule,
                    "sensor1": self.sensor1.scheduled_rule,
                    "sensor2": self.sensor2.scheduled_rule,
                    "sensor3": self.sensor3.scheduled_rule,
                    "sensor4": self.sensor4.scheduled_rule
                }
            }
        )
        self.assertEqual(self.device1.current_rule, self.device1.scheduled_rule)
        self.assertEqual(self.sensor1.current_rule, self.sensor1.scheduled_rule)
        self.assertEqual(self.sensor2.current_rule, self.sensor2.scheduled_rule)

    def test_10_get_schedule_rules(self):
        response = self.send_command(['get_schedule_rules', 'device1'])
        self.assertEqual(response, {'20:00': 915, '09:00': 734, '11:00': 345})

    def test_11_add_schedule_rule(self):
        # Add a rule at a time where no rule exists
        response = self.send_command(['add_schedule_rule', 'device1', '05:37', '64'])
        self.assertEqual(response, {'time': '05:37', 'Rule added': 64})

        # Add another rule at the same time, should refuse to overwrite
        response = self.send_command(['add_schedule_rule', 'device1', '05:37', '42'])
        self.assertEqual(response, {'ERROR': "Rule already exists at 05:37, add 'overwrite' arg to replace"})

        # Add another rule at the same time with the 'overwrite' argument, rule should be replaced
        response = self.send_command(['add_schedule_rule', 'device1', '05:37', '42', 'overwrite'])
        self.assertEqual(response, {'time': '05:37', 'Rule added': 42})

        # Add a rule using a schedule keyword instead of timestamp
        response = self.send_command(['add_schedule_rule', 'device1', 'sunrise', '42'])
        self.assertEqual(response, {'time': 'sunrise', 'Rule added': 42})

        # Confirm correct error received when timestamp format is incorrect
        response = self.send_command(['add_schedule_rule', 'device1', '1234', '99'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"})

        # Confirm correct error received when timestamp exceeds 24 hours
        response = self.send_command(['add_schedule_rule', 'device1', '42:99', '99'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"})

        # Confirm correct error received when timestamp is H:MM format
        response = self.send_command(['add_schedule_rule', 'device1', '8:22', '42'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"})

        # Confirm correct error received when rule rejected by validator
        response = self.send_command(['add_schedule_rule', 'device1', '15:57', '9999'])
        self.assertEqual(response, {"ERROR": "Invalid rule"})

    def test_12_remove_rule(self):
        # Get starting rules
        before = self.send_command(['get_schedule_rules', 'device1'])
        del before["20:00"]
        # Delete same rule
        response = self.send_command(['remove_rule', 'device1', '20:00'])
        self.assertEqual(response, {'Deleted': '20:00'})
        # Get ending rules
        after = self.send_command(['get_schedule_rules', 'device1'])
        # Should now be the same
        self.assertEqual(before, after)

        # Delete a schedule keyword rule
        response = self.send_command(['remove_rule', 'device1', 'sunrise'])
        self.assertEqual(response, {'Deleted': 'sunrise'})

        # Confirm correct error received when deleting a rule that doesn't exist
        response = self.send_command(['remove_rule', 'device1', '20:00'])
        self.assertEqual(response, {'ERROR': 'No rule exists at that time'})

        # Confirm correct error received when timestamp exceeds 24 hours
        response = self.send_command(['remove_rule', 'device1', '42:99'])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM) or schedule keyword"})

    # Note: will fail if config.json missing or contains fewer devices/sensors than test config
    def test_13_save_schedule_rules(self):
        # Save rules, confirm response
        response = self.send_command(['save_rules'])
        self.assertEqual(response, {"Success": "Rules written to disk"})

    def test_14_get_schedule_keywords(self):
        # Get keywords, should contain sunrise and sunset
        response = self.send_command(['get_schedule_keywords'])
        self.assertEqual(len(response), 2)
        self.assertIn('sunrise', response.keys())
        self.assertIn('sunset', response.keys())

    def test_15_add_schedule_keyword(self):
        # Add keyword, confirm added
        response = self.send_command(['add_schedule_keyword', {'sleep': '23:00'}])
        self.assertEqual(response, {"Keyword added": 'sleep', "time": '23:00'})

        # Add keyword with invalid timestamp, confirm error
        response = self.send_command(['add_schedule_keyword', {'invalid': '3:00'}])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

    def test_16_remove_schedule_keyword(self):
        # Add schedule rule using keyword, should be deleted when keyword deleted
        app.config.schedule['device1']['sleep'] = 512

        # Remove keyword, confirm removed, confirm rule using keyword removed
        response = self.send_command(['remove_schedule_keyword', 'sleep'])
        self.assertEqual(response, {"Keyword removed": 'sleep'})
        self.assertTrue('sleep' not in app.config.schedule['device1'].keys())

        # Confirm correct error when attempting to delete sunrise/sunset
        response = self.send_command(['remove_schedule_keyword', 'sunrise'])
        self.assertEqual(response, {"ERROR": "Cannot delete sunrise or sunset"})

        # Confirm correct error when attempting to non-existing keyword
        response = self.send_command(['remove_schedule_keyword', 'fake'])
        self.assertEqual(response, {"ERROR": "Keyword does not exist"})

    def test_17_save_schedule_keywords(self):
        response = self.send_command(['save_schedule_keywords'])
        self.assertEqual(response, {"Success": "Keywords written to disk"})

    def test_18_get_attributes(self):
        response = self.send_command(['get_attributes', 'sensor1'])
        self.assertIsInstance(response, dict)
        self.assertEqual(response["_type"], "si7021")
        self.assertEqual(response["targets"], ['device1'])

    def test_19_trigger_sensor_condition_met(self):
        # Initial state should be False
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': False})
        # Trigger sensor
        response = self.send_command(['trigger_sensor', 'sensor2'])
        self.assertEqual(response, {'Triggered': 'sensor2'})
        # State should now be True
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': True})

    def test_20_trigger_sensor_invalid(self):
        # Thermostat not compatible with endpoint
        response = self.send_command(['trigger_sensor', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Cannot trigger si7021 sensor type"})

        # Should return error if argument is not a sensor
        response = self.send_command(['trigger_sensor', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

    def test_21_condition_met_invalid(self):
        # Should return error if argument is not a sensor
        response = self.send_command(['condition_met', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

    def test_22_turn_on(self):
        # Make sure device is enabled and turned off before testing
        self.device1.enable()
        self.device1.send(0)
        # Send command to turn on
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'On': 'device1'})
        # PWM duty cycle should now be same as current rule
        self.assertEqual(self.device1.pwm.duty(), self.device1.current_rule)

        # Should only accept devices, not sensors
        response = self.send_command(['turn_on', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

        # Should not be able to turn on a disabled device
        self.device1.disable()
        self.device1.send(0)
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'ERROR': 'device1 is disabled, please enable before turning on'})

        # Device should still be off
        self.assertFalse(self.device1.state)
        self.assertEqual(self.device1.pwm.duty(), 0)

    def test_23_turn_off(self):
        # Make sure device is enabled and turned on before testing
        self.device1.enable()
        self.device1.send(1)
        # Send command to turn on
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})
        # PWM duty cycle should now be 0
        self.assertEqual(self.device1.pwm.duty(), 0)

        # Should only accept devices, not sensors
        response = self.send_command(['turn_off', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

        # Should be able to turn off a disabled device (just not on)
        response = self.send_command(['disable', 'device1'])
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})

        # Device should now be off
        self.assertFalse(self.device1.state)
        self.assertEqual(self.device1.pwm.duty(), 0)

    def test_24_get_temp(self):
        response = self.send_command(['get_temp'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Temp"], float)

    def test_25_get_humid(self):
        response = self.send_command(['get_humid'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Humidity"], float)

    def test_26_get_climate_data(self):
        response = self.send_command(['get_climate_data'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["humid"], float)
        self.assertIsInstance(response["temp"], float)

    def test_27_clear_log(self):
        response = self.send_command(['clear_log'])
        self.assertEqual(response, {'clear_log': 'success'})

        # Confirm correct error if log doesn't exist
        try:
            os.remove('app.log')
        except FileNotFoundError:
            pass
        response = self.send_command(['clear_log'])
        self.assertEqual(response, {'ERROR': 'no log file found'})

    def test_28_ir_key(self):
        response = self.send_command(['ir_key', 'tv', 'power'])
        self.assertEqual(response, {'tv': 'power'})

        # Confirm correct error message
        response = self.send_command(['ir_key', 'tv', 'on'])
        self.assertEqual(response, {'ERROR': 'Target "tv" has no key "on"'})

        # Confirm correct error message
        response = self.send_command(['ir_key', 'ac', 'on'])
        self.assertEqual(response, {'ERROR': 'No codes found for target "ac"'})

    def test_29_backlight(self):
        response = self.send_command(['backlight', 'off'])
        self.assertEqual(response, {'backlight': 'off'})

        # Confirm correct error message
        response = self.send_command(['backlight', 'low'])
        self.assertEqual(response, {'ERROR': 'Backlight setting must be "on" or "off"'})

    def test_30_invalid_command(self):
        response = self.send_command(['notacommand'])
        self.assertEqual(response, {"ERROR": "Invalid command"})

    def test_31_missing_arguments(self):
        response = self.send_command(['enable'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['disable'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['enable_in'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['enable_in', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['disable_in'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['disable_in', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['set_rule'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['set_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['increment_rule'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['increment_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['reset_rule'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['get_schedule_rules'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['add_schedule_rule'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['add_schedule_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['add_schedule_rule', 'device1', '01:23'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['remove_rule'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['remove_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['add_schedule_keyword'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['add_schedule_keyword', 'start'])
        self.assertEqual(response, {"ERROR": "Requires dict with keyword and timestamp"})

        response = self.send_command(['remove_schedule_keyword'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['get_attributes'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['condition_met'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['trigger_sensor'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['turn_on'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['turn_off'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_key'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_key', 'tv'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['backlight'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

    def test_32_invalid_instance(self):
        response = self.send_command(['enable', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['disable', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['enable_in', 'device99', '5'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['disable_in', 'device99', '5'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['set_rule', 'device99', '100'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['increment_rule', 'device99', '1'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['reset_rule', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['get_schedule_rules', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['add_schedule_rule', 'device99', '12:34', '100'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['remove_rule', 'device99', '12:34'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['get_attributes', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['condition_met', 'sensor99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['trigger_sensor', 'sensor99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['turn_on', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['turn_off', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

    # Original bug: Some device and sensor classes have attributes containing class objects, which
    # cannot be json-serialized. These are supposed to be deleted or replaced with string
    # representations when building get_attributes response. Earlier versions of API failed to do
    # this for some classes, breaking get_attributes and resulting in an "unable to decode" error.
    def test_33_regression_get_attributes(self):
        response = self.send_command(['get_attributes', 'sensor3'])
        self.assertEqual(
            response,
            {
                '_type': 'switch',
                'nickname': 'Test',
                'enabled': True,
                'targets': [],
                'group': 'group2',
                'name': 'sensor3',
                'rule_queue': [],
                'default_rule': 'enabled',
                'scheduled_rule': 'enabled',
                'current_rule': 'enabled'
            }
        )

        response = self.send_command(['get_attributes', 'sensor4'])
        # Prevent false positive if real-world monitor state differs (not important for test)
        response['current'] = 'On'
        self.assertEqual(
            response,
            {
                'ip': '192.168.1.216',
                'port': 5000,
                'nickname': 'test',
                'scheduled_rule': 'enabled',
                'group': 'group2',
                'current': 'On',
                'name': 'sensor4',
                'enabled': True,
                'rule_queue': [],
                'default_rule': 'enabled',
                'targets': [],
                'current_rule': 'enabled',
                'desktop_target': None,
                '_type': 'desktop'
            }
        )
