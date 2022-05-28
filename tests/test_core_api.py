import unittest
from Config import Config
import SoftwareTimer
import uasyncio as asyncio
import json



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
            "device1"
        ],
        "type": "si7021",
        "schedule": {
            "10:00": 74,
            "22:00": 74
        },
        "pin": 15,
        "default_rule": 70,
        "default_setting": 74
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
    "ir_blaster": {
        "pin": 32,
        "target": "tv"
    }
}

# Instantiate config object, pass to API
config = Config(config_file)

from Api import app
app.config = config



class TestApi(unittest.TestCase):

    def __init__(self):
        self.device1 = config.find("device1")
        self.sensor1 = config.find("sensor1")
        self.sensor2 = config.find("sensor2")

    async def request(self, msg):
        reader, writer = await asyncio.open_connection("192.168.1.223", 8123)
        try:
            writer.write('{}\n'.format(json.dumps(msg)).encode())
            await writer.drain()
            res = await reader.read(1000)
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
        response = asyncio.run(self.request(cmd))

        return response

    def test_status(self):
        response = self.send_command(['status'])
        self.assertIsInstance(response, dict)

    def test_enable(self):
        # Disable target device (might succeed incorrectly if it's already enabled)
        self.device1.disable()
        # Enable with API command
        response = self.send_command(['enable', 'device1'])
        self.assertTrue(self.device1.enabled)
        self.assertEqual(response, {'Enabled': 'device1'})

    def test_disable(self):
        # Enable target device (might succeed incorrectly if it's already disabled)
        self.device1.enable()
        # Disable with API command
        response = self.send_command(['disable', 'device1'])
        self.assertFalse(self.device1.enabled)
        self.assertEqual(response, {'Disabled': 'device1'})

    def test_enable_in(self):
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

    def test_disable_in(self):
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

    def test_set_rule(self):
        # Set to valid rule 5
        response = self.send_command(['set_rule', 'sensor2', '5'])
        self.assertEqual(self.sensor2.current_rule, 5.0)
        self.assertEqual(response, {'sensor2': '5'})

        # Attempt to set invalid rule True
        response = self.send_command(['set_rule', 'sensor2', 'True'])
        self.assertEqual(self.sensor2.current_rule, 5.0)
        self.assertEqual(response, {'ERROR': 'Invalid rule'})

    def test_reset_rule(self):
        # Set placeholder rule
        self.device1.set_rule(1)
        # Call reset API command
        response = self.send_command(['reset_rule', 'device1'])
        self.assertEqual(response, {'device1': 'Reverted to scheduled rule', 'current_rule': self.device1.scheduled_rule})
        self.assertEqual(self.device1.current_rule, self.device1.scheduled_rule)

    def test_get_schedule_rules(self):
        response = self.send_command(['get_schedule_rules', 'device1'])
        self.assertEqual(response, {'20:00': 915, '09:00': 734, '11:00': 345})

    def test_add_schedule_rule(self):
        response = self.send_command(['add_schedule_rule', 'device1', '05:37', '64'])
        self.assertEqual(response, {'time': '05:37', 'Rule added': '64'})

    def test_remove_rule(self):
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

    def test_get_attributes(self):
        response = self.send_command(['get_attributes', 'sensor1'])
        self.assertIsInstance(response, dict)
        self.assertEqual(response["sensor_type"], "si7021")
        self.assertEqual(response["targets"], ['device1'])

    def test_trigger_sensor_condition_met(self):
        # Initial state should be False
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': False})
        # Trigger sensor
        response = self.send_command(['trigger_sensor', 'sensor2'])
        self.assertEqual(response, {'Triggered': 'sensor2'})
        # State should now be True
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': True})
        # Set very short timeout
        response = self.send_command(['set_rule', 'sensor2', '0.0001'])
        # Wait for reset timer to expire
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(await asyncio.sleep(1))
        # State should now be False
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': False})

    def test_turn_on(self):
        # Make sure device is enabled and turned off before testing
        self.device1.enable()
        self.device1.send(0)
        # Send command to turn on
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'On': 'device1'})
        # PWM duty cycle should now be same as current rule
        self.assertEqual(self.device1.pwm.duty(), self.device1.current_rule)

    def test_turn_on(self):
        # Make sure device is enabled and turned on before testing
        self.device1.enable()
        self.device1.send(1)
        # Send command to turn on
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})
        # PWM duty cycle should now be 0
        self.assertEqual(self.device1.pwm.duty(), 0)

    def test_get_temp(self):
        response = self.send_command(['get_temp'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Temp"], float)

    def test_get_humid(self):
        response = self.send_command(['get_humid'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Humidity"], float)

    def test_clear_log(self):
        response = self.send_command(['clear_log'])
        self.assertEqual(response, {'clear_log': 'success'})

    def test_ir_key(self):
        response = self.send_command(['ir_key', 'tv', 'power'])
        self.assertEqual(response, {'tv': 'power'})

    def test_backlight(self):
        response = self.send_command(['backlight', 'off'])
        self.assertEqual(response, {'backlight': 'off'})
