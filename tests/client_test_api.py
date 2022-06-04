import unittest
from api_client import *
import time



class TestParseIP(unittest.TestCase):

    def test_all_nodes(self):
        args = ['--all', 'status']
        self.assertTrue(parse_ip(args))

    def test_node_name(self):
        args = ['bedroom', 'status']
        self.assertTrue(parse_ip(args))

    def test_ip_flag(self):
        args = ['-ip', '192.168.1.223', 'status']
        self.assertTrue(parse_ip(args))

    def test_no_ip_flag(self):
        args = ['192.168.1.223', 'status']
        self.assertTrue(parse_ip(args))



class TestParseIPInvalid(unittest.TestCase):

    def test_all_nodes_no_command(self):
        args = ['--all']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_all_nodes_invalid_command(self):
        args = ['--all', 'notacommand']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_node_name_no_command(self):
        args = ['bedroom']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_node_name_invalid_command(self):
        args = ['bedroom', 'notacommand']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_invalid_node_name(self):
        args = ['fakeroom', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_ip_flag_no_command(self):
        args = ['-ip', '192.168.1.223']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_ip_flag_invalid_command(self):
        args = ['-ip', '192.168.1.223', 'notacommand']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_ip_flag_invalid_ip(self):
        args = ['-ip', '192.168.1', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['-ip', '999.999.999.999', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['-ip', '192.168.1.999', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['-ip', '192.168.o.ll', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['-ip', '1921681223', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_no_ip_flag_no_command(self):
        args = ['192.168.1.223']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_no_ip_flag_invalid_command(self):
        args = ['192.168.1.223', 'notacommand']
        with self.assertRaises(SystemExit):
            parse_ip(args)

    def test_no_ip_flag_invalid_ip(self):
        args = ['192.168.1', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['999.999.999.999', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['192.168.1.999', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['192.168.o.ll', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)

        args = ['1921681223', 'status']
        with self.assertRaises(SystemExit):
            parse_ip(args)



class TestParseCommand(unittest.TestCase):

    # Test reboot first for predictable initial state (replace schedule rules deleted by last test etc)
    def test_1(self):
        response = parse_command("192.168.1.223", ['reboot'])
        self.assertEqual(response, "Rebooting")

        # Wait for node to finish booting before running next test
        time.sleep(20)

    def test_status(self):
        response = parse_command("192.168.1.223", ['status'])
        keys = response.keys()
        self.assertIn('metadata', keys)
        self.assertIn('sensors', keys)
        self.assertIn('devices', keys)
        self.assertEqual(len(response.keys()), 3)

    def test_disable(self):
        response = parse_command("192.168.1.223", ['disable', 'device1'])
        self.assertEqual(response, {'Disabled': 'device1'})

    def test_disable_in(self):
        response = parse_command("192.168.1.223", ['disable_in', 'device1', '1'])
        self.assertEqual(response, {'Disable_in_seconds': 60.0, 'Disabled': 'device1'})

    def test_enable(self):
        response = parse_command("192.168.1.223", ['enable', 'sensor1'])
        self.assertEqual(response, {'Enabled': 'sensor1'})

    def test_enable_in(self):
        response = parse_command("192.168.1.223", ['enable_in', 'sensor1', '1'])
        self.assertEqual(response, {'Enabled': 'sensor1', 'Enable_in_seconds': 60.0})

    def test_set_rule(self):
        response = parse_command("192.168.1.223", ['set_rule', 'sensor1', '1'])
        self.assertEqual(response, {'sensor1': '1'})

    def test_reset_rule(self):
        response = parse_command("192.168.1.223", ['reset_rule', 'sensor1'])
        self.assertEqual(response["sensor1"], 'Reverted to scheduled rule')

    def test_get_schedule_rules(self):
        response = parse_command("192.168.1.223", ['get_schedule_rules', 'sensor1'])
        self.assertEqual(response, {'01:00': '1', '06:00': '5'})

    def test_add_rule(self):
        response = parse_command("192.168.1.223", ['add_rule', 'device1', '08:00', '256'])
        self.assertEqual(response, {'time': '08:00', 'Rule added': '256'})

    def test_remove_rule(self):
        response = parse_command("192.168.1.223", ['remove_rule', 'device1', '01:00'])
        self.assertEqual(response, {'Deleted': '01:00'})

    def test_get_attributes(self):
        response = parse_command("192.168.1.223", ['get_attributes', 'sensor1'])
        keys = response.keys()
        self.assertIn('sensor_type', keys)
        self.assertIn('rule_queue', keys)
        self.assertIn('enabled', keys)
        self.assertIn('targets', keys)
        self.assertIn('name', keys)
        self.assertIn('scheduled_rule', keys)
        self.assertIn('state', keys)
        self.assertIn('current_rule', keys)
        self.assertIn('motion', keys)
        self.assertEqual(len(response.keys()), 9)

    def test_ir(self):
        response = parse_command("192.168.1.223", ['ir', 'tv', 'power'])
        self.assertEqual(response, {'tv': 'power'})

        response = parse_command("192.168.1.223", ['ir', 'ac', 'OFF'])
        self.assertEqual(response, {'ac': 'OFF'})

        response = parse_command("192.168.1.223", ['ir', 'backlight', 'on'])
        self.assertEqual(response, {'backlight': 'on'})

    def test_get_temp(self):
        response = parse_command("192.168.1.223", ['get_temp'])
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response["Temp"], float)

    def test_get_humid(self):
        response = parse_command("192.168.1.223", ['get_humid'])
        self.assertEqual(len(response), 1)
        self.assertIsInstance(response["Humidity"], float)

    def test_clear_log(self):
        response = parse_command("192.168.1.223", ['clear_log'])
        self.assertEqual(response, {'clear_log': 'success'})

    def test_condition_met(self):
        response = parse_command("192.168.1.223", ['condition_met', 'sensor1'])
        self.assertEqual(len(response), 1)
        self.assertIn("Condition", response.keys())

    def test_trigger_sensor(self):
        response = parse_command("192.168.1.223", ['trigger_sensor', 'sensor1'])
        self.assertEqual(response, {'Triggered': 'sensor1'})

    def test_turn_on(self):
        # Ensure enabled
        parse_command("192.168.1.223", ['enable', 'device1'])

        response = parse_command("192.168.1.223", ['turn_on', 'device1'])
        self.assertEqual(response, {'On': 'device1'})

    def test_turn_off(self):
        # Ensure enabled
        parse_command("192.168.1.223", ['enable', 'device1'])

        response = parse_command("192.168.1.223", ['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})



class TestParseCommandInvalid(unittest.TestCase):

    def test_disable_invalid(self):
        response = parse_command("192.168.1.223", ['disable', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['disable', 'other'])
        self.assertEqual(response, {'ERROR': 'Can only disable devices and sensors'})

        response = parse_command("192.168.1.223", ['disable'])
        self.assertEqual(response, {'Example usage': './api_client.py disable [device|sensor]'})

    def test_disable_in_invalid(self):
        response = parse_command("192.168.1.223", ['disable_in', 'device99', '5'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['disable_in', 'other', '5'])
        self.assertEqual(response, {'ERROR': 'Can only disable devices and sensors'})

        response = parse_command("192.168.1.223", ['disable_in', 'device1'])
        self.assertEqual(response, {'ERROR': 'Please specify delay in minutes'})

        response = parse_command("192.168.1.223", ['disable_in'])
        self.assertEqual(response, {'Example usage': './api_client.py disable_in [device|sensor] [minutes]'})

    def test_enable_invalid(self):
        response = parse_command("192.168.1.223", ['enable', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['enable', 'other'])
        self.assertEqual(response, {'ERROR': 'Can only enable devices and sensors'})

        response = parse_command("192.168.1.223", ['enable'])
        self.assertEqual(response, {'Example usage': './api_client.py enable [device|sensor]'})

    def test_enable_in_invalid(self):
        response = parse_command("192.168.1.223", ['enable_in', 'device99', '5'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['enable_in', 'other', '5'])
        self.assertEqual(response, {'ERROR': 'Can only enable devices and sensors'})

        response = parse_command("192.168.1.223", ['enable_in', 'device1'])
        self.assertEqual(response, {'ERROR': 'Please specify delay in minutes'})

        response = parse_command("192.168.1.223", ['enable_in'])
        self.assertEqual(response, {'Example usage': './api_client.py enable_in [device|sensor] [minutes]'})

    def test_set_rule_invalid(self):
        response = parse_command("192.168.1.223", ['set_rule'])
        self.assertEqual(response, {'Example usage': './api_client.py set_rule [device|sensor] [rule]'})

        response = parse_command("192.168.1.223", ['set_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify new rule'})

        response = parse_command("192.168.1.223", ['set_rule', 'device99', '5'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['set_rule', 'device1', '9999'])
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

    def test_reset_rule_invalid(self):
        response = parse_command("192.168.1.223", ['reset_rule'])
        self.assertEqual(response, {'Example usage': './api_client.py reset_rule [device|sensor]'})

        response = parse_command("192.168.1.223", ['reset_rule', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['reset_rule', 'notdevice'])
        self.assertEqual(response, {'ERROR': 'Can only set rules for devices and sensors'})

    def test_get_schedule_rules_invalid(self):
        response = parse_command("192.168.1.223", ['get_schedule_rules'])
        self.assertEqual(response, {'Example usage': './api_client.py get_schedule_rules [device|sensor]'})

        response = parse_command("192.168.1.223", ['get_schedule_rules', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['get_schedule_rules', 'notdevice'])
        self.assertEqual(response, {'ERROR': 'Only devices and sensors have schedule rules'})

    def test_add_rule_invalid(self):
        response = parse_command("192.168.1.223", ['add_rule'])
        self.assertEqual(response, {'Example usage': './api_client.py add_rule [device|sensor] [HH:MM] [rule] <overwrite>'})

        response = parse_command("192.168.1.223", ['add_rule', 'notdevice'])
        self.assertEqual(response, {'ERROR': 'Only devices and sensors have schedule rules'})

        response = parse_command("192.168.1.223", ['add_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['add_rule', 'device1', '99:99'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['add_rule', 'device1', '08:00'])
        self.assertEqual(response, {'ERROR': 'Must specify new rule'})

        response = parse_command("192.168.1.223", ['add_rule', 'device1', '05:00', '256'])
        self.assertEqual(response, {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = parse_command("192.168.1.223", ['add_rule', 'device1', '05:00', '256', 'del'])
        self.assertEqual(response, {'ERROR': "Rule already exists at 05:00, add 'overwrite' arg to replace"})

        response = parse_command("192.168.1.223", ['add_rule', 'device99', '09:13', '256'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['add_rule', 'device99', '99:13', '256'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['add_rule', 'device99', '256'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['add_rule', 'device1', '09:13', '9999'])
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

    def test_remove_rule_invalid(self):
        response = parse_command("192.168.1.223", ['remove_rule'])
        self.assertEqual(response, {'Example usage': './api_client.py remove_rule [device|sensor] [HH:MM]'})

        response = parse_command("192.168.1.223", ['remove_rule', 'notdevice'])
        self.assertEqual(response, {'ERROR': 'Only devices and sensors have schedule rules'})

        response = parse_command("192.168.1.223", ['remove_rule', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['remove_rule', 'device1', '99:99'])
        self.assertEqual(response, {'ERROR': 'Must specify time (HH:MM) followed by rule'})

        response = parse_command("192.168.1.223", ['remove_rule', 'device99', '01:00'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_get_attributes_invalid(self):
        response = parse_command("192.168.1.223", ['get_attributes'])
        self.assertEqual(response, {'Example usage': './api_client.py get_attributes [device|sensor]'})

        response = parse_command("192.168.1.223", ['get_attributes', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

        response = parse_command("192.168.1.223", ['get_attributes', 'notdevice'])
        self.assertEqual(response, {'ERROR': 'Must specify device or sensor'})

    def test_ir_invalid(self):
        response = parse_command("192.168.1.223", ['ir'])
        self.assertEqual(response, {'Example usage': './api_client.py ir [tv|ac|backlight] [command]'})

        response = parse_command("192.168.1.223", ['ir', 'foo'])
        self.assertEqual(response, {'Example usage': './api_client.py ir [tv|ac|backlight] [command]'})

        response = parse_command("192.168.1.223", ['ir', 'ac'])
        self.assertEqual(response, {'ERROR': 'Must speficy one of the following commands: ON, OFF, UP, DOWN, FAN, TIMER, UNITS, MODE, STOP, START'})

        response = parse_command("192.168.1.223", ['ir', 'ac', 'power'])
        self.assertEqual(response, {'ERROR': 'Target "ac" has no key power'})

        response = parse_command("192.168.1.223", ['ir', 'tv'])
        self.assertEqual(response, {'ERROR': 'Must speficy one of the following commands: power, vol_up, vol_down, mute, up, down, left, right, enter, settings, exit, source'})

        response = parse_command("192.168.1.223", ['ir', 'tv', 'START'])
        self.assertEqual(response, {'ERROR': 'Target "tv" has no key START'})

        response = parse_command("192.168.1.223", ['ir', 'backlight'])
        self.assertEqual(response, {'ERROR': "Must specify 'on' or 'off'"})

        response = parse_command("192.168.1.223", ['ir', 'backlight', 'start'])
        self.assertEqual(response, {'ERROR': "Must specify 'on' or 'off'"})

    def test_condition_met_invalid(self):
        response = parse_command("192.168.1.223", ['condition_met'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = parse_command("192.168.1.223", ['condition_met', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = parse_command("192.168.1.223", ['condition_met', 'sensor99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_trigger_sensor_invalid(self):
        response = parse_command("192.168.1.223", ['trigger_sensor'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = parse_command("192.168.1.223", ['trigger_sensor', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

        response = parse_command("192.168.1.223", ['trigger_sensor', 'sensor99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_turn_on_invalid(self):
        # Ensure disabled
        parse_command("192.168.1.223", ['disable', 'device1'])

        response = parse_command("192.168.1.223", ['turn_on', 'device1'])
        self.assertEqual(response, {'ERROR': 'Unable to turn on device1'})

        response = parse_command("192.168.1.223", ['turn_on'])
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = parse_command("192.168.1.223", ['turn_on', 'sensor1'])
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = parse_command("192.168.1.223", ['turn_on', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})

    def test_turn_off_invalid(self):
        # Ensure disabled
        parse_command("192.168.1.223", ['disable', 'device1'])

        response = parse_command("192.168.1.223", ['turn_off', 'device1'])
        self.assertEqual(response, {'ERROR': 'Unable to turn off device1'})

        response = parse_command("192.168.1.223", ['turn_off'])
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = parse_command("192.168.1.223", ['turn_off', 'sensor1'])
        self.assertEqual(response, {'ERROR': 'Can only turn on/off devices, use enable/disable for sensors'})

        response = parse_command("192.168.1.223", ['turn_off', 'device99'])
        self.assertEqual(response, {'ERROR': 'Instance not found, use status to see options'})
