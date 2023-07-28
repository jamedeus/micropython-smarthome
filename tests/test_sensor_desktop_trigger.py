import json
import unittest
import urequests
import uasyncio as asyncio
from Group import Group
from Desktop_target import Desktop_target
from Desktop_trigger import Desktop_trigger

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'ip': config['mock_receiver']['ip'],
    'port': config['mock_receiver']['port'],
    'nickname': 'sensor1',
    'current': None,
    'desktop_target': 'device1',
    'enabled': True,
    'group': 'group1',
    'rule_queue': [],
    'name': 'sensor1',
    'default_rule': 'enabled',
    '_type': 'desktop',
    'current_rule': None,
    'scheduled_rule': None,
    'targets': ['device1']
}


class TestDesktopTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Get mock command receiver address
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]

        # Create test instance, target instance, group instance
        cls.target = Desktop_target("device1", "device1", "desktop", "enabled", ip, port)
        cls.instance = Desktop_trigger("sensor1", "sensor1", "desktop", "enabled", [cls.target], ip, port)
        group = Group('group1', [cls.instance])
        cls.instance.group = group

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Desktop_trigger)
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.ip, config["mock_receiver"]["ip"])
        self.assertEqual(self.instance.port, config["mock_receiver"]["port"])
        self.assertEqual(self.instance.current, None)
        self.assertEqual(self.instance.desktop_target, self.target)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_get_idle_time(self):
        idle_time = self.instance.get_idle_time()
        self.assertIsInstance(idle_time, dict)
        self.assertIsInstance(int(idle_time["idle_time"]), int)

    def test_04_get_monitor_state(self):
        state = self.instance.get_monitor_state()
        self.assertIsInstance(state, str)
        self.assertIn(state, ['On', 'Off', 'Disabled'])

    def test_05_trigger(self):
        # Ensure not already triggered to avoid false positive
        self.instance.current = "Off"
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met, current should be On
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())
        self.assertEqual(self.instance.current, "On")

    def test_06_network_errors(self):
        # Change port to error port (mock receiver returns error for all requests on this port)
        self.instance.port = config["mock_receiver"]["error_port"]

        # Confirm that network error in get_idle_time() disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_idle_time())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Confirm that invalid json response in get_monitor_state() disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_monitor_state())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Revert port, change to invalid IP to simulate failed network request
        self.instance.port = config["mock_receiver"]["error_port"]
        self.instance.ip = "0.0.0."

        # Confirm get_monitor_state returns False when network error encountered
        self.assertFalse(self.instance.get_monitor_state())
        self.instance.ip = config["mock_receiver"]["ip"]

    def test_07_exit_monitor_loop_when_disabled(self):
        # Disable instance, confirm monitor coro returns False (end of loop)
        self.instance.disable()
        self.assertFalse(asyncio.run(self.instance.monitor()))

    def test_08_monitor(self):
        # Ensure instance enabled, using correct port
        self.instance.enable()
        self.instance.port = config["mock_receiver"]["port"]

        # Get URL of mock command receiver, set first reading to On
        url = f'{config["mock_receiver"]["ip"]}:{config["mock_receiver"]["port"]}'
        urequests.get(f'http://{url}/on')

        # Task break loop after 2 readings
        async def break_loop(instance):
            await asyncio.sleep(2.1)
            instance.disable()

        # Task toggles state returned by mock receiver while loop is sleeping
        async def toggle_state(url):
            await asyncio.sleep(0.1)
            urequests.get(f'http://{url}/off')
            await asyncio.sleep(1.1)
            urequests.get(f'http://{url}/on')

        # Run instance.monitor + 2 tasks above with asyncio.gather
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(self.instance))
            task_toggle = asyncio.create_task(toggle_state(url))
            await asyncio.gather(task_monitor, task_kill, task_toggle)
        asyncio.run(test_monitor_and_kill())

        # Confirm instance + target attributes match last reading (On)
        self.assertEqual(self.instance.current, 'On')
        self.assertTrue(self.target.state)
