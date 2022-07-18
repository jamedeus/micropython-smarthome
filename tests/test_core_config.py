from Config import Config
import unittest
import network
from machine import Pin, Timer
import time



class TestConfig(unittest.TestCase):

    def __dir__(self):
        return ["test_initialization", "test_wifi_connected", "test_indicator_led", "test_api_calls", "test_reboot_timer", "test_device_instantiation", "test_for_unexpected_devices", "test_sensor_instantiation", "test_for_unexpected_sensors", "test_group_instantiation", "test_for_unexpected_groups", "test_reload_timer", "test_find_method", "test_get_status_method", "test_rebuilding_queue"]

    def test_initialization(self):
        loaded_json = {'device1': {'max': 1023, 'min': '0', 'schedule': {'sunrise': 0, 'sunset': 32}, 'type': 'pwm', 'pin': 4, 'default_rule': 32}, 'wifi': {'ssid': 'jamnet', 'password': 'cjZY8PTa4ZQ6S83A'}, 'metadata': {'id': 'Upstairs bathroom', 'location': 'Under counter', 'floor': '2'}, 'sensor1': {'schedule': {'10:00': '5', '22:00': '5'}, 'pin': 15, 'targets': ['device1'], 'type': 'pir', 'default_rule': 5}}

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
        self.assertIsNotNone(self.config.sunrise)

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
