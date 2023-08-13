import json
import unittest
import urequests
import uasyncio as asyncio
from Group import Group
from MotionSensor import MotionSensor
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
    'targets': ['device1'],
    'monitor_task': True
}


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True
        super().refresh()


class TestDesktopTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Get mock command receiver address
        ip = config["mock_receiver"]["ip"]
        port = config["mock_receiver"]["port"]

        # Create test group with desktop_trigger and motion sensor targeting desktop_target
        cls.target = Desktop_target("device1", "device1", "desktop", "enabled", ip, port)
        cls.instance = Desktop_trigger("sensor1", "sensor1", "desktop", "enabled", [cls.target], ip, port)
        cls.pir = MotionSensor("sensor1", "sensor1", "pir", None, [cls.target], 15)
        cls.group = MockGroup('group1', [cls.instance, cls.pir])
        cls.instance.group = cls.group
        cls.pir.group = cls.group
        cls.target.group = cls.group

    @classmethod
    def tearDownClass(cls):
        # Kill monitor task next time loop yields, avoid accumulating tasks
        cls.instance.disable()
        asyncio.run(asyncio.sleep(1))

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

    def test_07_enable_starts_loop(self):
        # Cancel existing loop and replace with None
        self.instance.monitor_task.cancel()
        self.instance.monitor_task = None

        # Enable, confirm loop task created
        self.instance.enable()
        self.assertIsInstance(self.instance.monitor_task, asyncio.Task)

    def test_08_disable_stops_loop(self):
        # Confirm loop task exists
        self.assertIsInstance(self.instance.monitor_task, asyncio.Task)

        # Ensure cancel and yield are in same event loop (cpython test
        # environment, not required for pure micropython)
        async def test():
            # Disable, should call monitor_task.cancel()
            self.instance.disable()

            # Yield to loop to allow monitor_task to exit
            await asyncio.sleep(0.1)

        # Disable and yeild to loop, confirm task replaced with None
        asyncio.run(test())
        self.assertEqual(self.instance.monitor_task, None)

    def test_09_monitor(self):
        # Ensure instance enabled, using correct port, Group.refresh not called
        self.instance.enable()
        self.instance.port = config["mock_receiver"]["port"]
        self.group.refresh_called = False

        # Get URL of mock command receiver, set first reading to On
        url = f'{config["mock_receiver"]["ip"]}:{config["mock_receiver"]["port"]}'
        urequests.get(f'http://{url}/on')

        # Task breaks monitor loop after 3 readings
        async def break_loop(task):
            await asyncio.sleep(3.1)
            task.cancel()

        # Task changes response from mock receiver /state endpoint between
        # each monitor reading, verifies previous reading handled correctly
        async def change_state(url):
            # Let monitor get initial reading (On)
            await asyncio.sleep(0.1)

            # Simulate MotionSensor triggered
            self.pir.motion = True
            # Change response to Off, wait for monitor to read
            urequests.get(f'http://{url}/off')
            await asyncio.sleep(1.0)

            # Confirm monitor read Off, reset MotionSensor
            self.assertEqual(self.instance.current, 'Off')
            self.assertFalse(self.pir.motion)
            # Change response to Disabled, wait for monitor to read
            urequests.get(f'http://{url}/Disabled')
            await asyncio.sleep(1.0)

            # Confirm monitor did not set current to Disabled (rest of
            # loop skipped if value is not On or Off), change to On
            self.assertEqual(self.instance.current, 'Off')
            urequests.get(f'http://{url}/on')

        # Run instance.monitor + 2 tasks above with asyncio.gather
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(task_monitor))
            task_toggle = asyncio.create_task(change_state(url))
            await asyncio.gather(task_monitor, task_kill, task_toggle)
        asyncio.run(test_monitor_and_kill())

        # Confirm instance + target attributes match last reading (On)
        self.assertEqual(self.instance.current, 'On')
        self.assertTrue(self.target.state)
        # Confirm refresh called
        self.assertTrue(self.group.refresh_called)

    # Original bug: trigger method set Desktop current reading to 'On', which caused
    # main loop to turn targets on. After main loop was removed in c6f5e1d2 Desktop
    # only calls refresh_group when monitor loop receives new reading - overwriting
    # reading did not achieve this. Instead, overwriting with 'On' caused monitor
    # to interpret next reading ('Off') as new, resulting in targets being turned
    # OFF by trigger instead of ON. Trigger method now calls refresh_group directly.
    def test_10_regression_trigger_does_not_turn_on(self):
        # Ensure target enabled, target turned off
        self.target.enable()
        self.target.state = False
        # Ensure Group.refresh not called, group state False
        self.group.refresh_called = False
        self.group.state = False

        # Trigger sensor, confirm Group.refresh called, confirm target turned ON
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)
        self.assertTrue(self.group.state)
        self.assertTrue(self.target.state)
