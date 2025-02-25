import sys
import json
import time
import asyncio
import network
import unittest
from machine import Pin, Timer
import app_context
from cpython_only import cpython_only
from Config import Config, instantiate_hardware

# Read mock API receiver address
with open('config.json', 'r') as file:
    test_config = json.load(file)

loaded_json = {
    'metadata': {
        'id': 'Upstairs bathroom',
        'location': 'Under counter',
        'floor': '2'
    },
    'schedule_keywords': {},
    'sensor1': {
        'nickname': 'sensor1',
        'schedule': {},
        'pin': 15,
        'targets': [
            'device1'
        ],
        '_type': 'pir',
        'default_rule': 5
    },
    'device1': {
        'max_rule': 1023,
        'min_rule': '0',
        'nickname': 'device1',
        'schedule': {
            'sunrise': 0,
            'sunset': 32,
            '01:00': 8,
        },
        '_type': 'pwm',
        'pin': 4,
        'default_rule': 32
    }
}


# Takes config, undoes _instantiate_peripherals, returns
# Used to instantiate various configs without repeating all steps
def reset_test_config(config):
    config.devices = []
    config.sensors = []
    config.groups = []
    config._sensor_configs = {}
    config._device_configs = {}
    return config


class TestConfig(unittest.TestCase):

    # Used to yield so SoftwareTimer create/cancel tasks can run
    async def sleep(self, ms):
        await asyncio.sleep_ms(ms)

    @classmethod
    def setUpClass(cls):
        # Instantiate class, skip setup to allow testing each step
        cls.config = Config(loaded_json, delay_setup=True)

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.config, Config)
        self.assertEqual(self.config._metadata["id"], loaded_json["metadata"]["id"])
        self.assertEqual(self.config._metadata["location"], loaded_json["metadata"]["location"])
        self.assertEqual(self.config._metadata["floor"], loaded_json["metadata"]["floor"])
        self.assertEqual(self.config.schedule_keywords, {'sunrise': '00:00', 'sunset': '00:00'})
        self.assertTrue("gps" not in self.config._metadata)

        # Confirm intermediate instance config attributes
        self.assertEqual(len(self.config._sensor_configs), 1)
        self.assertEqual(len(self.config._device_configs), 1)
        self.assertEqual(self.config._sensor_configs['sensor1'], loaded_json['sensor1'])
        self.assertEqual(self.config._device_configs['device1'], loaded_json['device1'])

        # Confirm peripheral not instantiated yet (delay_setup)
        self.assertEqual(self.config.devices, [])
        self.assertEqual(self.config.sensors, [])
        self.assertEqual(self.config.groups, [])
        self.assertEqual(self.config.ir_blaster, None)

    def test_02_api_calls(self):
        # Confirm network is not connected
        wlan = network.WLAN()
        wlan.disconnect()
        while wlan.isconnected():
            continue
        self.assertFalse(network.WLAN().isconnected())

        # Run API calls, confirm connected successfully
        self.config._api_calls()
        self.assertTrue(network.WLAN().isconnected())

        # Confirm sunrise + sunset times set
        self.assertNotEqual(self.config.schedule_keywords["sunrise"], "00:00")
        self.assertNotEqual(self.config.schedule_keywords["sunset"], "00:00")

        # Confirm LED turned off after calls complete complete
        led = Pin(2, Pin.OUT)
        self.assertEqual(led.value(), 0)

        # Confirm reboot_timer stopped by reading remaining time twice with delay in between
        reboot_timer = Timer(2)
        first = reboot_timer.value()
        time.sleep_ms(1)
        second = reboot_timer.value()
        self.assertEqual(first, second)

    def test_03_instantiate_peripherals(self):
        # Run _instantiate_peripherals method
        self.config._instantiate_peripherals()

        # Confirm correct devices were instantiated
        self.assertEqual(len(self.config.devices), 1)
        self.assertEqual(self.config.devices[0]._type, 'pwm')
        self.assertTrue(self.config.devices[0].enabled)
        self.assertEqual(self.config.devices[0].triggered_by[0], self.config.sensors[0])
        self.assertEqual(self.config.devices[0].default_rule, 32)

        # Confirm correct sensors were instantiated
        self.assertEqual(len(self.config.sensors), 1)
        self.assertEqual(self.config.sensors[0]._type, 'pir')
        self.assertTrue(self.config.sensors[0].enabled)
        self.assertEqual(self.config.sensors[0].targets[0], self.config.devices[0])
        self.assertEqual(self.config.sensors[0].default_rule, 5)

        # Confirm current and scheduled rules are not set (determined by _build_queue, hasn't run)
        self.assertEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, None)

        # Should not be able to call _instantiate_peripherals again
        with self.assertRaises(RuntimeError):
            self.config._instantiate_peripherals()

    def test_04_start_reload_timer(self):
        # Confirm reload timer not in queue
        app_context.timer_instance.cancel("reload_schedule_rules")
        # Yield to let cancel coroutine run
        asyncio.run(self.sleep(10))
        self.assertTrue("reload_schedule_rules" not in str(app_context.timer_instance.schedule))

        # Call method to start config_timer, yield to let create coroutine run
        self.config._start_reload_schedule_rules_timer()
        asyncio.run(self.sleep(10))
        # Confirm timer running
        self.assertIn("reload_schedule_rules", str(app_context.timer_instance.schedule))

    def test_05_build_queue(self):
        # Confirm no schedule rule timers in SoftwareTimer queue
        app_context.timer_instance.cancel('scheduler')
        asyncio.run(self.sleep(10))
        rules = [time for time, rule in app_context.timer_instance.schedule.items()
                 if rule[0] == "scheduler"]
        self.assertEqual(len(rules), 0)

        # Run _build_queue method
        self.config._build_queue()
        # Yield to let SoftwareTimer coroutine create timers
        asyncio.run(self.sleep(10))

        # Confirm current and scheduled rules set
        self.assertNotEqual(self.config.devices[0].current_rule, None)
        self.assertNotEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5.0)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5.0)

        # Device should have at least 1 rule in queue (depends on time of day)
        self.assertGreaterEqual(len(self.config.devices[0].rule_queue), 1)
        # Should always contain 1:00 am rule (adds for tomorrow if expired today)
        self.assertTrue(8 in self.config.devices[0].rule_queue)
        # Sensor should empty queue (no schedule rules)
        self.assertEqual(self.config.sensors[0].rule_queue, [])

        # Confirm schedule rule timers were added to SoftwareTimer queue
        rules = [time for time, rule in app_context.timer_instance.schedule.items()
                 if rule[0] == "scheduler"]
        self.assertGreaterEqual(len(rules), 1)

    def test_06_build_groups(self):
        # Confirm no groups
        self.assertEqual(self.config.groups, [])

        # Call method, confirm correct group created
        self.config._build_groups()
        self.assertEqual(len(self.config.groups), 1)
        self.assertEqual(self.config.groups[0].targets[0], self.config.devices[0])
        self.assertEqual(self.config.groups[0].triggers[0], self.config.sensors[0])

        # Should not be able to call _build_groups again
        with self.assertRaises(RuntimeError):
            self.config._build_groups()

    def test_07_full_instantiation(self):
        # Add GPS coordinates to config
        loaded_json["metadata"]["gps"] = {"lat": "1.15156", "lon": "174.70617"}
        # Instantiate without delay_setup arg, simulate real-world usage
        config = Config(loaded_json)

        # Confirm expected attributes
        self.assertIsInstance(config, Config)
        self.assertEqual(config._metadata["id"], loaded_json["metadata"]["id"])
        self.assertEqual(config._metadata["location"], loaded_json["metadata"]["location"])
        self.assertEqual(config._metadata["floor"], loaded_json["metadata"]["floor"])
        self.assertEqual(config._metadata["gps"], {"lat": "1.15156", "lon": "174.70617"})

        # Confirm connected to wifi successfully, led turned off
        self.assertTrue(network.WLAN().isconnected())
        led = Pin(2, Pin.OUT)
        self.assertEqual(led.value(), 0)

        # Confirm sunrise and sunset timestamps were set
        self.assertEqual(len(config.schedule_keywords), 2)
        self.assertNotEqual(config.schedule_keywords["sunrise"], "00:00")
        self.assertNotEqual(config.schedule_keywords["sunset"], "00:00")

        # Confirm reboot_timer stopped by reading remaining time twice with delay in between
        reboot_timer = Timer(2)
        first = reboot_timer.value()
        time.sleep_ms(1)
        second = reboot_timer.value()
        self.assertEqual(first, second)

        # Confirm instantiated correct instances
        self.assertEqual(len(config.devices), 1)
        self.assertEqual(len(config.sensors), 1)
        self.assertEqual(len(config.groups), 1)

        # Confirm current and scheduled rules set
        self.assertNotEqual(config.devices[0].current_rule, None)
        self.assertNotEqual(config.devices[0].current_rule, None)
        self.assertEqual(config.sensors[0].scheduled_rule, 5.0)
        self.assertEqual(config.sensors[0].scheduled_rule, 5.0)

        # Device should have rules in queue, sensor should have none (no schedule rules)
        self.assertGreaterEqual(len(config.devices[0].rule_queue), 1)
        self.assertEqual(len(config.sensors[0].rule_queue), 0)

    def test_08_find_method(self):
        # Pass device and sensor IDs, should return instance
        self.assertEqual(self.config.find("device1"), self.config.devices[0])
        self.assertEqual(self.config.find("sensor1"), self.config.sensors[0])

        # Should return False if argument doesn't exist
        self.assertFalse(self.config.find("device99"))
        self.assertFalse(self.config.find("sensor99"))
        self.assertFalse(self.config.find("waldo"))

    def test_09_get_status_method(self):
        # Should return dict of current status info
        self.assertEqual(type(self.config.get_status()), dict)

    # TODO different results on micropython than in test env
    def test_10_rebuilding_queue(self):
        # Get current rule queue before rebuilding
        device_before = self.config.devices[0].rule_queue
        sensor_before = self.config.sensors[0].rule_queue

        self.config._build_queue()

        # Confirm duplicate rules were not added
        self.assertEqual(device_before, self.config.devices[0].rule_queue)
        self.assertEqual(sensor_before, self.config.sensors[0].rule_queue)

    def test_11_default_rule(self):
        # Regression test for sensor with no schedule rules receiving default_rule of last device/sensor in config
        self.assertEqual(self.config.sensors[0].current_rule, 5)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5)

    def test_12_instantiate_hardware_errors(self):
        # Should raise ValueError when attempting to instantiate unknown type
        with self.assertRaises(ValueError):
            instantiate_hardware('device1', _type='invalid')

        with self.assertRaises(ValueError):
            instantiate_hardware('sensor1', _type='invalid')

        with self.assertRaises(ValueError):
            instantiate_hardware('ir_blaster')

    def test_13_invalid_types_in_config(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device and sensor configs with invalid _type
        self.config._sensor_configs = {
            "sensor1": {
                "_type": "fake",
                "nickname": "sensor1",
                "default_rule": "enabled",
                "schedule": {},
                "targets": [
                    "device1"
                ]
            }
        }
        self.config._device_configs = {
            "device1": {
                "_type": "invalid",
                "nickname": "device1",
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm neither instance instantiated
        self.assertEqual(len(self.config.devices), 0)
        self.assertEqual(len(self.config.sensors), 0)

    # Confirm device current_rule is set to schedule_rule when valid
    def test_14_valid_scheduled_rule(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with valid schedule rule, should be used as current_rule
        self.config._device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': 50,
                'min_rule': 0,
                'max_rule': 1023,
                'schedule': {
                    '10:00': 50
                }
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm scheduled rule set for both current_rule and scheduled_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm device current_rule falls back to default_rule when scheduled invalid
    def test_15_invalid_scheduled_rule_valid_default_rule(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Scheduled rule is NOT valid, default_rule should be set for current_rule and scheduled_rule instead

        # Add device with invalid schedule rule, valid default_rule
        # Should set default_rule for both current and scheduled rule
        self.config._device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': 50,
                'min_rule': 0,
                'max_rule': 1023,
                'schedule': {
                    '10:00': '9999',
                    'later': '999'
                }
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm current and schedule rules match default_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm handles devices with all rules invalid by disabling and
    # setting "disabled" for current, scheduled, and default rule
    def test_16_all_invalid_rules(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with invalid default and schedule rules
        # Should be disabled with all rule set to "disabled"
        self.config._device_configs = {
            'device1': {
                '_type': 'relay',
                'nickname': 'test',
                'pin': 4,
                'default_rule': '9999',
                'schedule': {
                    '10:00': '9999'
                }
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm disabled, all rules disabled
        self.assertFalse(self.config.devices[0].enabled)
        self.assertEqual(self.config.devices[0].current_rule, 'disabled')
        self.assertEqual(self.config.devices[0].scheduled_rule, 'disabled')
        self.assertEqual(self.config.devices[0].default_rule, 'disabled')

    # Confirm devices with no schedule rules fall back to default_rule
    def test_17_no_schedule_rules(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with no schedule rules, should fall back to default_rule
        self.config._device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': '50',
                'min_rule': 0,
                'max_rule': 1023,
                'schedule': {}
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm current_rule and schedule_rule set to default_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm handles sensor with no schedule rules and invalid default_rule by
    # disabling and setting "disabled" for current, schedule and default rules
    def test_18_no_schedule_rules_invalid_default_rule(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add sensor with invalid default_rule and no schedule rules
        # Instance should be disabled with all rules set to "disabled"
        self.config._sensor_configs = {
            'sensor1': {
                '_type': 'si7021',
                'nickname': 'test',
                'mode': 'cool',
                'tolerance': 5,
                'units': 'fahrenheit',
                'default_rule': '9999',
                'schedule': {},
                'targets': []
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm instance disabled, all rules disabled
        self.assertFalse(self.config.sensors[0].enabled)
        self.assertEqual(self.config.sensors[0].current_rule, 'disabled')
        self.assertEqual(self.config.sensors[0].scheduled_rule, 'disabled')
        self.assertEqual(self.config.sensors[0].default_rule, 'disabled')

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_19_regression_instantiate_with_invalid_default_rule(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add PWM device with invalid default rule, valid relay, valid motion sensor
        # PWM should fail to instantiate, others should instantiate
        self.config._device_configs = {
            "device1": {
                "_type": "pwm",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "min_rule": 0,
                "max_rule": 1023,
                "default_rule": "enabled",
                "schedule": {
                    "sunrise": "0",
                    "sunset": "enabled"
                }
            },
            "device2": {
                "_type": "relay",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config._sensor_configs = {
            "sensor1": {
                "_type": "pir",
                "nickname": "Motion Sensor",
                "pin": 15,
                "default_rule": 5,
                "schedule": {},
                "targets": [
                    "device1",
                    "device2"
                ]
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm only the relay sensor instantiated
        self.assertEqual(len(self.config.devices), 1)
        self.assertEqual(self.config.devices[0]._type, "relay")
        # Confirm sensor only has 1 target (relay)
        self.assertEqual(len(self.config.sensors[0].targets), 1)
        self.assertEqual(self.config.sensors[0].targets[0]._type, "relay")

    # Original bug: Some sensor types would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_20_regression_instantiate_with_invalid_default_rule_sensor(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add sensor with invalid default_rule, should fail to instantiate
        self.config._sensor_configs = {
            "sensor1": {
                "_type": "pir",
                "nickname": "Motion Sensor",
                "pin": 15,
                "default_rule": "enabled",
                "schedule": {
                    "10:00": "5",
                    "22:00": "5"
                },
                "targets": []
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Confirm no sensors (failed to instantiate)
        self.assertEqual(len(self.config.sensors), 0)

    # Original bug: desktop_trigger was broken by 9aa2a7f4, which instantiated sensors with their
    # config parameters (including target ID list), then replaced instance.targets with a list of
    # device instances. DesktopTrigger __init__ expects targets list to contain device instances
    # and checks their _type, raising an exception when the list contained strings.
    def test_21_regression_instantiate_with_desktop_trigger(self):
        # Undo _instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add desktop_trigger targeting desktop_target
        self.config._sensor_configs = {
            "sensor1": {
                "_type": "desktop",
                "nickname": "Computer Screen",
                "ip": test_config["mock_receiver"]["ip"],
                "port": test_config["mock_receiver"]["port"],
                "default_rule": "enabled",
                "mode": "screen",
                "schedule": {},
                "targets": [
                    "device1"
                ]
            }
        }
        self.config._device_configs = {
            "device1": {
                "_type": "relay",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config._instantiate_peripherals()
        self.config._build_queue()
        self.config._build_groups()

        # Should have 1 sensor (instantiated successfully)
        self.assertEqual(len(self.config.sensors), 1)

        # Kill monitor task next time loop yields, avoid accumulating tasks
        self.config.sensors[0].disable()

    def test_22_reload_schedule_rules(self):
        # Used to detect which mock methods called
        self.api_calls_called = False
        self._build_queue_called = False

        # Mock both methods called by reload_schedule_rules
        def mock_api_calls(arg=None):
            self.api_calls_called = True

        def mock__build_queue(arg=None):
            self._build_queue_called = True

        # Overwrite instance methods with mocks
        self.config._api_calls = mock_api_calls
        self.config._build_queue = mock__build_queue

        # Call reload_schedule_rules, confirm methods called
        self.config.reload_schedule_rules()
        self.assertTrue(self.api_calls_called)
        self.assertTrue(self._build_queue_called)

    @cpython_only
    def test_23_failed_api_calls(self):
        # Create mock reboot function that raises custom exception
        class MockRebootCalled(Exception):
            pass

        def mock_reboot():
            raise MockRebootCalled()

        # Apply mock
        import util
        util.reboot = mock_reboot

        # Mock API key to simulate error response from API
        import api_keys
        api_keys.ipgeo_key = "invalid"

        # Remove Config from cache and re-import
        # Uses mocks from cache instead of actual api_key and reboot
        del sys.modules["Config"]
        from Config import Config

        # Simulate network error in API call, confirm error triggers reboot
        with self.assertRaises(MockRebootCalled):
            Config._api_calls(self.config)

        # Create requests.get mock that raises OSError (failed connection)
        def mock_get(*args, **kwargs):
            raise OSError

        # Remove from cache, re-import, apply mocks
        del sys.modules["requests"]
        import requests
        requests.get = mock_get
        del sys.modules["Config"]
        from Config import Config

        # Call method, confirm error triggers reboot
        with self.assertRaises(MockRebootCalled):
            Config._api_calls(self.config)

    @cpython_only
    def test_24_regression_no_rules_expired_when_convert_rules_runs(self):
        '''Original bug: Config._convert_rules finds current_rule by iterating
        chronological schedule rules until the first non-expired rule is found
        (the expired rule before this is current rule). After 70a7f85a removed
        most duplicate rules it was possible for there to be no expired rules,
        which prevented the `current` variable from being set and resulted in
        an uncaught UnboundLocalError. For devices/sensors with no schedule
        rules between midnight and 3 am this happened every time the reload
        timer expired between 3 and 4 am.
        '''

        from unittest.mock import patch

        # Mock time methods to simulate running at 3:10 am on 2024-10-30
        # (crash occurred when reload rules timer expired, but not in day time)
        with patch('time.time', return_value=1730283000.0), \
             patch('time.localtime', return_value=(2024, 10, 30, 3, 10, 0, 2, 304, 1)):

            # Convert schedule with no expired rules (should not raise exception)
            epoch_rules = self.config._convert_rules({
                "23:00": "fade/32/7200",
                "06:00": "disabled",
                "18:00": "1023"
            })

            # Confirm that 23:00 (current_rule) is first even though timestamp
            # is last, confirm that other rules are in chronological order

            # Confirm that 23:00 rule is first (current rule), timestamps for
            # other rules are chronological (23:00 < sunrise < sunset)
            self.assertEqual(
                epoch_rules,
                {
                    1730354400.0: 'fade/32/7200',
                    1730268000.0: 'fade/32/7200',
                    1730293200.0: 'disabled',
                    1730336400.0: '1023'
                }
            )

    def test_25_regression_sensor_target_order_broke_group_matching(self):
        '''Original bug: Config._build_groups determines which sensors are part
        of the same group by comparing their targets attribute (list of device
        instances). If 2 sensors had identical targets but different order they
        would be incorrectly put in separate groups. This could happen if a web
        frontend user clicked sensor target checkboxes in a different order.
        '''

        # Instantiate a config with 2 sensors with identical targets but
        # non-identical order
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'floor': 1,
                    'location': 'unit tests'
                },
                'schedule_keywords': {},
                'sensor1': {
                    'nickname': 'sensor1',
                    'schedule': {},
                    'targets': [
                        'device1',
                        'device2'
                    ],
                    '_type': 'dummy',
                    'default_rule': 'on'
                },
                'sensor2': {
                    'nickname': 'sensor2',
                    'schedule': {},
                    'targets': [
                        'device2',
                        'device1'
                    ],
                    '_type': 'dummy',
                    'default_rule': 'on'
                },
                'device1': {
                    'nickname': 'device1',
                    'schedule': {},
                    '_type': 'relay',
                    'pin': 18,
                    'default_rule': 'enabled'
                },
                'device2': {
                    'nickname': 'device2',
                    'schedule': {},
                    '_type': 'relay',
                    'pin': 19,
                    'default_rule': 'enabled'
                }
            }
        )

        # Confirm both devices and sensors instantiated successfully
        self.assertEqual(len(config.devices), 2)
        self.assertEqual(len(config.sensors), 2)
        # Confirm all 4 instances are part of a single group
        self.assertEqual(len(config.groups), 1)
