import time
import network
import unittest
from machine import Pin, Timer
from Config import Config


class TestConfig(unittest.TestCase):

    def __dir__(self):
        return [
            "test_initialization",
            "test_wifi_connected",
            "test_indicator_led",
            "test_api_calls",
            "test_reboot_timer",
            "test_device_instantiation",
            "test_for_unexpected_devices",
            "test_sensor_instantiation",
            "test_for_unexpected_sensors",
            "test_group_instantiation",
            "test_for_unexpected_groups",
            "test_reload_timer",
            "test_find_method",
            "test_get_status_method",
            "test_rebuilding_queue",
            "test_valid_scheduled_rule",
            "test_invalid_scheduled_rule_valid_default_rule",
            "test_all_invalid_rules",
            "test_no_schedule_rules",
            "test_no_schedule_rules_invalid_default_rule",
            "test_regression_instantiate_with_invalid_default_rule",
            "test_regression_instantiate_with_invalid_default_rule_sensor"
        ]

    def test_initialization(self):
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
                'sensor_type': 'pir',
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
                'device_type': 'pwm',
                'pin': 4,
                'default_rule': 32
            }
        }

        self.config = Config(loaded_json)
        self.assertIsInstance(self.config, Config)

    def test_wifi_connected(self):
        # Check if network connected successfully
        self.assertTrue(network.WLAN().isconnected())

    def test_indicator_led(self):
        # Make sure LED went off
        led = Pin(2, Pin.OUT)
        print(f"State = {led.value()}")
        self.assertEqual(led.value(), 0)

    def test_api_calls(self):
        # Confirm API call succeeded
        self.assertIsNotNone(self.config.schedule_keywords['sunrise'])

    def test_reboot_timer(self):
        # Confirm reboot_timer stopped by reading remaining time twice with delay in between
        reboot_timer = Timer(2)
        first = reboot_timer.value()
        time.sleep_ms(1)
        second = reboot_timer.value()
        self.assertEqual(first, second)

    def test_device_instantiation(self):
        # Confirm correct devices were instantiated
        self.assertEqual(len(self.config.devices), 1)
        self.assertEqual(self.config.devices[0].device_type, 'pwm')
        self.assertTrue(self.config.devices[0].enabled)
        self.assertEqual(self.config.devices[0].triggered_by[0], self.config.sensors[0])
        self.assertEqual(self.config.devices[0].default_rule, 32)

    def test_for_unexpected_devices(self):
        # Should only be one device
        with self.assertRaises(IndexError):
            self.config.devices[1].device_type

    def test_sensor_instantiation(self):
        # Confirm correct sensors were instantiated
        self.assertEqual(len(self.config.sensors), 1)
        self.assertEqual(self.config.sensors[0].sensor_type, 'pir')
        self.assertTrue(self.config.sensors[0].enabled)
        self.assertEqual(self.config.sensors[0].targets[0], self.config.devices[0])
        self.assertEqual(self.config.sensors[0].default_rule, 5)

    def test_for_unexpected_sensors(self):
        # Should only be one sensor
        with self.assertRaises(IndexError):
            self.config.sensors[1].sensor_type

    def test_group_instantiation(self):
        # Confirm group created correctly
        self.assertEqual(len(self.config.groups), 1)
        self.assertEqual(self.config.groups[0].targets[0], self.config.devices[0])
        self.assertEqual(self.config.groups[0].triggers[0], self.config.sensors[0])

    def test_for_unexpected_groups(self):
        # Should only be one group
        with self.assertRaises(IndexError):
            self.config.groups[1]

    def test_reload_timer(self):
        # Confirm reload_config timer is running
        self.config_timer = Timer(1)
        first = self.config_timer.value()
        time.sleep_ms(1)
        second = self.config_timer.value()
        self.assertNotEqual(first, second)

    def test_find_method(self):
        self.assertEqual(self.config.find("device1"), self.config.devices[0])

    def test_get_status_method(self):
        # Test get_status method
        self.assertEqual(type(self.config.get_status()), dict)

    def test_rebuilding_queue(self):
        # Get current rule queue before rebuilding
        device_before = self.config.devices[0].rule_queue
        sensor_before = self.config.sensors[0].rule_queue

        self.config.build_queue()

        # Confirm duplicate rules were not added
        self.assertEqual(device_before, self.config.devices[0].rule_queue)
        self.assertEqual(sensor_before, self.config.sensors[0].rule_queue)

    def test_default_rule(self):
        # Regression test for sensor with no schedule rules receiving default_rule of last device/sensor in config
        self.assertEqual(self.config.sensors[0].current_rule, 5)
        self.assertEqual(self.config.sensors[0].scheduled_rule, 5)

    ## Tests to confirm correct rule is set after instantiating device ##

    def test_valid_scheduled_rule(self):
        # Scheduled rule is valid, should be set for current_rule and scheduled_rule
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'location': 'test',
                    'floor': '0',
                    "schedule_keywords": {}
                },
                'wifi': {
                    'ssid': 'jamnet',
                    'password': 'cjZY8PTa4ZQ6S83A'
                },
                'device1': {
                    'device_type': 'pwm',
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
        )

        self.assertEqual(config.devices[0].current_rule, 50)
        self.assertEqual(config.devices[0].scheduled_rule, 50)
        self.assertTrue(config.devices[0].enabled)

    def test_invalid_scheduled_rule_valid_default_rule(self):
        # Scheduled rule is NOT valid, default_rule should be set for current_rule and scheduled_rule instead
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'location': 'test',
                    'floor': '0',
                    "schedule_keywords": {}
                },
                'wifi': {
                    'ssid': 'jamnet',
                    'password': 'cjZY8PTa4ZQ6S83A'
                },
                'device1': {
                    'device_type': 'pwm',
                    'nickname': 'test',
                    'pin': 4,
                    'default_rule': 50,
                    'min_bright': 0,
                    'max_bright': 1023,
                    'schedule': {
                        '10:00': '9999'
                    }
                }
            }
        )

        self.assertEqual(config.devices[0].current_rule, 50)
        self.assertEqual(config.devices[0].scheduled_rule, 50)
        self.assertTrue(config.devices[0].enabled)

    def test_all_invalid_rules(self):
        # All rules are invalid, instance should be disabled with all rules set to "disabled"
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'location': 'test',
                    'floor': '0',
                    "schedule_keywords": {}
                },
                'wifi': {
                    'ssid': 'jamnet',
                    'password': 'cjZY8PTa4ZQ6S83A'
                },
                'device1': {
                    'device_type': 'pwm',
                    'nickname': 'test',
                    'pin': 4,
                    'default_rule': '9999',
                    'min_bright': 0,
                    'max_bright': 1023,
                    'schedule': {
                        '10:00': '9999'
                    }
                }
            }
        )

        self.assertEqual(config.devices[0].current_rule, 'disabled')
        self.assertEqual(config.devices[0].scheduled_rule, 'disabled')
        self.assertEqual(config.devices[0].default_rule, 'disabled')
        self.assertFalse(config.devices[0].enabled)

    def test_no_schedule_rules(self):
        # No schedule rules are configured, should fall back to default_rule
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'location': 'test',
                    'floor': '0',
                    "schedule_keywords": {}
                },
                'wifi': {
                    'ssid': 'jamnet',
                    'password': 'cjZY8PTa4ZQ6S83A'
                },
                'device1': {
                    'device_type': 'pwm',
                    'nickname': 'test',
                    'pin': 4,
                    'default_rule': '50',
                    'min_bright': 0,
                    'max_bright': 1023,
                    'schedule': {}
                }
            }
        )

        self.assertEqual(config.devices[0].current_rule, 50)
        self.assertEqual(config.devices[0].scheduled_rule, 50)
        self.assertTrue(config.devices[0].enabled)

    def test_no_schedule_rules_invalid_default_rule(self):
        # No schedule rules + invalid default_rule, instance should be disabled with all rules set to "disabled"
        config = Config(
            {
                'metadata': {
                    'id': 'test',
                    'location': 'test',
                    'floor': '0',
                    "schedule_keywords": {}
                },
                'wifi': {
                    'ssid': 'jamnet',
                    'password': 'cjZY8PTa4ZQ6S83A'
                },
                'device1': {
                    'device_type': 'pwm',
                    'nickname': 'test',
                    'pin': 4,
                    'default_rule': '9999',
                    'min_bright': 0,
                    'max_bright': 1023,
                    'schedule': {}
                }
            }
        )

        self.assertEqual(config.devices[0].current_rule, 'disabled')
        self.assertEqual(config.devices[0].scheduled_rule, 'disabled')
        self.assertEqual(config.devices[0].default_rule, 'disabled')
        self.assertFalse(config.devices[0].enabled)

    # Original bug: Devices that use current_rule in send() payload crashed if default_rule was "enabled" or "disabled"
    # and current_rule changed to "enabled" (string rule instead of int in payload). These classes now raise exception
    # in init method to prevent this. It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_instantiate_with_invalid_default_rule(self):
        config = Config(
            {
                "metadata": {
                    "id": "Upstairs Bathroom",
                    "location": "Under counter",
                    "floor": "2",
                    "schedule_keywords": {}
                },
                "wifi": {
                    "ssid": "jamnet",
                    "password": "cjZY8PTa4ZQ6S83A"
                },
                "sensor1": {
                    "sensor_type": "pir",
                    "nickname": "Motion Sensor",
                    "pin": 15,
                    "default_rule": 5,
                    "schedule": {
                        "10:00": "5",
                        "22:00": "5"
                    },
                    "targets": [
                        "device1"
                    ]
                },
                "device1": {
                    "device_type": "pwm",
                    "nickname": "Countertop LEDs",
                    "pin": 19,
                    "min_bright": 0,
                    "max_bright": 1023,
                    "default_rule": "enabled",
                    "schedule": {
                        "sunrise": "0",
                        "sunset": "enabled"
                    }
                }
            }
        )

        # Should have no device instances
        self.assertEqual(len(config.devices), 0)
        # Sensor should have no targets
        self.assertEqual(len(config.sensors[0].targets), 0)

    # Original bug: Some sensor types would crash or behave unexpectedly if default_rule was "enabled" or "disabled"
    # in various situations. These classes now raise exception in init method to prevent this.
    # It should no longer be possible to instantiate with invalid default_rule.
    def test_regression_instantiate_with_invalid_default_rule_sensor(self):
        config = Config(
            {
                "metadata": {
                    "id": "Upstairs Bathroom",
                    "location": "Under counter",
                    "floor": "2",
                    "schedule_keywords": {}
                },
                "wifi": {
                    "ssid": "jamnet",
                    "password": "cjZY8PTa4ZQ6S83A"
                },
                "sensor1": {
                    "sensor_type": "pir",
                    "nickname": "Motion Sensor",
                    "pin": 15,
                    "default_rule": "enabled",
                    "schedule": {
                        "10:00": "5",
                        "22:00": "5"
                    },
                    "targets": [
                        "device1"
                    ]
                },
                "device1": {
                    "device_type": "pwm",
                    "nickname": "Countertop LEDs",
                    "pin": 19,
                    "min_bright": 0,
                    "max_bright": 1023,
                    "default_rule": 512,
                    "schedule": {
                        "sunrise": "0",
                        "sunset": "enabled"
                    }
                }
            }
        )

        # Should have no sensor instances
        self.assertEqual(len(config.sensors), 0)
