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
        self.assertEqual(response, {'Reboot_in': '1 second'})

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
