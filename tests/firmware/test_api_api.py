import os
import sys
import json
import asyncio
import network
import logging
import unittest
from machine import reset, Pin
import app_context
from Config import Config
from cpython_only import cpython_only

# Read mock API receiver address
with open('config.json', 'r') as file:
    test_config = json.load(file)

# IP and port of mock API receiver instance (for WLED)
mock_address = f"{test_config['mock_receiver']['ip']}:{test_config['mock_receiver']['port']}"

# Get IP address
ip = network.WLAN(network.WLAN.IF_STA).ifconfig()[0]


config_file = {
    "metadata": {
        "id": "unit-testing",
        "location": "test environment",
        "floor": "0"
    },
    "schedule_keywords": {
        'sunrise': '06:00',
        'sunset': '18:00'
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
        "units": "fahrenheit",
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
        "_type": "load-cell",
        "targets": [],
        "pin_data": 34,
        "pin_clock": 33,
        "default_rule": 100000,
        "schedule": {},
        "nickname": "sensor4"
    },
    "device1": {
        "_type": "wled",
        "schedule": {
            "09:00": 75,
            "11:00": 35,
            "20:00": 90
        },
        "min_rule": 1,
        "max_rule": 255,
        "default_rule": 50,
        "nickname": "device1",
        "ip": mock_address
    },
    "ir_blaster": {
        "pin": 32,
        "target": ["samsung_tv"],
        "macros": {}
    }
}


# Mock endpoint that raises uncaught exception for testing
def uncaught_exception(self, args):
    raise TypeError


class TestApi(unittest.TestCase):

    # Used to yield so SoftwareTimer create/cancel tasks can run
    async def sleep(self, ms):
        await asyncio.sleep_ms(ms)

    @classmethod
    def setUpClass(cls):
        # Instantiate config object, pass to global context
        app_context.config_instance = Config(config_file, delay_setup=True)
        app_context.config_instance._instantiate_peripherals()
        app_context.config_instance._build_queue()
        app_context.config_instance._build_groups()

        cls.device1 = app_context.config_instance.find("device1")
        cls.sensor1 = app_context.config_instance.find("sensor1")
        cls.sensor2 = app_context.config_instance.find("sensor2")
        cls.sensor3 = app_context.config_instance.find("sensor3")
        cls.sensor4 = app_context.config_instance.find("sensor4")

        # Patch API backend to add mock endpoint that raises exception
        if sys.implementation.name == 'cpython':
            app_context.api_instance.uncaught_exception = uncaught_exception.__get__(
                app_context.api_instance
            )

        try:
            os.remove('ir_macros.json')
        except OSError:
            pass

        try:
            os.remove('log_level.py')
        except OSError:
            pass

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove('ir_macros.json')
        except OSError:
            pass

        try:
            os.remove('log_level.py')
        except OSError:
            pass

    def tearDown(self):
        # Cancel timers started by endpoints after each test
        app_context.timer_instance.cancel('rebuild_queue')
        app_context.timer_instance.cancel('device1_enable_in')
        app_context.timer_instance.cancel('device1_fade')
        asyncio.run(self.sleep(10))

    async def request(self, msg):
        reader, writer = await asyncio.open_connection(ip, 8123)
        try:
            writer.write('{}\n'.format(json.dumps(msg)).encode())
            await writer.drain()
            res = await asyncio.wait_for(reader.read(1500), timeout=1)
        except asyncio.TimeoutError:
            return "Error: Timed out waiting for response"
        except OSError:
            return "Error: Request failed"
        try:
            response = json.loads(res)
        except ValueError:
            return "Error: Unable to decode response"
        writer.close()
        await writer.wait_closed()

        return response

    def send_command(self, cmd):
        return asyncio.run(self.request(cmd))

    async def request_http(self, msg):
        reader, writer = await asyncio.open_connection(ip, 8123)
        try:
            writer.write(msg.encode())
            writer.write('Host: 10.0.0.10:8123\r\n'.encode())
            writer.write('Accept-Language: en-US,en;q=0.5\r\n'.encode())
            writer.write('\r\n\r\n'.encode())
            await writer.drain()
            res = await reader.read(1500)
        except OSError:
            pass
        writer.close()
        await writer.wait_closed()

        return res.decode()

    def send_http_command(self, cmd):
        return asyncio.run(self.request_http(cmd))

    async def broken_connection(self):
        reader, writer = await asyncio.open_connection(ip, 8123)
        writer.close()
        await writer.wait_closed()

    def test_01_status(self):
        response = self.send_command(['status'])
        self.assertIsInstance(response, dict)

    @cpython_only
    def test_02_status_http(self):
        response = self.send_http_command('GET /status HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 200 NA\r\nContent-Type: application/json'))

    def test_03_enable(self):
        # Disable target device (might succeed incorrectly if it's already enabled)
        self.device1.disable()
        # Enable with API command
        response = self.send_command(['enable', 'device1'])
        self.assertTrue(self.device1.enabled)
        self.assertEqual(response, {'Enabled': 'device1'})

        # Simulate SoftwareTimer from previous disable_in call with same target
        app_context.timer_instance.create(9999, self.device1.disable, "device1_enable_in")
        asyncio.run(self.sleep(10))
        self.assertTrue("device1_enable_in" in str(app_context.timer_instance.schedule))

        # Call enable endpoint, should cancel disable_in callback timer
        self.send_command(['enable', 'device1'])
        self.assertTrue("device1_enable_in" not in str(app_context.timer_instance.schedule))

    def test_04_disable(self):
        # Enable target device (might succeed incorrectly if it's already disabled)
        self.device1.enable()
        # Disable with API command
        response = self.send_command(['disable', 'device1'])
        self.assertFalse(self.device1.enabled)
        self.assertEqual(response, {'Disabled': 'device1'})

        # Simulate SoftwareTimer from previous enable_in call with same target
        app_context.timer_instance.create(9999, self.device1.enable, "device1_enable_in")
        asyncio.run(self.sleep(10))
        self.assertTrue("device1_enable_in" in str(app_context.timer_instance.schedule))

        # Call enable endpoint, should cancel enable_in callback timer
        self.send_command(['enable', 'device1'])
        self.assertTrue("device1_enable_in" not in str(app_context.timer_instance.schedule))

    def test_05_enable_in(self):
        # Cancel all SoftwareTimers created by enable_in/disable_in for device1
        self.assertTrue("device1_enable_in" not in str(app_context.timer_instance.schedule))

        # Disable target device (might succeed incorrectly if it's already enabled)
        self.device1.disable()
        # Send API command to enable in 5 minutes
        response = self.send_command(['enable_in', 'device1', '5'])
        self.assertEqual(response, {'Enabled': 'device1', 'Enable_in_seconds': 300.0})
        # SoftwareTimer queue should now contain entry named "device1_enable_in"
        self.assertIn("device1_enable_in", str(app_context.timer_instance.schedule))
        # Device should still be disabled since timer hasn't expired yet
        self.assertFalse(self.device1.enabled)

        # Simulate SoftwareTimer from previous enable_in call with same target
        app_context.timer_instance.create(9999, self.device1.enable, "device1_enable_in")
        asyncio.run(self.sleep(10))
        # Get timer expiration timestamp
        for i in app_context.timer_instance.schedule:
            if app_context.timer_instance.schedule[i][0] == "device1_enable_in":
                old_timer = i
                break

        # Call enable_in endpoint, confirm old timer expiring in 9999 was canceled
        response = self.send_command(['enable_in', 'device1', '5'])
        self.assertTrue(old_timer not in app_context.timer_instance.schedule)

    def test_06_disable_in(self):
        # Cancel all SoftwareTimers created by enable_in/disable_in for device1
        self.assertTrue("device1_enable_in" not in str(app_context.timer_instance.schedule))

        # Enable target device (might succeed incorrectly if it's already disabled)
        self.device1.enable()
        # Send API command to disable in 5 minutes
        response = self.send_command(['disable_in', 'device1', '5'])
        self.assertEqual(response, {'Disable_in_seconds': 300.0, 'Disabled': 'device1'})
        # SoftwareTimer queue should now contain entry named "device1_enable_in"
        self.assertIn("device1_enable_in", str(app_context.timer_instance.schedule))
        # Device should still be enabled since timer hasn't expired yet
        self.assertTrue(self.device1.enabled)

        # Simulate SoftwareTimer from previous disable_in call with same target
        app_context.timer_instance.create(9999, self.device1.enable, "device1_enable_in")
        asyncio.run(self.sleep(10))
        # Get timer expiration timestamp
        for i in app_context.timer_instance.schedule:
            if app_context.timer_instance.schedule[i][0] == "device1_enable_in":
                old_timer = i
                break

        # Call disable_in endpoint, confirm old timer expiring in 9999 was canceled
        response = self.send_command(['disable_in', 'device1', '5'])
        self.assertTrue(old_timer not in app_context.timer_instance.schedule)

    def test_07_set_rule(self):
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
        self.assertEqual(response, {'device1': 'fade/50/3600'})
        # Confirm timer added to queue
        self.assertIn('device1_fade', str(app_context.timer_instance.schedule))

    def test_08_increment_rule(self):
        # Set known starting values
        self.device1.current_rule = 50
        self.sensor1.current_rule = 70

        # Increment PWM by both positive and negative numbers
        response = self.send_command(['increment_rule', 'device1', '-12'])
        self.assertEqual(response, {'device1': 38})
        self.assertEqual(self.device1.current_rule, 38)
        response = self.send_command(['increment_rule', 'device1', '30'])
        self.assertEqual(response, {'device1': 68})
        self.assertEqual(self.device1.current_rule, 68)

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

    def test_09_reset_rule(self):
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

    def test_10_reset_all_rules(self):
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

    def test_11_get_schedule_rules(self):
        response = self.send_command(['get_schedule_rules', 'device1'])
        self.assertEqual(response, {'20:00': 90, '09:00': 75, '11:00': 35})

    def test_12_add_schedule_rule(self):
        # Confirm no rebuild_queue timer in queue
        self.assertTrue("rebuild_queue" not in str(app_context.timer_instance.schedule))

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

        # Confirm created timer to rebuild queue with new schedule rule(s)
        self.assertIn("rebuild_queue", str(app_context.timer_instance.schedule))

    def test_13_remove_rule(self):
        # Confirm no rebuild_queue timer in queue
        self.assertTrue("rebuild_queue" not in str(app_context.timer_instance.schedule))

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

        # Confirm created timer to rebuild queue without removed rules
        self.assertIn("rebuild_queue", str(app_context.timer_instance.schedule))

    # Note: will fail if config.json missing or contains fewer devices/sensors than test config
    def test_14_save_schedule_rules(self):
        # Save rules, confirm response
        response = self.send_command(['save_rules'])
        self.assertEqual(response, {"Success": "Rules written to disk"})

    def test_15_get_schedule_keywords(self):
        # Get keywords, should contain sunrise and sunset
        response = self.send_command(['get_schedule_keywords'])
        self.assertEqual(len(response), 2)
        self.assertIn('sunrise', response.keys())
        self.assertIn('sunset', response.keys())

    def test_16_add_schedule_keyword(self):
        # Confirm no rebuild_queue timer in queue
        self.assertTrue("rebuild_queue" not in str(app_context.timer_instance.schedule))

        # Add keyword, confirm added
        response = self.send_command(['add_schedule_keyword', {'sleep': '23:00'}])
        self.assertEqual(response, {"Keyword added": 'sleep', "time": '23:00'})

        # Add keyword with invalid timestamp, confirm error
        response = self.send_command(['add_schedule_keyword', {'invalid': '3:00'}])
        self.assertEqual(response, {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"})

        # Confirm created timer to rebuild queue with new keyword timestamp
        self.assertIn("rebuild_queue", str(app_context.timer_instance.schedule))

    def test_17_remove_schedule_keyword(self):
        # Confirm no rebuild_queue timer in queue
        self.assertTrue("rebuild_queue" not in str(app_context.timer_instance.schedule))

        # Add schedule rule using keyword, should be deleted when keyword deleted
        app_context.config_instance.devices[0].schedule['sleep'] = 50

        # Remove keyword, confirm removed, confirm rule using keyword removed
        response = self.send_command(['remove_schedule_keyword', 'sleep'])
        self.assertEqual(response, {"Keyword removed": 'sleep'})
        self.assertTrue('sleep' not in app_context.config_instance.devices[0].schedule)

        # Confirm correct error when attempting to delete sunrise/sunset
        response = self.send_command(['remove_schedule_keyword', 'sunrise'])
        self.assertEqual(response, {"ERROR": "Cannot delete sunrise or sunset"})

        # Confirm correct error when attempting to non-existing keyword
        response = self.send_command(['remove_schedule_keyword', 'fake'])
        self.assertEqual(response, {"ERROR": "Keyword does not exist"})

        # Confirm created timer to rebuild queue without deleted keyword
        self.assertIn("rebuild_queue", str(app_context.timer_instance.schedule))

    def test_18_save_schedule_keywords(self):
        response = self.send_command(['save_schedule_keywords'])
        self.assertEqual(response, {"Success": "Keywords written to disk"})

    def test_19_get_attributes(self):
        response = self.send_command(['get_attributes', 'device1'])
        self.assertIsInstance(response, dict)
        self.assertEqual(response["_type"], "wled")
        self.assertEqual(response["group"], "group1")
        self.assertEqual(response["triggered_by"], ['sensor1', 'sensor2'])

    def test_20_trigger_sensor_condition_met(self):
        # Initial state should be False
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': False})
        # Trigger sensor
        response = self.send_command(['trigger_sensor', 'sensor2'])
        self.assertEqual(response, {'Triggered': 'sensor2'})
        # State should now be True
        response = self.send_command(['condition_met', 'sensor2'])
        self.assertEqual(response, {'Condition': True})

    def test_21_trigger_sensor_invalid(self):
        # Thermostat not compatible with endpoint
        response = self.send_command(['trigger_sensor', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Cannot trigger si7021 sensor type"})

        # Should return error if argument is not a sensor
        response = self.send_command(['trigger_sensor', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

    def test_22_condition_met_invalid(self):
        # Should return error if argument is not a sensor
        response = self.send_command(['condition_met', 'device1'])
        self.assertEqual(response, {'ERROR': 'Must specify sensor'})

    def test_23_turn_on(self):
        # Make sure device is enabled and turned off before testing
        self.device1.enable()
        self.device1.send(0)
        # Send command to turn on
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'On': 'device1'})
        # Confirm turned on
        self.assertTrue(self.device1.state)

        # Should not be able to turn on a disabled device
        self.device1.disable()
        self.device1.send(0)
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'ERROR': 'device1 is disabled, please enable before turning on'})

        # Device should still be off
        self.assertFalse(self.device1.state)

    def test_24_turn_on_invalid(self):
        self.device1.enable()

        # Should only accept devices, not sensors
        response = self.send_command(['turn_on', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

        # Change to invalid IP to simulate failed network connection
        self.device1.ip = "0.0.0."
        # Confirm endpoint returns error
        response = self.send_command(['turn_on', 'device1'])
        self.assertEqual(response, {'ERROR': 'Unable to turn on device1'})
        # Revert IP
        self.device1.ip = mock_address

    def test_25_turn_off(self):
        # Make sure device is enabled and turned on before testing
        self.device1.enable()
        self.device1.set_rule(50)
        self.device1.send(1)
        # Send command to turn on
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})
        # Confirm turned on
        self.assertFalse(self.device1.state)

        # Should be able to turn off a disabled device (just not on)
        self.device1.disable()
        self.device1.state = True
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'Off': 'device1'})

        # Device should now be off
        self.assertFalse(self.device1.state)

    def test_26_turn_off_invalid(self):
        # Should only accept devices, not sensors
        response = self.send_command(['turn_off', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"})

        # Change to invalid IP to simulate failed network connection
        self.device1.ip = "0.0.0."
        # Confirm endpoint returns error
        response = self.send_command(['turn_off', 'device1'])
        self.assertEqual(response, {'ERROR': 'Unable to turn off device1'})
        # Revert IP
        self.device1.ip = mock_address

    def test_27_get_temp(self):
        response = self.send_command(['get_temp'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Temp"], float)

    def test_28_get_humid(self):
        response = self.send_command(['get_humid'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["Humidity"], float)

    def test_29_get_climate_data(self):
        response = self.send_command(['get_climate_data'])
        self.assertIsInstance(response, dict)
        self.assertIsInstance(response["humid"], float)
        self.assertIsInstance(response["temp"], float)

    def test_30_no_temperature_sensor_errors(self):
        # Change temperature sensor type to simulate no temp sensor
        self.sensor1._type = "pir"

        # All endpoints should now return error
        response = self.send_command(['get_temp'])
        self.assertEqual(response, {"ERROR": "No temperature sensor configured"})
        response = self.send_command(['get_humid'])
        self.assertEqual(response, {"ERROR": "No temperature sensor configured"})
        response = self.send_command(['get_climate_data'])
        self.assertEqual(response, {"ERROR": "No temperature sensor configured"})

        # Revert sensor type
        self.sensor1._type = "si7021"

    def test_31_clear_log(self):
        response = self.send_command(['clear_log'])
        self.assertEqual(response, {'clear_log': 'success'})

        # Confirm correct error if log doesn't exist
        try:
            os.remove('app.log')
        except OSError:
            pass
        response = self.send_command(['clear_log'])
        self.assertEqual(response, {'ERROR': 'no log file found'})

    def test_32_ir_key(self):
        response = self.send_command(['ir_key', 'samsung_tv', 'power'])
        self.assertEqual(response, {'samsung_tv': 'power'})

        # Confirm correct error message
        response = self.send_command(['ir_key', 'samsung_tv', 'on'])
        self.assertEqual(response, {'ERROR': 'Target "samsung_tv" has no key "on"'})

        # Confirm correct error message
        response = self.send_command(['ir_key', 'whynter_ac', 'on'])
        self.assertEqual(response, {'ERROR': 'No codes found for target "whynter_ac"'})

    def test_33_ir_create_macro(self):
        # Confirm no macros
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros), 0)

        # Create macro, confirm response, confirm created
        response = self.send_command(['ir_create_macro', 'test1'])
        self.assertEqual(response, {"Macro created": 'test1'})
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros), 1)

        # Attempt to create duplicate, confirm error, confirm not created
        response = self.send_command(['ir_create_macro', 'test1'])
        self.assertEqual(response, {"ERROR": 'Macro named test1 already exists'})
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros), 1)

    def test_34_ir_add_macro_action(self):
        # Confirm macro created in last test has no actions
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros['test1']), 0)

        # Add action with all required args, confirm added
        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'power'])
        self.assertEqual(response, {"Macro action added": ['test1', 'samsung_tv', 'power']})
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros['test1']), 1)

        # Add action with all required and optional args, confirm added
        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'power', 50, 3])
        self.assertEqual(response, {"Macro action added": ['test1', 'samsung_tv', 'power', 50, 3]})
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros['test1']), 2)

        # Confirm error when attempting to add to non-existing macro
        response = self.send_command(['ir_add_macro_action', 'test99', 'samsung_tv', 'power'])
        self.assertEqual(response, {"ERROR": "Macro test99 does not exist, use create_macro to add"})

        # Confirm error when attempting to add action with non-existing target
        response = self.send_command(['ir_add_macro_action', 'test1', 'refrigerator', 'power'])
        self.assertEqual(response, {"ERROR": "No codes for refrigerator"})

        # Confirm error when attempting to add to non-existing key
        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'fake'])
        self.assertEqual(response, {"ERROR": "Target samsung_tv has no key fake"})

        # Confirm error when delay arg is not integer
        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'power', 'short'])
        self.assertEqual(response, {"ERROR": "Delay arg must be integer (milliseconds)"})

        # Confirm error when repeats arg is not integer
        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'power', '50', 'yes'])
        self.assertEqual(response, {"ERROR": "Repeat arg must be integer (number of times to press key)"})

    def test_35_ir_run_macro(self):
        # Run macro, confirm response
        response = self.send_command(['ir_run_macro', 'test1'])
        self.assertEqual(response, {"Ran macro": "test1"})

        # Attempt to run non-existing macro, confirm error
        response = self.send_command(['ir_run_macro', 'test99'])
        self.assertEqual(response, {"ERROR": "Macro test99 does not exist, use create_macro to add"})

    def test_36_ir_save_macros(self):
        # Save macros to disk, confirm response
        response = self.send_command(['ir_save_macros'])
        self.assertEqual(response, {"Success": "Macros written to disk"})

    def test_37_ir_get_existing_macros(self):
        # Save macros to disk, confirm response
        response = self.send_command(['ir_get_existing_macros'])
        self.assertEqual(response, {"test1": ["samsung_tv power 0 1", "samsung_tv power 50 3"]})

    def test_38_ir_delete_macro(self):
        # Confirm macro exists
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros), 1)

        # Delete macro, confirm response, confirm deleted
        response = self.send_command(['ir_delete_macro', 'test1'])
        self.assertEqual(response, {"Macro deleted": 'test1'})
        self.assertEqual(len(app_context.config_instance.ir_blaster.macros), 0)

        # Attempt to delete again, confirm error
        response = self.send_command(['ir_delete_macro', 'test1'])
        self.assertEqual(response, {"ERROR": 'Macro named test1 does not exist'})

    def test_39_no_ir_blaster_configured_errors(self):
        # Remove IrBlaster from config to test error
        ir_blaster = app_context.config_instance.ir_blaster
        app_context.config_instance.ir_blaster = None

        # Confirm correct error message for each IR endpoint
        response = self.send_command(['ir_key', 'whynter_ac', 'on'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_create_macro', 'test1'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_add_macro_action', 'test1', 'samsung_tv', 'power'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_run_macro', 'test1'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_save_macros'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_delete_macro', 'test1'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        response = self.send_command(['ir_get_existing_macros'])
        self.assertEqual(response, {"ERROR": "No IR blaster configured"})

        # Restore IrBlaster
        app_context.config_instance.ir_blaster = ir_blaster

    def test_40_set_gps_coords(self):
        response = self.send_command(['set_gps_coords', {'latitude': -90, 'longitude': 0}])
        self.assertEqual(response, {"Success": "GPS coordinates set"})

        response = self.send_command(['set_gps_coords', -90, 0])
        self.assertEqual(response, {"ERROR": "Requires dict with longitude and latitude keys"})

        response = self.send_command(['set_gps_coords', {'lat': -90, 'long': 0}])
        self.assertEqual(response, {"ERROR": "Requires dict with longitude and latitude keys"})

        response = self.send_command(['set_gps_coords', {'latitude': -99, 'longitude': 0}])
        self.assertEqual(response, {"ERROR": "Latitude must be between -90 and 90"})

        response = self.send_command(['set_gps_coords', {'latitude': 'string', 'longitude': 0}])
        self.assertEqual(response, {"ERROR": "Latitude must be between -90 and 90"})

        response = self.send_command(['set_gps_coords', {'latitude': -90, 'longitude': 999}])
        self.assertEqual(response, {"ERROR": "Longitude must be between -180 and 180"})

        response = self.send_command(['set_gps_coords', {'latitude': -90, 'longitude': 'string'}])
        self.assertEqual(response, {"ERROR": "Longitude must be between -180 and 180"})

    def test_41_load_cell_tare(self):
        response = self.send_command(['load_cell_tare', 'sensor4'])
        self.assertEqual(response, {"Success": "Sensor tared"})

        response = self.send_command(['load_cell_tare', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Must specify load cell sensor"})

    def test_42_load_cell_read(self):
        response = self.send_command(['load_cell_read', 'sensor4'])
        self.assertEqual(response, {"Raw": 0.0})

        response = self.send_command(['load_cell_read', 'sensor1'])
        self.assertEqual(response, {"ERROR": "Must specify load cell sensor"})

    def test_43_mem_info(self):
        response = self.send_command(['mem_info'])
        self.assertEqual(list(response.keys()), ['free', 'max_new_split', 'max_free_sz'])
        self.assertEqual(type(response['free']), int)
        self.assertEqual(type(response['max_new_split']), int)
        self.assertEqual(type(response['max_free_sz']), int)

    def test_44_invalid_command(self):
        response = self.send_command(['notacommand'])
        self.assertEqual(response, {"ERROR": "Invalid command"})

        # Confirm can't run Api class internal methods (finds endpoint handlers
        # with getattr, but there is a check to block calling internal methods)
        response = self.send_command(['_run'])
        self.assertEqual(response, {"ERROR": "Invalid command"})
        response = self.send_command(['_run_client'])
        self.assertEqual(response, {"ERROR": "Invalid command"})
        response = self.send_command(['_parse_http_request'])
        self.assertEqual(response, {"ERROR": "Invalid command"})
        response = self.send_command(['_invalid_endpoint_error'])
        self.assertEqual(response, {"ERROR": "Invalid command"})

    @cpython_only
    def test_45_invalid_http_endpoint(self):
        response = self.send_http_command('GET /notacommand HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 404 NA\r\nContent-Type: application/json'))

        # Confirm can't run Api class internal methods (finds endpoint handlers
        # with getattr, but there is a check to block calling internal methods)
        response = self.send_http_command('GET /_run HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 404 NA\r\nContent-Type: application/json'))
        response = self.send_http_command('GET /_run_client HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 404 NA\r\nContent-Type: application/json'))
        response = self.send_http_command('GET /_parse_http_request HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 404 NA\r\nContent-Type: application/json'))
        response = self.send_http_command('GET /_invalid_endpoint_error HTTP/1.1\r\n')
        self.assertTrue(response.startswith('HTTP/1.0 404 NA\r\nContent-Type: application/json'))

    def test_46_missing_arguments(self):
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

        response = self.send_command(['set_log_level'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_key'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_key', 'samsung_tv'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_create_macro'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_delete_macro'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_add_macro_action'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['ir_run_macro'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['set_gps_coords'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['load_cell_tare'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

        response = self.send_command(['load_cell_read'])
        self.assertEqual(response, {'ERROR': 'Invalid syntax'})

    @cpython_only
    def test_47_missing_querystring(self):
        # HTTP request with missing querystring arg
        response = self.send_http_command('GET /set_rule?device1 HTTP/1.1\r\n')
        self.assertEqual(
            response,
            'HTTP/1.0 200 NA\r\nContent-Type: application/json\r\n\r\n{"ERROR": "Invalid syntax"}'
        )

    def test_48_invalid_instance(self):
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

        response = self.send_command(['load_cell_tare', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

        response = self.send_command(['load_cell_read', 'device99'])
        self.assertEqual(response, {"ERROR": "Instance not found, use status to see options"})

    def test_49_broken_connection(self):
        # Simulate broken connection, confirm no response sent
        response = asyncio.run(self.broken_connection())
        self.assertEqual(response, None)

    @cpython_only
    def test_50_connection_timeout(self):
        from unittest.mock import patch
        # Simulate connection timeout while waiting for response, confirm correct error
        with patch('Api.asyncio.wait_for', side_effect=asyncio.TimeoutError):
            self.assertEqual(self.send_command(['status']), "Error: Timed out waiting for response")

    def test_51_set_log_level(self):
        # Confirm module does not exist
        self.assertFalse('log_level.py' in os.listdir())

        # Call with invalid log level, confirm error
        response = self.send_command(['set_log_level', 'EVERYTHING'])
        self.assertEqual(response, {
            "ERROR": "Unsupported log level",
            "options": list(logging._nameToLevel.keys())
        })

        # Call with valid log level, confirm response
        response = self.send_command(['set_log_level', 'DEBUG'])
        self.assertEqual(
            response,
            {"Success": "Log level set (takes effect after reboot)"}
        )

        # Confirm module created on disk with correct contents
        self.assertTrue('log_level.py' in os.listdir())
        with open('log_level.py', 'r') as file:
            contents = file.read()
            self.assertEqual(
                contents,
                "LOG_LEVEL = 'DEBUG'"
            )

    # Original bug: Some device and sensor classes have attributes containing class objects, which
    # cannot be json-serialized. These are supposed to be deleted or replaced with string
    # representations when building get_attributes response. Earlier versions of API failed to do
    # this for some classes, breaking get_attributes and resulting in an "unable to decode" error.
    def test_52_regression_get_attributes(self):
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
                'schedule': {},
                'default_rule': 'enabled',
                'scheduled_rule': 'enabled',
                'current_rule': 'enabled',
                'switch_closed': bool(Pin(19, Pin.IN, Pin.PULL_DOWN).value())
            }
        )

    # Original bug: enable_in and disable_in cast delay argument to float with no error handling,
    # leading to exceptions when invalid arguments were received. In production this could only
    # occur when argument was NaN, other types were rejected by client-side validation.
    def test_53_regression_enable_in_disable_in_invalid_arguments(self):
        # Confirm correct error for string argument
        response = self.send_command(['enable_in', 'sensor1', 'foo'])
        self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})
        response = self.send_command(['disable_in', 'sensor1', 'foo'])
        self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})

        # Confirm correct error for NaN argument
        response = self.send_command(['enable_in', 'sensor1', 'NaN'])
        self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})
        response = self.send_command(['disable_in', 'sensor1', 'NaN'])
        self.assertEqual(response, {"ERROR": "Delay argument must be int or float"})

    # Original bug: run_client had no error handling when decoding received JSON, leading to
    # uncaught ValueError. This occurred when testing the bug fixed above by sending NaN with
    # api_client, which parses it to float before encoding as JSON. NaN is supported in JSON
    # on cpython but not micropython. This lead to crash when micropython attempted to parse
    # JSON containing NaN (rather than "NaN" string). Should now catch and return error.
    def test_54_regression_received_invalid_json(self):
        # Micropython's json module cannot parse NaN
        response = self.send_command(['enable_in', 'sensor1', float('NaN')])
        self.assertEqual(response, {"ERROR": "Syntax error in received JSON"})

    # Original bug: increment_rule endpoint response was determined by checking the return
    # value of increment_rule method in bare conditional, assuming the method only returned
    # True and False. Method can also return error JSON, which was interpreted as success
    # resulting in success message instead of error.
    def test_55_regression_increment_rule_wrong_error(self):
        # Call with invalid argument, confirm correct error
        response = self.send_command(['increment_rule', 'sensor1', 'string'])
        self.assertEqual(response, {'ERROR': 'Invalid argument string'})

        # Call with NaN argument, confirm correct error
        response = self.send_command(['increment_rule', 'sensor1', float('NaN')])
        self.assertEqual(response, {"ERROR": "Syntax error in received JSON"})

    # Original bug: An uncaught exception within an endpoint would cause run_client to return
    # before releasing lock. The server continued listening for API calls but would hang
    # while waiting to acquire lock resulting in client-side timeout. Lock is now acquired
    # with context manager and automatically released if an exception occurs.
    @cpython_only
    def test_56_regression_fails_to_release_lock(self):
        # Call endpoint that raises uncaught exception, should time out
        response = self.send_command(['uncaught_exception'])
        self.assertEqual(response, "Error: Timed out waiting for response")

        # Call status endpoint, should succeed (this would hang + timeout prior to fix)
        response = self.send_command(['status'])
        self.assertIsInstance(response, dict)

    # Original bug: The set_rule endpoint used "if ... in" to check if the new rule contained
    # url-encoded forward slashes (detect fade rule) without casting the rule to string. This
    # resulted in "TypeError: 'int' object isn't iterable" if the new rule was an integer.
    def test_57_regression_set_rule_fails_if_rule_is_int(self):
        response = self.send_command(['set_rule', 'device1', 100])
        self.assertEqual(self.device1.current_rule, 100)
        self.assertEqual(response, {'device1': 100})

    # Must run last, lock in reboot coro blocks future API requests
    @cpython_only
    def test_999_reboot_endpoint(self):
        # Confirm reset not yet called
        reset.called = False
        self.assertFalse(reset.called)

        # Call reboot endpoint, confirm response, confirm reset called
        self.assertEqual(self.send_command(['reboot']), 'Rebooting')
        self.assertTrue(reset.called)
