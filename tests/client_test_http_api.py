import unittest
import requests
import time



class TestEndpoint(unittest.TestCase):

    # Test reboot first for predictable initial state (replace schedule rules deleted by last test etc)
    def test_1(self):
        response = requests.get('http://192.168.1.223:8123/reboot')
        self.assertEqual(response.json(), "Rebooting")

        # Wait for node to finish booting before running next test
        time.sleep(20)

    def test_status(self):
        response = requests.get('http://192.168.1.223:8123/status')
        keys = response.json().keys()
        self.assertIn('metadata', keys)
        self.assertIn('sensors', keys)
        self.assertIn('devices', keys)
        self.assertEqual(len(keys), 3)

    def test_disable(self):
        response = requests.get('http://192.168.1.223:8123/disable?device1')
        self.assertEqual(response.json(), {'Disabled': 'device1'})

    def test_disable_in(self):
        response = requests.get('http://192.168.1.223:8123/disable_in?device1/1')
        self.assertEqual(response.json(), {'Disable_in_seconds': 60.0, 'Disabled': 'device1'})

    def test_enable(self):
        response = requests.get('http://192.168.1.223:8123/enable?sensor1')
        self.assertEqual(response.json(), {'Enabled': 'sensor1'})

    def test_enable_in(self):
        response = requests.get('http://192.168.1.223:8123/enable_in?sensor1/1')
        self.assertEqual(response.json(), {'Enabled': 'sensor1', 'Enable_in_seconds': 60.0})

    def test_set_rule(self):
        response = requests.get('http://192.168.1.223:8123/set_rule?sensor1/1')
        self.assertEqual(response.json(), {'sensor1': '1'})

    def test_reset_rule(self):
        response = requests.get('http://192.168.1.223:8123/reset_rule?sensor1')
        self.assertEqual(response.json()["sensor1"], 'Reverted to scheduled rule')

    def test_reset_all_rules(self):
        response = requests.get('http://192.168.1.223:8123/reset_all_rules')
        self.assertEqual(response.json(), {"New rules": {"device1": 1023, "sensor2": 72.0, "sensor1": 5.0, "device2": "off", "device3": "disabled"}})

    def test_get_schedule_rules(self):
        response = requests.get('http://192.168.1.223:8123/get_schedule_rules?sensor1')
        self.assertEqual(response.json(), {'01:00': '1', '06:00': '5'})

    def test_add_rule(self):
        # Add a rule at a time where no rule exists
        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/04:00/256')
        self.assertEqual(response.json(), {'time': '04:00', 'Rule added': 256})

        # Add another rule at the same time, should refuse to overwrite
        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/04:00/512')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 04:00, add 'overwrite' arg to replace"})

        # Add another rule at the same time with the 'overwrite' argument, rule should be replaced
        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/04:00/512/overwrite')
        self.assertEqual(response.json(), {'time': '04:00', 'Rule added': 512})

    def test_remove_rule(self):
        response = requests.get('http://192.168.1.223:8123/remove_rule?device1/01:00')
        self.assertEqual(response.json(), {'Deleted': '01:00'})

    def test_get_attributes(self):
        response = requests.get('http://192.168.1.223:8123/get_attributes?sensor1')
        keys = response.json().keys()
        self.assertIn('sensor_type', keys)
        self.assertIn('rule_queue', keys)
        self.assertIn('enabled', keys)
        self.assertIn('targets', keys)
        self.assertIn('name', keys)
        self.assertIn('scheduled_rule', keys)
        self.assertIn('current_rule', keys)
        self.assertIn('default_rule', keys)
        self.assertIn('motion', keys)
        self.assertIn('nickname', keys)
        self.assertIn('group', keys)
        self.assertEqual(len(keys), 11)
        self.assertEqual(response.json()['sensor_type'], 'pir')
        self.assertEqual(response.json()['default_rule'], 5)
        self.assertEqual(response.json()['name'], 'sensor1')
        self.assertEqual(response.json()['nickname'], 'sensor1')

    def test_ir(self):
        response = requests.get('http://192.168.1.223:8123/ir_key?tv/power')
        self.assertEqual(response.json(), {'tv': 'power'})

        response = requests.get('http://192.168.1.223:8123/ir_key?ac/OFF')
        self.assertEqual(response.json(), {'ac': 'OFF'})

        response = requests.get('http://192.168.1.223:8123/backlight?on')
        self.assertEqual(response.json(), {'backlight': 'on'})

    def test_get_temp(self):
        response = requests.get('http://192.168.1.223:8123/get_temp')
        self.assertEqual(len(response.json()), 1)
        self.assertIsInstance(response.json()["Temp"], float)

    def test_get_humid(self):
        response = requests.get('http://192.168.1.223:8123/get_humid')
        self.assertEqual(len(response.json()), 1)
        self.assertIsInstance(response.json()["Humidity"], float)

    def test_get_climate(self):
        response = requests.get('http://192.168.1.223:8123/get_climate_data')
        self.assertEqual(len(response.json()), 2)
        self.assertIsInstance(response.json()["humid"], float)
        self.assertIsInstance(response.json()["temp"], float)

    def test_clear_log(self):
        response = requests.get('http://192.168.1.223:8123/clear_log')
        self.assertEqual(response.json(), {'clear_log': 'success'})

    def test_condition_met(self):
        response = requests.get('http://192.168.1.223:8123/condition_met?sensor1')
        self.assertEqual(len(response.json()), 1)
        self.assertIn("Condition", response.json().keys())

    def test_trigger_sensor(self):
        response = requests.get('http://192.168.1.223:8123/trigger_sensor?sensor1')
        self.assertEqual(response.json(), {'Triggered': 'sensor1'})

    def test_turn_on(self):
        # Ensure enabled
        requests.get('http://192.168.1.223:8123/enable?device1')

        response = requests.get('http://192.168.1.223:8123/turn_on?device1')
        self.assertEqual(response.json(), {'On': 'device1'})

    def test_turn_off(self):
        # Ensure enabled
        requests.get('http://192.168.1.223:8123/enable?device1')

        response = requests.get('http://192.168.1.223:8123/turn_off?device1')
        self.assertEqual(response.json(), {'Off': 'device1'})

    # Original bug: Enabling and turning on when both current and scheduled rules == "disabled"
    # resulted in comparison operator between int and string, causing crash.
    # After fix (see efd79c6f) this is handled by overwriting current_rule with default_rule.
    def test_enable_regression_test(self):
        # Confirm correct starting conditions
        response = requests.get('http://192.168.1.223:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 'disabled')
        self.assertEqual(response.json()['scheduled_rule'], 'disabled')
        # Enable and turn on to reproduce issue
        response = requests.get('http://192.168.1.223:8123/enable?device3')
        response = requests.get('http://192.168.1.223:8123/turn_on?device3')
        # Should not crash, should replace unusable rule with default_rule (256) and fade on
        response = requests.get('http://192.168.1.223:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 256)
        self.assertEqual(response.json()['scheduled_rule'], 'disabled')
        self.assertEqual(response.json()['state'], True)
        self.assertEqual(response.json()['enabled'], True)



class TestEndpointInvalid(unittest.TestCase):

    def test_nonexistent_endpoint(self):
        response = requests.get('http://192.168.1.223:8123/notanendpoint')
        self.assertEqual(response.json(), {'ERROR': 'Invalid command'})

    def test_disable_invalid(self):
        response = requests.get('http://192.168.1.223:8123/disable?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/disable?other')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/disable')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_disable_in_invalid(self):
        response = requests.get('http://192.168.1.223:8123/disable_in?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/disable_in?other/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/disable_in?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/disable_in')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_enable_invalid(self):
        response = requests.get('http://192.168.1.223:8123/enable?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/enable?other')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/enable')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_enable_in_invalid(self):
        response = requests.get('http://192.168.1.223:8123/enable_in?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/enable_in?other/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/enable_in?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/enable_in')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_set_rule_invalid(self):
        response = requests.get('http://192.168.1.223:8123/set_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/set_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/set_rule?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/set_rule?device1/9999')
        self.assertEqual(response.json(), {'ERROR': 'Invalid rule'})

    def test_reset_rule_invalid(self):
        response = requests.get('http://192.168.1.223:8123/reset_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/reset_rule?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/reset_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_get_schedule_rules_invalid(self):
        response = requests.get('http://192.168.1.223:8123/get_schedule_rules')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/get_schedule_rules?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/get_schedule_rules?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_add_rule_invalid(self):
        response = requests.get('http://192.168.1.223:8123/add_schedule_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/99:99')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/08:00')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/99:99/15')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM)'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/05:00/256')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/05:00/256/del')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device99/09:13/256')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device99/99:13/256')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device99/256')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/09:13/9999')
        self.assertEqual(response.json(), {'ERROR': 'Invalid rule'})

        response = requests.get('http://192.168.1.223:8123/add_schedule_rule?device1/0913/256')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM)'})

    def test_remove_rule_invalid(self):
        response = requests.get('http://192.168.1.223:8123/remove_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?device1/99:99')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM)'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?device99/01:00')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?device1/07:16')
        self.assertEqual(response.json(), {'ERROR': 'No rule exists at that time'})

        response = requests.get('http://192.168.1.223:8123/remove_rule?device1/0913')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM)'})

    def test_get_attributes_invalid(self):
        response = requests.get('http://192.168.1.223:8123/get_attributes')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/get_attributes?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/get_attributes?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_ir_invalid(self):
        response = requests.get('http://192.168.1.223:8123/ir_key')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/ir_key?foo')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/ir_key?ac')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/ir_key?ac/power')
        self.assertEqual(response.json(), {'ERROR': 'Target "ac" has no key power'})

        response = requests.get('http://192.168.1.223:8123/ir_key?tv')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/ir_key?tv/START')
        self.assertEqual(response.json(), {'ERROR': 'Target "tv" has no key START'})

        response = requests.get('http://192.168.1.223:8123/backlight')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/backlight?start')
        self.assertEqual(response.json(), {'ERROR': 'Backlight setting must be "on" or "off"'})

    def test_condition_met_invalid(self):
        response = requests.get('http://192.168.1.223:8123/condition_met')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/condition_met?device1')
        self.assertEqual(response.json(), {'ERROR': 'Must specify sensor'})

        response = requests.get('http://192.168.1.223:8123/condition_met?sensor99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_trigger_sensor_invalid(self):
        response = requests.get('http://192.168.1.223:8123/trigger_sensor')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/trigger_sensor?device1')
        self.assertEqual(response.json(), {'ERROR': 'Must specify sensor'})

        response = requests.get('http://192.168.1.223:8123/trigger_sensor?sensor99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get('http://192.168.1.223:8123/trigger_sensor?sensor2')
        self.assertEqual(response.json(), {'ERROR': 'Cannot trigger si7021 sensor type'})

    def test_turn_on_invalid(self):
        # Ensure disabled
        requests.get('http://192.168.1.223:8123/disable?device1')

        response = requests.get('http://192.168.1.223:8123/turn_on?device1')
        self.assertEqual(response.json(), {'ERROR': 'Unable to turn on device1'})

        response = requests.get('http://192.168.1.223:8123/turn_on')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/turn_on?sensor1')
        self.assertEqual(response.json(), {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = requests.get('http://192.168.1.223:8123/turn_on?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_turn_off_invalid(self):
        # Ensure disabled
        requests.get('http://192.168.1.223:8123/disable?device1')

        response = requests.get('http://192.168.1.223:8123/turn_off?device1')
        self.assertEqual(response.json(), {'ERROR': 'Unable to turn off device1'})

        response = requests.get('http://192.168.1.223:8123/turn_off')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get('http://192.168.1.223:8123/turn_off?sensor1')
        self.assertEqual(response.json(), {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = requests.get('http://192.168.1.223:8123/turn_off?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})
