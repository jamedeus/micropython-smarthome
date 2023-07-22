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


class TestGroup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Instantiate test device, sensor, and group
        cls.device = MockDevice('device1', 'device1', 'device', True, 'enabled', 'enabled')
        cls.sensor = Sensor('sensor1', 'sensor1', 'sensor', True, 'enabled', 'enabled', [cls.device])
        cls.group = Group("group1", [cls.sensor])

    def test_01_determine_correct_action(self):
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

    def test_02_apply_action(self):
        # Confirm send method not called if action matches group state
        self.group.state = True
        self.group.apply_action(True)
        self.assertFalse(self.device.send_method_called)

        # Confirm that send method is called, group action changes to reflect applied action
        self.group.apply_action(False)
        self.assertFalse(self.group.state)
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False

        # Confirm that group state does not change when send methods fail
        self.device.send_result = False
        self.group.apply_action(True)
        self.assertFalse(self.group.state)
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False
