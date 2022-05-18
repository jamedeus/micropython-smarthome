from Config import Config
import unittest
import network
from machine import Pin, Timer
import time



class TestConfig(unittest.TestCase):

    def test_initialization(self):
        loaded_json = {'device1': {'max': 1023, 'min': '0', 'schedule': {'sunrise': 0, 'sunset': 32}, 'type': 'pwm', 'pin': 4, 'default_rule': 32}, 'wifi': {'ssid': 'jamnet', 'password': 'cjZY8PTa4ZQ6S83A'}, 'metadata': {'id': 'Upstairs bathroom', 'location': 'Under counter', 'floor': '2'}, 'sensor1': {'schedule': {'10:00': '5', '22:00': '5'}, 'pin': 15, 'targets': ['device1'], 'type': 'pir', 'default_rule': 5}}

        config = Config(loaded_json)

        # Check if network connected successfully
        self.assertTrue(network.WLAN().isconnected())

        # Make sure LED went off
        led = Pin(2, Pin.OUT)
        print(f"State = {led.value()}")
        self.assertEqual(led.value(), 0)

        # Confirm API call succeeded
        self.assertIsNotNone(config.sunrise)

        # Confirm reboot_timer stopped by reading remaining time twice with delay in between
        reboot_timer = Timer(2)
        first = reboot_timer.value()
        time.sleep_ms(1)
        second = reboot_timer.value()
        self.assertEqual(first, second)

        # Confirm correct devices were instantiated
        self.assertEqual(len(config.devices), 1)
        self.assertEqual(config.devices[0].device_type, 'pwm')
        self.assertTrue(config.devices[0].enabled)
        self.assertEqual(config.devices[0].triggered_by[0], config.sensors[0])

        # Confirm correct sensors were instantiated
        self.assertEqual(len(config.sensors), 1)
        self.assertEqual(config.sensors[0].sensor_type, 'pir')
        self.assertTrue(config.sensors[0].enabled)
        self.assertEqual(config.sensors[0].targets[0], config.devices[0])

        # Confirm group created correctly
        self.assertEqual(len(config.groups), 1)
        self.assertEqual(config.groups["group1"]["targets"][0], config.devices[0])
        self.assertEqual(config.groups["group1"]["triggers"][0], config.sensors[0])

        # Confirm reload_config timer is running
        config_timer = Timer(1)
        first = config_timer.value()
        time.sleep_ms(1)
        second = config_timer.value()
        self.assertNotEqual(first, second)

        # Test find method
        self.assertEqual(config.find("device1"), config.devices[0])

        # Test get_status method
        self.assertEqual(type(config.get_status()), dict)
