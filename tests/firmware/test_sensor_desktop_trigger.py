import json
import asyncio
import requests
import unittest
from Group import Group
from MotionSensor import MotionSensor
from DesktopTarget import DesktopTarget
from DesktopTrigger import DesktopTrigger
from cpython_only import cpython_only

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)

# Get mock command receiver address
ip = config["mock_receiver"]["ip"]
port = config["mock_receiver"]["port"]

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'uri': f'{ip}:{port}',
    'nickname': 'sensor1',
    'current': None,
    'desktop_target': 'device1',
    'enabled': True,
    'mode': 'screen',
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


# Subclass Group to detect when refresh and reset_state methods called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False
        self.reset_state_called = False

    def refresh(self, arg=None):
        self.refresh_called = True
        super().refresh()

    def reset_state(self):
        self.reset_state_called = True
        super().reset_state()


class TestDesktopTrigger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test group with desktop_trigger and motion sensor targeting desktop_target
        cls.target = DesktopTarget("device1", "device1", "desktop", "enabled", ip, port)
        cls.instance = DesktopTrigger("sensor1", "sensor1", "desktop", "enabled", [cls.target], "screen", ip, port)
        cls.pir = MotionSensor("sensor1", "sensor1", "pir", None, [cls.target], 15)
        cls.group = MockGroup('group1', [cls.instance, cls.pir])
        cls.instance.group = cls.group
        cls.pir.group = cls.group
        cls.target.group = cls.group

    def setUp(self):
        # Enable instance, reset self.current, set mode to screen
        self.instance.enable()
        self.instance.current = None
        self.instance.mode = "screen"
        # Set normal IP and port (not error)
        self.instance.uri = f'{ip}:{port}'
        # Ensure sensor has desktop_target attribute (removed in some tests)
        self.instance.desktop_target = self.target
        # Reset group refresh_called and reset_state_called
        self.group.refresh_called = False
        self.group.reset_state_called = False

    @classmethod
    def tearDownClass(cls):
        # Kill monitor task next time loop yields, avoid accumulating tasks
        cls.instance.disable()
        asyncio.run(asyncio.sleep(1))

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, DesktopTrigger)
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.uri, f'{ip}:{port}')
        self.assertEqual(self.instance.current, None)
        self.assertEqual(self.instance.desktop_target, self.target)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_get_idle_time(self):
        idle_time = self.instance.get_idle_time()
        self.assertIsInstance(idle_time, int)

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

        # Change mode to "activity", ensure not triggered
        self.instance.mode = "activity"
        self.instance.current = 999999
        self.assertFalse(self.instance.condition_met())
        # Trigger, condition should now be met, current should be 0
        self.assertTrue(self.instance.trigger())
        self.assertTrue(self.instance.condition_met())
        self.assertEqual(self.instance.current, 0)

    def test_06_network_errors(self):
        # Change port to error port (mock receiver returns error for all requests on this port)
        self.instance.uri = f'{ip}:{config["mock_receiver"]["error_port"]}'

        # Configure mock receiver to return 400 error
        url = f'{ip}:{config["mock_receiver"]["error_port"]}'
        requests.get(f'http://{url}/set_bad_request_error')

        # Confirm that get_idle_time returns False, does not disable sensor
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_idle_time())
        self.assertTrue(self.instance.enabled)

        # Confirm that get_monitor_state returns False, does not disable sensor
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_monitor_state())
        self.assertTrue(self.instance.enabled)

        # Configure mock receiver to return 200 status with unexpected JSON
        requests.get(f'http://{url}/set_unexpected_json_error')

        # Confirm that invalid json response in get_monitor_state disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_monitor_state())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Confirm that invalid json response in get_idle_time disables instance
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.get_idle_time())
        self.assertFalse(self.instance.enabled)
        self.instance.enable()

        # Change to invalid IP to simulate failed network request
        self.instance.uri = f"0.0.0.:{port}"

        # Confirm both methods return False when network error encountered
        self.assertFalse(self.instance.get_monitor_state())
        self.assertFalse(self.instance.get_idle_time())

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

        # Disable and yield to loop, confirm task replaced with None
        asyncio.run(test())
        self.assertEqual(self.instance.monitor_task, None)

    def test_09_condition_met_screen_mode(self):
        # Should return True when self.current is On
        self.instance.current = "On"
        self.assertTrue(self.instance._condition_met_screen_mode())

        # Should return False when self.current is Off
        self.instance.current = "Off"
        self.assertFalse(self.instance._condition_met_screen_mode())

    def test_10_condition_met_activity_mode(self):
        # Should return True when self.current is less than 60000 (1 minute)
        self.instance.current = 0
        self.assertTrue(self.instance._condition_met_activity_mode())

        # Should return False when self.current is greater than 60000
        self.instance.current = 999999
        self.assertFalse(self.instance._condition_met_activity_mode())

        # Should return False when self.current is not integer
        self.instance.current = "On"
        self.assertFalse(self.instance._condition_met_activity_mode())

    def test_11_get_current_screen_mode_on(self):
        # Configure mock receiver to return On for first reading
        requests.post(f'http://{ip}:{port}/set_screen_state', json={'state': 'On'})

        # Call method
        self.instance._get_current_screen_mode()
        # Confirm current is "On", condition is met, Group.refresh called
        self.assertEqual(self.instance.current, "On")
        self.assertTrue(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)
        # Confirm DesktopTarget state atribute matches
        self.assertTrue(self.instance.desktop_target.state)

    def test_12_get_current_screen_mode_off(self):
        # Configure mock receiver to return Off for next reading
        requests.post(f'http://{ip}:{port}/set_screen_state', json={'state': 'Off'})

        # Call method
        self.instance._get_current_screen_mode()
        # Confirm current is "Off", condition not met, Group.refresh called
        self.assertEqual(self.instance.current, "Off")
        self.assertFalse(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)
        # Confirm DesktopTarget state atribute matches
        self.assertFalse(self.instance.desktop_target.state)
        # Confirm group state was reset to None (allows turning screen back on)
        self.assertTrue(self.group.reset_state_called)

        # Simulate no DesktopTarget configured, reset group, set current to On
        self.instance.desktop_target = None
        self.group.refresh_called = False
        self.group.reset_state_called = False
        self.instance.current = "On"

        # Call method
        self.instance._get_current_screen_mode()
        # Confirm current is "Off", condition not met, Group.refresh called
        self.assertEqual(self.instance.current, "Off")
        self.assertFalse(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)
        # Confirm group state was NOT reset (only needed for DesktopTarget)
        self.assertFalse(self.group.reset_state_called)

    def test_13_get_current_screen_mode_standby(self):
        # Configure mock receiver to return standby for next reading
        requests.post(f'http://{ip}:{port}/set_screen_state', json={'state': 'standby'})

        # Call method
        self.instance._get_current_screen_mode()
        # Confirm current did not change, condition not met, Group.refresh not called
        self.assertEqual(self.instance.current, None)
        self.assertFalse(self.instance.condition_met())
        self.assertFalse(self.group.refresh_called)

    def test_14_get_current_activity_mode(self):
        # Reset instance.current, ensure activity mode
        self.instance.current = None
        self.instance.mode = "activity"

        # Configure mock receiver to return 0ms for first reading
        requests.post(f'http://{ip}:{port}/set_idle_time', json={'idle_time': 0})

        # Call method
        self.instance._get_current_activity_mode()
        # Confirm current is 0, condition is met, Group.refresh called
        self.assertEqual(self.instance.current, 0)
        self.assertTrue(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)

        # Reset group, set next reading to 999999
        self.group.refresh_called = False
        self.group.state = True
        requests.post(f'http://{ip}:{port}/set_idle_time', json={'idle_time': 999999})

        # Call method
        self.instance._get_current_activity_mode()
        # Confirm current is 999999, condition not met, Group.refresh called
        self.assertEqual(self.instance.current, 999999)
        self.assertFalse(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)

        # Change to error port to simulate failed request
        self.instance.uri = f'{ip}:{config["mock_receiver"]["error_port"]}'
        # Call method, confirm returns False
        self.assertFalse(self.instance._get_current_activity_mode())

    def test_15_instantiate_with_invalid_mode(self):
        # Instantiate with unsupported mode
        with self.assertRaises(ValueError):
            DesktopTrigger("sensor1", "sensor1", "desktop", "enabled", [], "invalid", ip, port)

    def test_16_monitor_screen(self):
        # Configure mock receiver to return On for first reading
        requests.post(f'http://{ip}:{port}/set_screen_state', json={'state': 'On'})

        # Set sensor mode to screen, set current to Off
        self.instance.mode = "screen"
        self.instance.current = "Off"

        # Task breaks monitor loop after first reading
        async def break_loop(task):
            await asyncio.sleep(1.1)
            task.cancel()

        # Runs instance.monitor + task to kill loop after first request
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(task_monitor))
            await asyncio.gather(task_monitor, task_kill)

        # Run loop for 1 second
        asyncio.run(test_monitor_and_kill())

        # Confirm instance + target attributes match last reading (On)
        self.assertEqual(self.instance.current, 'On')
        self.assertTrue(self.target.state)
        # Confirm refresh called
        self.assertTrue(self.group.refresh_called)

        # Reset, set next reading to Off
        requests.post(f'http://{ip}:{port}/set_screen_state', json={'state': 'Off'})
        self.group.refresh_called = False

        # Run loop for 1 second
        asyncio.run(test_monitor_and_kill())

        # Confirm instance + target attributes match last reading (On)
        self.assertEqual(self.instance.current, 'Off')
        self.assertFalse(self.target.state)
        # Confirm refresh called
        self.assertTrue(self.group.refresh_called)

    def test_17_monitor_activity(self):
        # Configure mock receiver to return 42ms for first reading
        requests.post(f'http://{ip}:{port}/set_idle_time', json={'idle_time': 42})

        # Set sensor mode to activity
        self.instance.mode = "activity"

        # Task breaks monitor loop after first reading
        async def break_loop(task):
            await asyncio.sleep(1.1)
            task.cancel()

        # Runs instance.monitor + task to kill loop after first request
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(task_monitor))
            await asyncio.gather(task_monitor, task_kill)

        # Run loop for 1 second
        asyncio.run(test_monitor_and_kill())

        # Confirm current is 42, condition met, group refreshed
        self.assertEqual(self.instance.current, 42)
        self.assertTrue(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)

        # Reset, set group.state = True (condition currently met)
        self.group.refresh_called = False
        self.group.state = True

        # Run again, confirm group NOT refreshed (condition matches state)
        asyncio.run(test_monitor_and_kill())
        self.assertFalse(self.group.refresh_called)

        # Set reading >60,000 (user not active)
        requests.post(f'http://{ip}:{port}/set_idle_time', json={'idle_time': 999999})

        # Run loop for 1 second
        asyncio.run(test_monitor_and_kill())

        # Confirm current is 999999, condition NOT met, group refreshed
        self.assertEqual(self.instance.current, 999999)
        self.assertFalse(self.instance.condition_met())
        self.assertTrue(self.group.refresh_called)

    # Original bug: trigger method set Desktop current reading to 'On', which caused
    # main loop to turn targets on. After main loop was removed in c6f5e1d2 Desktop
    # only calls refresh_group when monitor loop receives new reading - overwriting
    # reading did not achieve this. Instead, overwriting with 'On' caused monitor
    # to interpret next reading ('Off') as new, resulting in targets being turned
    # OFF by trigger instead of ON. Trigger method now calls refresh_group directly.
    def test_18_regression_trigger_does_not_turn_on(self):
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

    # Original bug: If scheduled_rule was "disabled" at boot time calling the
    # enable method later would fail to start monitor loop. The __init__ method
    # creates an asyncio task for monitor and saves Task object in monitor_task
    # attribute (the enable method only creates task if monitor_task is None).
    # However, the loop does not start until sync code yields to asyncio. When
    # rule was "disabled" at boot time the set_rule call in Config.build_queue
    # would call DesktopTrigger.disable, which cancels monitor_task, before the
    # loop had started, so the except block in DesktopTrigger.monitor was never
    # reached. This except block originally set monitor_task to None (allowing
    # enable to create a new loop), so if it was not reached monitor_task would
    # still contain the canceled Task, preventing the loop from being started.
    # This is now handled in the disable method to ensure monitor_task is None.
    @cpython_only
    def test_19_regression_disabled_at_boot_breaks_monitor_loop(self):
        # Simulate instantiating with current_rule = disabled
        instance = DesktopTrigger("sensor1", "sensor1", "desktop", "disabled", [], "screen", ip, port)
        instance.set_rule("disabled")

        # Confirm monitor_task is None
        self.assertIsNone(instance.monitor_task)

    # Original bug: When the sensor was disabled self.current was not modified.
    # If the desktop was in sleep mode when sensor re-enabled it would continue
    # to use the outdated reading, which could cause condition_met to return
    # True (user active) even though the computer was offline.
    def test_20_regression_incorrect_condition_if_enabled_while_computer_asleep(self):
        # Simulate very recent user activity
        self.instance.mode = "activity"
        self.instance.current = 10
        self.assertTrue(self.instance.condition_met())

        # Disable sensor, re-enable
        self.instance.disable()
        self.instance.enable()

        # Confirm condition_met returns False until new idle time reading
        self.assertFalse(self.instance.condition_met())
