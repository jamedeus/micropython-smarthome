import os
import time
import unittest
import requests
from Webrepl import Webrepl

# Get absolute paths to tests dir, repo root dir
client_tests_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(os.path.dirname(client_tests_dir))

# Read target IP from disk
with open(os.path.join(client_tests_dir, 'CLIENT_TEST_TARGET_IP'), 'r') as file:
    target_ip = file.read()


class TestEndpoint(unittest.TestCase):

    # Test reboot first for predictable initial state (replace schedule rules deleted by last test etc)
    def test_01(self):
        # Re-upload config file (modified by save methods, breaks next test)
        node = Webrepl(target_ip)
        node.put_file(os.path.join(client_tests_dir, 'client_test_config.json'), 'config.json')
        node.close_connection()

        # Reboot test node, wait 30 seconds before running next test
        response = requests.get(f'http://{target_ip}:8123/reboot')
        self.assertEqual(response.json(), "Rebooting")
        time.sleep(30)

    def test_02_status(self):
        response = requests.get(f'http://{target_ip}:8123/status')
        keys = response.json().keys()
        self.assertIn('metadata', keys)
        self.assertIn('sensors', keys)
        self.assertIn('devices', keys)
        self.assertEqual(len(keys), 3)

    def test_03_disable(self):
        response = requests.get(f'http://{target_ip}:8123/disable?device1')
        self.assertEqual(response.json(), {'Disabled': 'device1'})

    def test_04_disable_in(self):
        response = requests.get(f'http://{target_ip}:8123/disable_in?device1/1')
        self.assertEqual(response.json(), {'Disable_in_seconds': 60.0, 'Disabled': 'device1'})

    def test_05_enable(self):
        response = requests.get(f'http://{target_ip}:8123/enable?sensor1')
        self.assertEqual(response.json(), {'Enabled': 'sensor1'})

    def test_06_enable_in(self):
        response = requests.get(f'http://{target_ip}:8123/enable_in?sensor1/1')
        self.assertEqual(response.json(), {'Enabled': 'sensor1', 'Enable_in_seconds': 60.0})

    def test_07_set_rule(self):
        response = requests.get(f'http://{target_ip}:8123/set_rule?sensor1/1')
        self.assertEqual(response.json(), {'sensor1': '1'})

    def test_08_increment_rule(self):
        # Increment by 1, confirm correct rule
        response = requests.get(f'http://{target_ip}:8123/increment_rule?sensor1/1')
        self.assertEqual(response.json(), {'sensor1': 2})

        # Increment beyond max range, confirm rule set to max
        response = requests.get(f'http://{target_ip}:8123/increment_rule?device1/99999')
        self.assertEqual(response.json(), {'device1': 1023})

    def test_09_reset_rule(self):
        response = requests.get(f'http://{target_ip}:8123/reset_rule?sensor1')
        self.assertEqual(response.json(), {'sensor1': 'Reverted to scheduled rule', 'current_rule': 5})

    # TODO failing
    def test_10_reset_all_rules(self):
        response = requests.get(f'http://{target_ip}:8123/reset_all_rules')
        self.assertEqual(
            response.json(),
            {
                "New rules": {
                    "device1": 1023,
                    "sensor2": 72.0,
                    "sensor1": 5.0,
                    "device2": "disabled",
                    "device3": "disabled"
                }
            }
        )

    # TODO failing
    def test_11_get_schedule_rules(self):
        response = requests.get(f'http://{target_ip}:8123/get_schedule_rules?sensor1')
        self.assertEqual(response.json(), {'01:00': 1, '06:00': 5})

    def test_12_add_rule(self):
        # Add a rule at a time where no rule exists
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/04:00/256')
        self.assertEqual(response.json(), {'time': '04:00', 'Rule added': 256})

        # Add a rule at the same time, should refuse to overwrite
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/04:00/512')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 04:00, add 'overwrite' arg to replace"})

        # Add a rule at the same time with the 'overwrite' argument, rule should be replaced
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/04:00/512/overwrite')
        self.assertEqual(response.json(), {'time': '04:00', 'Rule added': 512})

        # Add rule (0) which is equivalent to False in conditional (regression test for bug causing incorrect rejection)
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/02:52/0')
        self.assertEqual(response.json(), {'time': '02:52', 'Rule added': 0})

        # Add a rule with sunrise keyword instead of timestamp
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/sunrise/512')
        self.assertEqual(response.json(), {'time': 'sunrise', 'Rule added': 512})

    def test_13_remove_rule(self):
        # Delete a rule by timestamp
        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1/04:00')
        self.assertEqual(response.json(), {'Deleted': '04:00'})

        # Delete a rule by keyword
        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1/sunrise')
        self.assertEqual(response.json(), {'Deleted': 'sunrise'})

    def test_14_save_rules(self):
        # Send command, verify response
        response = requests.get(f'http://{target_ip}:8123/save_rules')
        self.assertEqual(response.json(), {"Success": "Rules written to disk"})

    def test_15_get_schedule_keywords(self):
        # Get keywords, should contain sunrise and sunset
        response = requests.get(f'http://{target_ip}:8123/get_schedule_keywords')
        self.assertEqual(len(response.json()), 2)
        self.assertIn('sunrise', response.json().keys())
        self.assertIn('sunset', response.json().keys())

    # Not currently supported, unable to parse url param to dict
    #def test_16_add_schedule_keyword(self):
        ## Add keyword, confirm added
        #response = requests.get(f'http://{target_ip}:8123/add_schedule_keyword?sleep/23:00')
        #self.assertEqual(response.json(), {"Keyword added": 'sleep', "time": '23:00'})

    #def test_17_remove_schedule_keyword(self):
        ## Remove keyword, confirm removed
        #response = requests.get(f'http://{target_ip}:8123/remove_schedule_keyword?sleep')
        #self.assertEqual(response.json(), {"Keyword removed": 'sleep'})

    def test_18_save_schedule_keywords(self):
        response = requests.get(f'http://{target_ip}:8123/save_schedule_keywords')
        self.assertEqual(response.json(), {"Success": "Keywords written to disk"})

    def test_19_get_attributes(self):
        response = requests.get(f'http://{target_ip}:8123/get_attributes?sensor1')
        keys = response.json().keys()
        self.assertIn('_type', keys)
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
        self.assertEqual(response.json()['_type'], 'pir')
        self.assertEqual(response.json()['default_rule'], 5)
        self.assertEqual(response.json()['name'], 'sensor1')
        self.assertEqual(response.json()['nickname'], 'sensor1')

    def test_20_ir(self):
        response = requests.get(f'http://{target_ip}:8123/ir_key?tv/power')
        self.assertEqual(response.json(), {'tv': 'power'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?ac/OFF')
        self.assertEqual(response.json(), {'ac': 'OFF'})

    def test_21_ir_create_macro(self):
        response = requests.get(f'http://{target_ip}:8123/ir_create_macro?test1')
        self.assertEqual(response.json(), {"Macro created": 'test1'})

        # Attempt to create duplicate, confirm error, confirm not created
        response = requests.get(f'http://{target_ip}:8123/ir_create_macro?test1')
        self.assertEqual(response.json(), {"ERROR": 'Macro named test1 already exists'})

    def test_22_ir_add_macro_action(self):
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/tv/power')
        self.assertEqual(response.json(), {"Macro action added": ['test1', 'tv', 'power']})

        # Add action with all required and optional args
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/tv/power/50/3')
        self.assertEqual(response.json(), {"Macro action added": ['test1', 'tv', 'power', '50', '3']})

        # Confirm error when attempting to add to non-existing macro
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test99/tv/power')
        self.assertEqual(response.json(), {"ERROR": "Macro test99 does not exist, use create_macro to add"})

        # Confirm error when attempting to add action with non-existing target
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/refrigerator/power')
        self.assertEqual(response.json(), {"ERROR": "No codes for refrigerator"})

        # Confirm error when attempting to add to non-existing key
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/tv/fake')
        self.assertEqual(response.json(), {"ERROR": "Target tv has no key fake"})

        # Confirm error when delay arg is not integer
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/tv/power/short')
        self.assertEqual(response.json(), {"ERROR": "Delay arg must be integer (milliseconds)"})

        # Confirm error when repeats arg is not integer
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1/tv/power/50/yes')
        self.assertEqual(response.json(), {"ERROR": "Repeat arg must be integer (number of times to press key)"})

    def test_23_ir_run_macro(self):
        response = requests.get(f'http://{target_ip}:8123/ir_run_macro?test1/tv/power')
        self.assertEqual(response.json(), {"Ran macro": "test1"})

        # Attempt to run non-existing macro, confirm error
        response = requests.get(f'http://{target_ip}:8123/ir_run_macro?test99/tv/power')
        self.assertEqual(response.json(), {"ERROR": "Macro test99 does not exist, use create_macro to add"})

    def test_24_ir_save_macros(self):
        response = requests.get(f'http://{target_ip}:8123/ir_save_macros')
        self.assertEqual(response.json(), {"Success": "Macros written to disk"})

    def test_25_ir_get_existing_macros(self):
        response = requests.get(f'http://{target_ip}:8123/ir_get_existing_macros')
        self.assertEqual(response.json(), {"test1": ["tv power 0 1", "tv power 50 3"]})

    def test_26_ir_delete_macro(self):
        response = requests.get(f'http://{target_ip}:8123/ir_delete_macro?test1')
        self.assertEqual(response.json(), {"Macro deleted": 'test1'})

    def test_27_get_temp(self):
        response = requests.get(f'http://{target_ip}:8123/get_temp')
        self.assertEqual(len(response.json()), 1)
        self.assertIsInstance(response.json()["Temp"], float)

    def test_28_get_humid(self):
        response = requests.get(f'http://{target_ip}:8123/get_humid')
        self.assertEqual(len(response.json()), 1)
        self.assertIsInstance(response.json()["Humidity"], float)

    def test_29_get_climate(self):
        response = requests.get(f'http://{target_ip}:8123/get_climate_data')
        self.assertEqual(len(response.json()), 2)
        self.assertIsInstance(response.json()["humid"], float)
        self.assertIsInstance(response.json()["temp"], float)

    def test_30_clear_log(self):
        response = requests.get(f'http://{target_ip}:8123/clear_log')
        self.assertEqual(response.json(), {'clear_log': 'success'})

    def test_31_condition_met(self):
        response = requests.get(f'http://{target_ip}:8123/condition_met?sensor1')
        self.assertEqual(len(response.json()), 1)
        self.assertIn("Condition", response.json().keys())

    def test_32_trigger_sensor(self):
        response = requests.get(f'http://{target_ip}:8123/trigger_sensor?sensor1')
        self.assertEqual(response.json(), {'Triggered': 'sensor1'})

    def test_33_turn_on(self):
        # Ensure enabled
        requests.get(f'http://{target_ip}:8123/enable?device1')

        response = requests.get(f'http://{target_ip}:8123/turn_on?device1')
        self.assertEqual(response.json(), {'On': 'device1'})

    def test_34_turn_off(self):
        # Ensure enabled
        requests.get(f'http://{target_ip}:8123/enable?device1')

        response = requests.get(f'http://{target_ip}:8123/turn_off?device1')
        self.assertEqual(response.json(), {'Off': 'device1'})

        # Ensure disabled
        requests.get(f'http://{target_ip}:8123/disable?device1')

        response = requests.get(f'http://{target_ip}:8123/turn_off?device1')
        self.assertEqual(response.json(), {'Off': 'device1'})

    # Original bug: Enabling and turning on when both current and scheduled rules == "disabled"
    # resulted in comparison operator between int and string, causing crash.
    # After fix (see efd79c6f) this is handled by overwriting current_rule with default_rule.
    # Issue caused by str default_rule - it correctly falls back to 256, but "256"
    def test_35_enable_regression_test(self):
        # Confirm correct starting conditions
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 'disabled')
        self.assertEqual(response.json()['scheduled_rule'], 'disabled')
        # Enable and turn on to reproduce issue
        response = requests.get(f'http://{target_ip}:8123/enable?device3')
        response = requests.get(f'http://{target_ip}:8123/turn_on?device3')
        # Should not crash, should replace unusable rule with default_rule (256) and fade on
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 256)
        self.assertEqual(response.json()['scheduled_rule'], 'disabled')
        self.assertEqual(response.json()['state'], True)
        self.assertEqual(response.json()['enabled'], True)

    # Original bug: LedStrip fade method made calls to set_rule method for each fade step.
    # Later, set_rule was modified to abort an in-progress fade when it received a brightness
    # rule. This caused fade to abort itself after the first step. Fixed in a29f5383.
    def test_36_regression_fade_on(self):
        # Starting conditions
        requests.get(f'http://{target_ip}:8123/set_rule?device3/500')
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['fading'], False)

        # Start fade
        requests.get(f'http://{target_ip}:8123/set_rule?device3/fade%2F505%2F15')
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['fading']['target'], 505)

        # Wait for fade to complete
        time.sleep(16)
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 505)
        self.assertEqual(response.json()['fading'], False)

    # Confirm that calling set_rule while a fade is in-progress correctly aborts
    def test_37_abort_fade(self):
        # Starting conditions
        requests.get(f'http://{target_ip}:8123/set_rule?device3/500')
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['fading'], False)

        # Start 5 minute fade to 505 brightness, confirm started
        requests.get(f'http://{target_ip}:8123/set_rule?device3/fade%2F505%2F300')
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['fading']['target'], 505)

        # Wait 5 seconds, then change rule - fade should abort, new rule should be used
        time.sleep(5)
        requests.get(f'http://{target_ip}:8123/set_rule?device3/400')
        response = requests.get(f'http://{target_ip}:8123/get_attributes?device3')
        self.assertEqual(response.json()['current_rule'], 400)
        self.assertEqual(response.json()['fading'], False)


class TestEndpointInvalid(unittest.TestCase):

    def test_32_nonexistent_endpoint(self):
        response = requests.get(f'http://{target_ip}:8123/notanendpoint')
        self.assertEqual(response.json(), {'ERROR': 'Invalid command'})

    def test_33_disable_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/disable?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/disable?other')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/disable')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_34_disable_in_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/disable_in?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/disable_in?other/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/disable_in?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/disable_in')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_35_enable_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/enable?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/enable?other')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/enable')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_36_enable_in_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/enable_in?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/enable_in?other/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/enable_in?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/enable_in')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_37_set_rule_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/set_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/set_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/set_rule?device99/5')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/set_rule?device1/9999')
        self.assertEqual(response.json(), {'ERROR': 'Invalid rule'})

    def test_38_increment_rule_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/increment_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/increment_rule?sensor1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/increment_rule?sensor1/NaN')
        self.assertEqual(response.json(), {'ERROR': 'Invalid argument nan'})

        response = requests.get(f'http://{target_ip}:8123/increment_rule?sensor1/string')
        self.assertEqual(response.json(), {'ERROR': 'Invalid argument string'})

        response = requests.get(f'http://{target_ip}:8123/increment_rule?device2/1')
        self.assertEqual(response.json(), {'ERROR': 'Unsupported target, must accept int or float rule'})

    def test_39_reset_rule_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/reset_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/reset_rule?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/reset_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_40_get_schedule_rules_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/get_schedule_rules')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/get_schedule_rules?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/get_schedule_rules?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_41_add_rule_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/99:99')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/08:00')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/99:99/15')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/05:00/256')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/05:00/256/del')
        self.assertEqual(response.json(), {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device99/09:13/256')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device99/99:13/256')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device99/256')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/09:13/9999')
        self.assertEqual(response.json(), {'ERROR': 'Invalid rule'})

        response = requests.get(f'http://{target_ip}:8123/add_schedule_rule?device1/0913/256')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

    def test_42_remove_rule_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/remove_rule')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1/99:99')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?device99/01:00')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1/07:16')
        self.assertEqual(response.json(), {'ERROR': 'No rule exists at that time'})

        response = requests.get(f'http://{target_ip}:8123/remove_rule?device1/0913')
        self.assertEqual(response.json(), {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

    def test_43_get_attributes_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/get_attributes')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/get_attributes?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/get_attributes?notdevice')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_44_ir_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/ir_key')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?foo')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?ac')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?foo/on')
        self.assertEqual(response.json(), {'ERROR': 'No codes found for target "foo"'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?ac/power')
        self.assertEqual(response.json(), {'ERROR': 'Target "ac" has no key "power"'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?tv')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/ir_key?tv/START')
        self.assertEqual(response.json(), {'ERROR': 'Target "tv" has no key "START"'})

    def test_45_ir_add_macro_action_missing_args(self):
        response = requests.get(f'http://{target_ip}:8123/ir_add_macro_action?test1')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

    def test_46_condition_met_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/condition_met')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/condition_met?device1')
        self.assertEqual(response.json(), {'ERROR': 'Must specify sensor'})

        response = requests.get(f'http://{target_ip}:8123/condition_met?sensor99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_47_trigger_sensor_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/trigger_sensor')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/trigger_sensor?device1')
        self.assertEqual(response.json(), {'ERROR': 'Must specify sensor'})

        response = requests.get(f'http://{target_ip}:8123/trigger_sensor?sensor99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

        response = requests.get(f'http://{target_ip}:8123/trigger_sensor?sensor2')
        self.assertEqual(response.json(), {'ERROR': 'Cannot trigger si7021 sensor type'})

    def test_48_turn_on_invalid(self):
        # Ensure disabled
        requests.get(f'http://{target_ip}:8123/disable?device1')

        response = requests.get(f'http://{target_ip}:8123/turn_on?device1')
        self.assertEqual(response.json(), {'ERROR': 'device1 is disabled, please enable before turning on'})

        response = requests.get(f'http://{target_ip}:8123/turn_on')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/turn_on?sensor1')
        self.assertEqual(response.json(), {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = requests.get(f'http://{target_ip}:8123/turn_on?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})

    def test_49_turn_off_invalid(self):
        response = requests.get(f'http://{target_ip}:8123/turn_off')
        self.assertEqual(response.json(), {'ERROR': 'Invalid syntax'})

        response = requests.get(f'http://{target_ip}:8123/turn_off?sensor1')
        self.assertEqual(response.json(), {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = requests.get(f'http://{target_ip}:8123/turn_off?device99')
        self.assertEqual(response.json(), {'ERROR': 'Instance not found, use status to see options'})
