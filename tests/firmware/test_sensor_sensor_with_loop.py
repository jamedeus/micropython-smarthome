import asyncio
import unittest
from Group import Group
from SensorWithLoop import SensorWithLoop


async def mock_monitor():
    await asyncio.sleep(0)


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True


class TestSensorWithLoop(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create test instance, add rule to queue
        cls.instance = SensorWithLoop("sensor1", "Test", "sensor", True, "enabled", [])
        cls.instance.rule_queue = ["disabled"]
        cls.instance.current_rule = "enabled"
        cls.instance.scheduled_rule = "enabled"

        # Create mock group
        cls.group = MockGroup("group1", [cls.instance])
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        # Confirm expected attributes just after instantiation
        self.assertIsInstance(self.instance, SensorWithLoop)
        self.assertEqual(self.instance.name, "sensor1")
        self.assertEqual(self.instance.nickname, "Test")
        self.assertTrue(self.instance.enabled)
        self.assertEqual(self.instance.current_rule, "enabled")
        self.assertEqual(self.instance.scheduled_rule, "enabled")
        self.assertEqual(self.instance.default_rule, "enabled")
        self.assertEqual(self.instance.targets, [])
        self.assertEqual(self.instance.monitor_task, None)

    def test_02_disable_stops_loop(self):
        # Confirm loop task exists
        self.instance.monitor_task = asyncio.create_task(mock_monitor())
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

    def test_03_enable_starts_loop(self):
        # Cancel existing loop and replace with None
        if self.instance.monitor_task:
            self.instance.monitor_task.cancel()
            self.instance.monitor_task = None

        # Enable, confirm loop task created
        self.instance.enable()
        self.assertIsInstance(self.instance.monitor_task, asyncio.Task)

    def test_04_get_attributes(self):
        # monitor_task key should contain "True" when loop is running
        self.instance.monitor_task = asyncio.create_task(mock_monitor())
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes['monitor_task'], True)

        # monitor_task key should contain "False" when loop not running
        self.instance.monitor_task = None
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes['monitor_task'], False)

    def test_05_placeholder_monitor(self):
        # Placeholder method should raise NotImplementedError
        with self.assertRaises(NotImplementedError):
            asyncio.run(self.instance.monitor())
