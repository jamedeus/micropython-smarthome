import time
import network
import unittest
from machine import Pin, Timer
import SoftwareTimer
from Config import Config, instantiate_hardware

loaded_json = {
    'wifi': {
        'ssid': 'jamnet',
        'password': 'cjZY8PTa4ZQ6S83A'
    },
    'metadata': {
        'id': 'Upstairs bathroom',
        'location': 'Under counter',
        'floor': '2',
        "schedule_keywords": {}
    },
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
        'max_bright': 1023,
        'min_bright': '0',
        'nickname': 'device1',
        'schedule': {
            'sunrise': 0,
            'sunset': 32
        },
        '_type': 'pwm',
        'pin': 4,
        'default_rule': 32
    }
}


# Takes config, undoes instantiate_peripherals, returns
# Used to instantiate various configs without repeating all steps
def reset_test_config(config):
    del config.devices
    del config.sensors
    del config.groups
    config.sensor_configs = {}
    config.device_configs = {}
    return config


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate class, skip setup to allow testing each step
        cls.config = Config(loaded_json, delay_setup=True)

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.config, Config)
        self.assertEqual(self.config.credentials, (loaded_json["wifi"]["ssid"], loaded_json["wifi"]["password"]))
        self.assertEqual(self.config.identifier, loaded_json["metadata"]["id"])
        self.assertEqual(self.config.location, loaded_json["metadata"]["location"])
        self.assertEqual(self.config.floor, loaded_json["metadata"]["floor"])
        self.assertEqual(self.config.schedule, {})
        self.assertEqual(self.config.schedule_keywords, {'sunrise': '00:00', 'sunset': '00:00'})
        self.assertEqual(self.config.gps, "")

        # Confirm intermediate instance config attributes
        self.assertEqual(len(self.config.sensor_configs), 1)
        self.assertEqual(len(self.config.device_configs), 1)
        self.assertEqual(self.config.sensor_configs['sensor1'], loaded_json['sensor1'])
        self.assertEqual(self.config.device_configs['device1'], loaded_json['device1'])

        # Confirm peripheral-related attributes not created (delay_setup)
        self.assertFalse("devices" in self.config.__dict__)
        self.assertFalse("sensors" in self.config.__dict__)
        self.assertFalse("groups" in self.config.__dict__)
        self.assertFalse("ir_blaster" in self.config.__dict__)

    def test_02_api_calls(self):
        # Confirm network is not connected
        wlan = network.WLAN()
        wlan.disconnect()
        while wlan.isconnected():
            continue
        self.assertFalse(network.WLAN().isconnected())

        # Run API calls, confirm connected successfully
        self.config.api_calls()
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
        # Run instantiate_peripherals method
        self.config.instantiate_peripherals()

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

        # Confirm group created correctly
        self.assertEqual(len(self.config.groups), 1)
        self.assertEqual(self.config.groups[0].targets[0], self.config.devices[0])
        self.assertEqual(self.config.groups[0].triggers[0], self.config.sensors[0])

        # Confirm current and sheduled rules are not set (determined by build_queue, hasn't run)
        self.assertEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, None)

        # Confirm config.schedule populated
        self.assertEqual(self.config.schedule, {'device1': {'sunrise': 0, 'sunset': 32}, 'sensor1': {}})

        # Should not be able to call instantiate_peripherals again
        with self.assertRaises(RuntimeError):
            self.config.instantiate_peripherals()

    def test_04_build_queue(self):
        # Run build_queue method
        self.config.build_queue()

        # Confirm current and scheduled rules set
        self.assertNotEqual(self.config.devices[0].current_rule, None)
        self.assertNotEqual(self.config.devices[0].current_rule, None)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5.0)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5.0)

        # Device should have rules in queue, sensor should have none (no schedule rules)
        self.assertGreaterEqual(len(self.config.devices[0].rule_queue), 1)
        self.assertEqual(len(self.config.sensors[0].rule_queue), 0)

    def test_05_start_reload_timer(self):
        # Confirm reload timer not in queue
        SoftwareTimer.timer.cancel("reload_schedule_rules")
        self.assertTrue("reload_schedule_rules" not in str(SoftwareTimer.timer.schedule))

        # Call method to start config_timer, confirm timer running
        self.config.start_reload_schedule_rules_timer()
        self.assertIn("reload_schedule_rules", str(SoftwareTimer.timer.schedule))

    def test_06_full_instantiation(self):
        # Instantiate without delay_setup arg, simulate real-world usage
        config = Config(loaded_json)

        # Confirm expected attributes
        self.assertIsInstance(config, Config)
        self.assertEqual(config.credentials, (loaded_json["wifi"]["ssid"], loaded_json["wifi"]["password"]))
        self.assertEqual(config.identifier, loaded_json["metadata"]["id"])
        self.assertEqual(config.location, loaded_json["metadata"]["location"])
        self.assertEqual(config.floor, loaded_json["metadata"]["floor"])
        self.assertEqual(config.gps, "")

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

    def test_07_find_method(self):
        # Pass device and sensor IDs, should return instance
        self.assertEqual(self.config.find("device1"), self.config.devices[0])
        self.assertEqual(self.config.find("sensor1"), self.config.sensors[0])

        # Should return False if argument doesn't exist
        self.assertFalse(self.config.find("device99"))
        self.assertFalse(self.config.find("sensor99"))
        self.assertFalse(self.config.find("waldo"))

    def test_08_get_status_method(self):
        # Should return dict of current status info
        self.assertEqual(type(self.config.get_status()), dict)

    def test_09_rebuilding_queue(self):
        # Get current rule queue before rebuilding
        device_before = self.config.devices[0].rule_queue
        sensor_before = self.config.sensors[0].rule_queue

        self.config.build_queue()

        # Confirm duplicate rules were not added
        self.assertEqual(device_before, self.config.devices[0].rule_queue)
        self.assertEqual(sensor_before, self.config.sensors[0].rule_queue)

    def test_10_default_rule(self):
        # Regression test for sensor with no schedule rules receiving default_rule of last device/sensor in config
        self.assertEqual(self.config.sensors[0].current_rule, 5)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5)

    def test_11_instantiate_hardware_errors(self):
        # Should raise ValueError when attempting to instantiate unknown type
        # assertRaises fails for some reason, this approach seems reliable
        try:
            instantiate_hardware('device1', _type='invalid')
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except ValueError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            instantiate_hardware('sensor1', _type='invalid')
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except ValueError:
            # Should raise exception, test passed
            self.assertTrue(True)

        try:
            instantiate_hardware('ir_blaster')
            # Should not make it to this line, test failed
            self.assertFalse(True)
        except ValueError:
            # Should raise exception, test passed
            self.assertTrue(True)

    def test_12_invalid_types_in_config(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device and sensor configs with invalid _type
        self.config.sensor_configs = {
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
        self.config.device_configs = {
            "device1": {
                "_type": "invalid",
                "nickname": "device1",
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm neither instance instantiated
        self.assertEqual(len(self.config.devices), 0)
        self.assertEqual(len(self.config.sensors), 0)

    # Confirm device current_rule is set to schedule_rule when valid
    def test_13_valid_scheduled_rule(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with valid schedule rule, should be used as current_rule
        self.config.device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': 50,
                'min_bright': 0,
                'max_bright': 1023,
                'schedule': {
                    '10:00': 50
                }
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm scheduled rule set for both current_rule and scheduled_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm device current_rule falls back to default_rule when scheduled invalid
    def test_14_invalid_scheduled_rule_valid_default_rule(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Scheduled rule is NOT valid, default_rule should be set for current_rule and scheduled_rule instead

        # Add device with invalid schedule rule, valid default_rule
        # Should set default_rule for both current and scheduled rule
        self.config.device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': 50,
                'min_bright': 0,
                'max_bright': 1023,
                'schedule': {
                    '10:00': '9999',
                    'later': '999'
                }
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm current and schedule rules match default_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm handles devices with all rules invalid by disabling and
    # setting "disabled" for current, scheduled, and default rule
    def test_15_all_invalid_rules(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with invalid default and schedule rules
        # Should be disabled with all rule set to "disabled"
        self.config.device_configs = {
            'device1': {
                '_type': 'mosfet',
                'nickname': 'test',
                'pin': 4,
                'default_rule': '9999',
                'schedule': {
                    '10:00': '9999'
                }
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm disabled, all rules disabled
        self.assertFalse(self.config.devices[0].enabled)
        self.assertEqual(self.config.devices[0].current_rule, 'disabled')
        self.assertEqual(self.config.devices[0].scheduled_rule, 'disabled')
        self.assertEqual(self.config.devices[0].default_rule, 'disabled')

    # Confirm devices with no schedule rules fall back to default_rule
    def test_16_no_schedule_rules(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add device with no schedule rules, should fall back to default_rule
        self.config.device_configs = {
            'device1': {
                '_type': 'pwm',
                'nickname': 'test',
                'pin': 4,
                'default_rule': '50',
                'min_bright': 0,
                'max_bright': 1023,
                'schedule': {}
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm current_rule and schedule_rule set to default_rule
        self.assertEqual(self.config.devices[0].current_rule, 50)
        self.assertEqual(self.config.devices[0].scheduled_rule, 50)
        self.assertTrue(self.config.devices[0].enabled)

    # Confirm handles sensor with no schedule rules and invalid default_rule by
    # disabling and setting "disabled" for current, schedule and default rules
    def test_17_no_schedule_rules_invalid_default_rule(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add sensor with invalid default_rule and no schedule rules
        # Instance should be disabled with all rules set to "disabled"
        self.config.sensor_configs = {
            'sensor1': {
                '_type': 'si7021',
                'nickname': 'test',
                'mode': 'cool',
                'tolerance': 5,
                'default_rule': '9999',
                'schedule': {},
                'targets': []
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm instance disabled, all rules disabled
        self.assertFalse(self.config.sensors[0].enabled)
        self.assertEqual(self.config.sensors[0].current_rule, 'disabled')
        self.assertEqual(self.config.sensors[0].scheduled_rule, 'disabled')
        self.assertEqual(self.config.sensors[0].default_rule, 'disabled')

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_18_regression_instantiate_with_invalid_default_rule(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add PWM device with invalid default rule, valid mosfet, valid motion sensor
        # PWM should fail to instantiate, others should instantiate
        self.config.device_configs = {
            "device1": {
                "_type": "pwm",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "min_bright": 0,
                "max_bright": 1023,
                "default_rule": "enabled",
                "schedule": {
                    "sunrise": "0",
                    "sunset": "enabled"
                }
            },
            "device2": {
                "_type": "mosfet",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config.sensor_configs = {
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
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm only the mosfet sensor instantiated
        self.assertEqual(len(self.config.devices), 1)
        self.assertEqual(self.config.devices[0]._type, "mosfet")
        # Confirm sensor only has 1 target (mosfet)
        self.assertEqual(len(self.config.sensors[0].targets), 1)
        self.assertEqual(self.config.sensors[0].targets[0]._type, "mosfet")

    # Original bug: Some sensor types would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_19_regression_instantiate_with_invalid_default_rule_sensor(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add sensor with invalid default_rule, should fail to instantiate
        self.config.sensor_configs = {
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
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Confirm no sensors (failed to instantiate)
        self.assertEqual(len(self.config.sensors), 0)

    # Original bug: desktop_trigger was broken by 9aa2a7f4, which instantiated sensors with their
    # config parameters (including target ID list), then replaced instance.targets with a list of
    # device instances. Desktop_trigger __init__ expects targets list to contain device instances
    # and checks their _type, raising an exception when the list contained strings.
    def test_20_regression_instantiate_with_desktop_trigger(self):
        # Undo instantiate_peripherals
        self.config = reset_test_config(self.config)

        # Add desktop_trigger targeting desktop_target
        self.config.sensor_configs = {
            "sensor1": {
                "_type": "desktop",
                "nickname": "Computer Screen",
                "ip": "192.168.1.123",
                "default_rule": "enabled",
                "schedule": {},
                "targets": [
                    "device1"
                ]
            }
        }
        self.config.device_configs = {
            "device1": {
                "_type": "mosfet",
                "nickname": "Countertop LEDs",
                "pin": 19,
                "default_rule": "enabled",
                "schedule": {}
            }
        }
        self.config.instantiate_peripherals()
        self.config.build_queue()

        # Should have 1 sensor (instantiated successfully)
        self.assertEqual(len(self.config.sensors), 1)

    def test_21_reload_schedule_rules(self):
        # Used to detect which mock methods called
        self.api_calls_called = False
        self.build_queue_called = False

        # Mock both methods called by reload_schedule_rules
        def mock_api_calls(arg=None):
            self.api_calls_called = True

        def mock_build_queue(arg=None):
            self.build_queue_called = True

        # Overwrite instance methods with mocks
        self.config.api_calls = mock_api_calls
        self.config.build_queue = mock_build_queue

        # Call reload_schedule_rules, confirm methods called
        self.config.reload_schedule_rules()
        self.assertTrue(self.api_calls_called)
        self.assertTrue(self.build_queue_called)
