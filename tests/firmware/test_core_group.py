import unittest
from Group import Group
from Device import Device
from Sensor import Sensor


class MockDevice(Device):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        # Used to confirm that send method was called
        self.send_method_called = False

        # Used to simulate failed send call
        self.send_result = True

    def send(self, arg=None):
        self.send_method_called = True
        return self.send_result


class MockSensor(Sensor):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, targets):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule, targets)

        self.enabled = True

        # Used to arbitrarily set sensor condition
        self.condition = False

        # Track if post-action routine called
        self.routine_called = False

    def condition_met(self):
        return self.condition

    # Adds decorated function to group's post_action_routines, called after turning on/off
    def add_routines(self):
        @self.group.add_post_action_routine()
        def routine():
            self.routine_called = True


class TestGroup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate test device, sensor, and group
        cls.device = MockDevice('device1', 'device1', 'device', True, 'enabled', 'enabled')
        cls.sensor = MockSensor('sensor1', 'sensor1', 'sensor', True, 'enabled', 'enabled', [cls.device])
        cls.group = Group("group1", [cls.sensor])
        cls.device.group = cls.group
        cls.sensor.group = cls.group
        cls.sensor.add_routines()

    def test_01_initial_conditions(self):
        # Confirm expected attributes
        self.assertEqual(self.group.triggers, [self.sensor])
        self.assertEqual(self.group.targets, [self.device])
        self.assertEqual(self.group.state, None)
        self.assertEqual(len(self.group.post_action_routines), 1)

    def test_02_reset_state(self):
        # Set state to True, confirm resets to None correctly
        self.group.state = True
        self.group.reset_state()
        self.assertEqual(self.group.state, None)

    def test_03_check_sensor_conditions(self):
        # Set sensor condition to True, should return list containing True
        self.sensor.condition = True
        self.assertEqual(self.group.check_sensor_conditions(), [True])

        # Set sensor condition to False, should return list containing False
        self.sensor.condition = False
        self.assertEqual(self.group.check_sensor_conditions(), [False])

        # Disable sensor, should return empty list
        self.sensor.enabled = False
        self.assertEqual(self.group.check_sensor_conditions(), [])
        self.sensor.enabled = True

    def test_04_determine_correct_action(self):
        # Ensure group state is None
        self.group.state = None

        # Should return True if any conditions are True
        self.assertTrue(self.group.determine_correct_action([False, True, None]))

        # Should return None if any condition is None and no conditions are True
        self.assertEqual(self.group.determine_correct_action([False, False, None]), None)

        # Should return False if all conditions are False
        self.assertFalse(self.group.determine_correct_action([False, False, False]))

        # Should return None if correct action matches current state
        self.group.state = True
        self.assertEqual(self.group.determine_correct_action([True, False, None]), None)

    def test_05_apply_action(self):
        # Confirm send method not called if action matches group state
        self.group.state = True
        self.group.apply_action(True)
        self.assertFalse(self.device.send_method_called)
        self.assertFalse(self.sensor.routine_called)

        # Confirm that send method is called, group action changes to reflect applied action
        self.group.apply_action(False)
        self.assertFalse(self.group.state)
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False
        self.assertTrue(self.sensor.routine_called)
        self.sensor.routine_called = False

        # Confirm that group state does not change when send methods fail
        self.device.send_result = False
        self.group.apply_action(True)
        self.assertFalse(self.group.state)
        self.assertTrue(self.device.send_method_called)
        self.assertFalse(self.sensor.routine_called)
        self.device.send_method_called = False

    def test_06_refresh(self):
        # Reset mock device: send method not called, send result = True
        self.device.send_method_called = False
        self.device.send_result = True

        # Simulate sensor triggered, call refresh_group
        self.sensor.condition = True
        self.sensor.refresh_group()

        # Confirm device turned on, reset
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False

        # Refresh again, confirm device.send not called (state already matches)
        self.sensor.refresh_group()
        self.assertFalse(self.device.send_method_called)

        # Simulate sensor off condition, call refresh_group
        self.sensor.condition = False
        self.sensor.refresh_group()

        # Confirm device turned off, reset
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False

        # Simulate sensor no-change condition, call refresh_group
        self.sensor.condition = None
        self.sensor.refresh_group()

        # Confirm device.send not called
        self.assertFalse(self.device.send_method_called)
