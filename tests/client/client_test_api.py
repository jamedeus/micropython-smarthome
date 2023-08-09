import os
import time
import asyncio
import unittest
from Webrepl import Webrepl
from api_endpoints import request

# Get absolute paths to tests dir, repo root dir
client_tests_dir = os.path.dirname(os.path.realpath(__file__))
repo_dir = os.path.dirname(os.path.dirname(client_tests_dir))

# Read target IP from disk
with open(os.path.join(client_tests_dir, 'CLIENT_TEST_TARGET_IP'), 'r') as file:
    target_ip = file.read()


class TestParseCommand(unittest.TestCase):

    # Test reboot first for predictable initial state (replace schedule rules deleted by last test etc)
    def test_01(self):
        # Re-upload config file (modified by save methods, breaks next test)
        node = Webrepl(target_ip)
        node.put_file(os.path.join(client_tests_dir, 'client_test_config.json'), 'config.json')
        node.close_connection()

        response = asyncio.run(request(target_ip, ['reboot']))
        self.assertEqual(response, "Rebooting")

        # Wait for node to finish booting before running next test
        time.sleep(30)

    def test_02_status(self):
        response = asyncio.run(request(target_ip, ['status']))
        keys = response.keys()
        self.assertIn('metadata', keys)
        self.assertIn('sensors', keys)
        self.assertIn('devices', keys)
        self.assertEqual(len(response.keys()), 3)

    def test_03_disable(self):
        response = asyncio.run(request(target_ip, ['disable', 'device1']))
        self.assertEqual(response, {'Disabled': 'device1'})

    def test_04_disable_in(self):
        response = asyncio.run(request(target_ip, ['disable_in', 'device1', '1']))
        self.assertEqual(response, {'Disable_in_seconds': 60.0, 'Disabled': 'device1'})

    def test_05_enable(self):
        response = asyncio.run(request(target_ip, ['enable', 'sensor1']))
        self.assertEqual(response, {'Enabled': 'sensor1'})

    def test_06_enable_in(self):
        response = asyncio.run(request(target_ip, ['enable_in', 'sensor1', '1']))
        self.assertEqual(response, {'Enabled': 'sensor1', 'Enable_in_seconds': 60.0})

    def test_07_set_rule(self):
        response = asyncio.run(request(target_ip, ['set_rule', 'sensor1', '1']))
        self.assertEqual(response, {'sensor1': '1'})

    def test_08_increment_rule(self):
        # Increment by 1, confirm correct rule
        response = asyncio.run(request(target_ip, ['increment_rule', 'sensor1', '1']))
        self.assertEqual(response, {'sensor1': 2})

        # Increment beyond max range, confirm rule set to max
        response = asyncio.run(request(target_ip, ['increment_rule', 'device1', '99999']))
        self.assertEqual(response, {'device1': 1023})

    def test_09_reset_rule(self):
        response = asyncio.run(request(target_ip, ['reset_rule', 'sensor1']))
        self.assertEqual(response, {'sensor1': 'Reverted to scheduled rule', 'current_rule': 5})

    def test_10_reset_all_rules(self):
        response = asyncio.run(request(target_ip, ['reset_all_rules']))
        self.assertEqual(
            response,
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

    def test_11_get_schedule_rules(self):
        response = asyncio.run(request(target_ip, ['get_schedule_rules', 'sensor1']))
        self.assertEqual(response, {'01:00': 1, '06:00': 5})

    def test_12_add_rule(self):
        # Add a rule at a time where no rule exists
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '04:00', '256']))
        self.assertEqual(response, {'time': '04:00', 'Rule added': 256})

        # Add another rule at the same time, should refuse to overwrite
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '04:00', '512']))
        self.assertEqual(response, {'ERROR': "Rule already exists at 04:00, add 'overwrite' arg to replace"})

        # Add another rule at the same time with the 'overwrite' argument, rule should be replaced
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '04:00', '512', 'overwrite']))
        self.assertEqual(response, {'time': '04:00', 'Rule added': 512})

        # Add rule (0) which is equivalent to False in conditional (regression test for bug causing incorrect rejection)
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '02:52', '0']))
        self.assertEqual(response, {'time': '02:52', 'Rule added': 0})

        # Add a rule with sunrise keyword instead of timestamp
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', 'sunrise', '512']))
        self.assertEqual(response, {'time': 'sunrise', 'Rule added': 512})

    def test_13_remove_rule(self):
        # Delete a rule by timestamp
        response = asyncio.run(request(target_ip, ['remove_rule', 'device1', '04:00']))
        self.assertEqual(response, {'Deleted': '04:00'})

        # Delete a rule by keyword
        response = asyncio.run(request(target_ip, ['remove_rule', 'device1', 'sunrise']))
        self.assertEqual(response, {'Deleted': 'sunrise'})

    def test_14_save_rules(self):
        # Send command, verify response
        response = asyncio.run(request(target_ip, ['save_rules']))
        self.assertEqual(response, {"Success": "Rules written to disk"})

    def test_15_get_schedule_keywords(self):
        # Get keywords, should contain sunrise and sunset
        response = asyncio.run(request(target_ip, ['get_schedule_keywords']))
        self.assertEqual(len(response), 2)
        self.assertIn('sunrise', response.keys())
        self.assertIn('sunset', response.keys())

    def test_16_add_schedule_keyword(self):
        # Add keyword, confirm added
        response = asyncio.run(request(target_ip, ['add_schedule_keyword', {'sleep': '23:00'}]))
        self.assertEqual(response, {"Keyword added": 'sleep', "time": '23:00'})

    def test_17_remove_schedule_keyword(self):
        # Remove keyword, confirm removed
        response = asyncio.run(request(target_ip, ['remove_schedule_keyword', 'sleep']))
        self.assertEqual(response, {"Keyword removed": 'sleep'})

    def test_18_save_schedule_keywords(self):
        response = asyncio.run(request(target_ip, ['save_schedule_keywords']))
        self.assertEqual(response, {"Success": "Keywords written to disk"})

    def test_19_get_attributes(self):
        response = asyncio.run(request(target_ip, ['get_attributes', 'sensor1']))
        keys = response.keys()
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
        self.assertEqual(len(response.keys()), 11)
        self.assertEqual(response['_type'], 'pir')
        self.assertEqual(response['default_rule'], 5)
        self.assertEqual(response['name'], 'sensor1')
        self.assertEqual(response['nickname'], 'sensor1')

    def test_20_ir(self):
        response = asyncio.run(request(target_ip, ['ir_key', 'tv', 'power']))
        self.assertEqual(response, {'tv': 'power'})

        response = asyncio.run(request(target_ip, ['ir_key', 'ac', 'OFF']))
        self.assertEqual(response, {'ac': 'OFF'})

    def test_21_get_temp(self):
        response = asyncio.run(request(target_ip, ['get_temp']))
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response["Temp"], float)

    def test_22_get_humid(self):
        response = asyncio.run(request(target_ip, ['get_humid']))
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response["Humidity"], float)

    def test_23_get_climate(self):
        response = asyncio.run(request(target_ip, ['get_climate_data']))
        self.assertEqual(len(response), 2)
        self.assertIsInstance(response["humid"], float)
        self.assertIsInstance(response["temp"], float)

    def test_24_clear_log(self):
        response = asyncio.run(request(target_ip, ['clear_log']))
        self.assertEqual(response, {'clear_log': 'success'})

    def test_25_condition_met(self):
        response = asyncio.run(request(target_ip, ['condition_met', 'sensor1']))
        self.assertEqual(len(response), 1)
        self.assertIn("Condition", response.keys())

    def test_26_trigger_sensor(self):
        response = asyncio.run(request(target_ip, ['trigger_sensor', 'sensor1']))
        self.assertEqual(response, {'Triggered': 'sensor1'})

    def test_27_turn_on(self):
        # Ensure enabled
        asyncio.run(request(target_ip, ['enable', 'device1']))

        response = asyncio.run(request(target_ip, ['turn_on', 'device1']))
        self.assertEqual(response, {'On': 'device1'})

    def test_28_turn_off(self):
        # Ensure enabled
        asyncio.run(request(target_ip, ['enable', 'device1']))

        response = asyncio.run(request(target_ip, ['turn_off', 'device1']))
        self.assertEqual(response, {'Off': 'device1'})

        # Ensure disabled
        asyncio.run(request(target_ip, ['disable', 'device1']))

        # Should still be able to turn off (but not on)
        response = asyncio.run(request(target_ip, ['turn_off', 'device1']))
        self.assertEqual(response, {'Off': 'device1'})

    # Original bug: Enabling and turning on when both current and scheduled rules == "disabled"
    # resulted in comparison operator between int and string, causing crash.
    # After fix (see efd79c6f) this is handled by overwriting current_rule with default_rule.
    def test_29_enable_regression_test(self):
        # Confirm correct starting conditions
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['current_rule'], 'disabled')
        self.assertEqual(response['scheduled_rule'], 'disabled')
        # Enable and turn on to reproduce issue
        response = asyncio.run(request(target_ip, ['enable', 'device3']))
        response = asyncio.run(request(target_ip, ['turn_on', 'device3']))
        # Should not crash, should replace unusable rule with default_rule (256) and fade on
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['current_rule'], 256)
        self.assertEqual(response['scheduled_rule'], 'disabled')
        self.assertEqual(response['state'], True)
        self.assertEqual(response['enabled'], True)

    # Original bug: LedStrip fade method made calls to set_rule method for each fade step.
    # Later, set_rule was modified to abort an in-progress fade when it received a brightness
    # rule. This caused fade to abort itself after the first step. Fixed in a29f5383.
    def test_30_regression_fade_on(self):
        # Starting conditions
        asyncio.run(request(target_ip, ['set_rule', 'device3', '500']))
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['fading'], False)

        # Start fade
        asyncio.run(request(target_ip, ['set_rule', 'device3', 'fade/505/15']))
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['fading']['target'], 505)

        # Wait for fade to complete
        time.sleep(16)
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['current_rule'], 505)
        self.assertEqual(response['fading'], False)

    # Confirm that calling set_rule while a fade is in-progress correctly aborts
    def test_31_abort_fade(self):
        # Starting conditions
        asyncio.run(request(target_ip, ['set_rule', 'device3', '500']))
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['fading'], False)

        # Start 5 minute fade to 505 brightness, confirm started
        asyncio.run(request(target_ip, ['set_rule', 'device3', 'fade/505/300']))
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['fading']['target'], 505)

        # Wait 5 seconds, then change rule - fade should abort, new rule should be used
        time.sleep(5)
        asyncio.run(request(target_ip, ['set_rule', 'device3', '400']))
        response = asyncio.run(request(target_ip, ['get_attributes', 'device3']))
        self.assertEqual(response['current_rule'], 400)
        self.assertEqual(response['fading'], False)


class TestParseCommandInvalid(unittest.TestCase):

    def test_32_disable_invalid(self):
        response = asyncio.run(request(target_ip, ['disable', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['disable', 'other']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['disable']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

    def test_33_disable_in_invalid(self):
        response = asyncio.run(request(target_ip, ['disable_in', 'device99', '5']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['disable_in', 'other', '5']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['disable_in', 'device1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['disable_in']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['disable_in', 'device1', float('NaN')]))
        self.assertEqual(response, {'ERROR': 'Syntax error in received JSON'})

    def test_34_enable_invalid(self):
        response = asyncio.run(request(target_ip, ['enable', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['enable', 'other']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['enable']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

    def test_35_enable_in_invalid(self):
        response = asyncio.run(request(target_ip, ['enable_in', 'device99', '5']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['enable_in', 'other', '5']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['enable_in', 'device1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['enable_in']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['enable_in', 'device1', float('NaN')]))
        self.assertEqual(response, {'ERROR': 'Syntax error in received JSON'})

    def test_36_set_rule_invalid(self):
        response = asyncio.run(request(target_ip, ['set_rule']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['set_rule', 'device1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['set_rule', 'device99', '5']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['set_rule', 'device1', '9999']))
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

    def test_37_increment_rule_invalid(self):
        response = asyncio.run(request(target_ip, ['increment_rule']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['increment_rule', 'sensor1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['increment_rule', 'sensor1', float('NaN')]))
        self.assertEqual(response, {'ERROR': 'Syntax error in received JSON'})

        response = asyncio.run(request(target_ip, ['increment_rule', 'sensor1', 'string']))
        self.assertEqual(response, {'ERROR': 'Invalid argument string'})

        response = asyncio.run(request(target_ip, ['increment_rule', 'device2', '1']))
        self.assertEqual(response, {'ERROR': 'Unsupported target, must accept int or float rule'})

    def test_38_reset_rule_invalid(self):
        response = asyncio.run(request(target_ip, ['reset_rule']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['reset_rule', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['reset_rule', 'notdevice']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_39_get_schedule_rules_invalid(self):
        response = asyncio.run(request(target_ip, ['get_schedule_rules']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['get_schedule_rules', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['get_schedule_rules', 'notdevice']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_40_add_rule_invalid(self):
        response = asyncio.run(request(target_ip, ['add_schedule_rule']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'notdevice']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '99:99']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '08:00']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '256']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '05:00', '256']))
        self.assertEqual(response, {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '05:00', '256', 'del']))
        self.assertEqual(response, {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        # Should get error response from node (cannot regex timestamp without rejecting keyword)
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '99:13', '256']))
        self.assertEqual(response, {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device99', '09:13', '256']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device99', '99:13', '256']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', '09:13', '9999']))
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

        # Should get error response from node, schedule keyword doesn't exist
        response = asyncio.run(request(target_ip, ['add_schedule_rule', 'device1', 'midnight', '50']))
        self.assertEqual(response, {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

    def test_41_remove_rule_invalid(self):
        response = asyncio.run(request(target_ip, ['remove_rule']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'notdevice']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'device1']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'device1', '99:99']))
        self.assertEqual(response, {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'device99', '01:00']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'device1', '07:16']))
        self.assertEqual(response, {'ERROR': 'No rule exists at that time'})

        response = asyncio.run(request(target_ip, ['remove_rule', 'device1', 'midnight']))
        self.assertEqual(response, {'ERROR': 'Timestamp format must be HH:MM (no AM/PM) or schedule keyword'})

    def test_42_add_schedule_keyword_invalid(self):
        response = asyncio.run(request(target_ip, ['add_schedule_keyword']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['add_schedule_keyword', 'new_keyword']))
        self.assertEqual(response, {"ERROR": "Requires dict with keyword and timestamp"})

        response = asyncio.run(request(target_ip, ['add_schedule_keyword', {'new_keyword': '99:99'}]))
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

    def test_43_remove_schedule_keyword_invalid(self):
        response = asyncio.run(request(target_ip, ['remove_schedule_keyword']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['remove_schedule_keyword', 'sunrise']))
        self.assertEqual(response, {"ERROR": "Cannot delete sunrise or sunset"})

        response = asyncio.run(request(target_ip, ['remove_schedule_keyword', 'doesnotexist']))
        self.assertEqual(response, {"ERROR": "Keyword does not exist"})

    def test_44_get_attributes_invalid(self):
        response = asyncio.run(request(target_ip, ['get_attributes']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['get_attributes', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['get_attributes', 'notdevice']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_45_ir_invalid(self):
        response = asyncio.run(request(target_ip, ['ir_key']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['ir_key', 'foo']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['ir_key', 'ac']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['ir_key', 'foo', 'on']))
        self.assertEqual(response, {'ERROR': 'No codes found for target "foo"'})

        response = asyncio.run(request(target_ip, ['ir_key', 'ac', 'power']))
        self.assertEqual(response, {'ERROR': 'Target "ac" has no key "power"'})

        response = asyncio.run(request(target_ip, ['ir_key', 'tv']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['ir_key', 'tv', 'START']))
        self.assertEqual(response, {'ERROR': 'Target "tv" has no key "START"'})

    def test_46_condition_met_invalid(self):
        response = asyncio.run(request(target_ip, ['condition_met']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['condition_met', 'device1']))
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = asyncio.run(request(target_ip, ['condition_met', 'sensor99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_47_trigger_sensor_invalid(self):
        response = asyncio.run(request(target_ip, ['trigger_sensor']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['trigger_sensor', 'device1']))
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = asyncio.run(request(target_ip, ['trigger_sensor', 'sensor99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = asyncio.run(request(target_ip, ['trigger_sensor', 'sensor2']))
        self.assertEqual(response, {'ERROR': 'Cannot trigger si7021 sensor type'})

    def test_48_turn_on_invalid(self):
        # Ensure disabled
        asyncio.run(request(target_ip, ['disable', 'device1']))

        response = asyncio.run(request(target_ip, ['turn_on', 'device1']))
        self.assertEqual(response, {'ERROR': 'device1 is disabled, please enable before turning on'})

        response = asyncio.run(request(target_ip, ['turn_on']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['turn_on', 'sensor1']))
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = asyncio.run(request(target_ip, ['turn_on', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_49_turn_off_invalid(self):
        response = asyncio.run(request(target_ip, ['turn_off']))
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = asyncio.run(request(target_ip, ['turn_off', 'sensor1']))
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = asyncio.run(request(target_ip, ['turn_off', 'device99']))
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})
