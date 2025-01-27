import json
import asyncio
import unittest
from TasmotaRelay import TasmotaRelay
from cpython_only import cpython_only

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# IP and port of mock API receiver instance
mock_address = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['port']}"


class TestTasmotaRelay(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = TasmotaRelay("device1", "device1", "tasmota-relay", "enabled", {}, mock_address)

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, TasmotaRelay)
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.uri, mock_address)

    def test_02_turn_on(self):
        self.assertTrue(self.instance.send(1))
        self.assertEqual(self.instance.check_state(), 'ON')

    def test_03_turn_off(self):
        self.assertTrue(self.instance.send(0))
        self.assertEqual(self.instance.check_state(), 'OFF')

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_06_get_url(self):
        # Confirm both URLs are correct
        self.assertEqual(self.instance.get_url(0), f'http://{mock_address}/cm?cmnd=Power%20Off')
        self.assertEqual(self.instance.get_url(1), f'http://{mock_address}/cm?cmnd=Power%20On')

    def test_06_network_errors(self):
        # Change port to error port (mock receiver returns error for all requests on this port)
        # Confirm send method returns False
        self.instance.uri = f"{config['mock_receiver']['ip']}:{config['mock_receiver']['error_port']}"
        self.assertFalse(self.instance.send(1))

        # Change to invalid IP, confirm send method returns False
        self.instance.uri = "0.0.0."
        self.assertFalse(self.instance.send(0))
        self.assertFalse(self.instance.send(1))

        # Confirm check_state method raises RuntimeError
        with self.assertRaises(RuntimeError):
            self.instance.check_state()

        # Revert URI
        self.instance.uri = mock_address

    @cpython_only
    def test_07_monitor(self):
        from unittest.mock import patch

        # Task breaks monitor loop after first reading
        async def break_loop(task):
            await asyncio.sleep(1.1)
            task.cancel()

        # Runs instance.monitor + task to kill loop after first request
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(task_monitor))
            await asyncio.gather(task_monitor, task_kill)

        # Turn on (mock receiver will respond 'ON' to status request)
        self.assertTrue(self.instance.send(1))
        # Override state to False (simulate user turning on with lightswitch
        # while sensor condition is not met)
        self.instance.state = False

        # Run loop for 1 second, confirm state changed to True
        asyncio.run(test_monitor_and_kill())
        self.assertTrue(self.instance.state)

        # Turn off (mock receiver will respond 'OFF' to status request)
        self.assertTrue(self.instance.send(0))
        # Override state to True (simulate user turning of with lightswitch
        # while sensor condition is met)
        self.instance.state = True

        # Run loop for 1 second, confirm state changed to False
        asyncio.run(test_monitor_and_kill())
        self.assertFalse(self.instance.state)

        # Run loop for 1 second while simulating network error in API call
        with patch.object(self.instance, 'check_state', side_effect=RuntimeError):
            asyncio.run(test_monitor_and_kill())

        # Confirm state did not change
        self.assertFalse(self.instance.state)
