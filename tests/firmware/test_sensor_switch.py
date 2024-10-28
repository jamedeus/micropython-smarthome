import unittest
from machine import Pin
from Group import Group
from Switch import Switch
from cpython_only import cpython_only

# Expected return value of get_attributes method just after instantiation
expected_attributes = {
    'rule_queue': [],
    'enabled': True,
    'group': 'group1',
    'default_rule': 'enabled',
    'name': 'sensor1',
    '_type': 'switch',
    'nickname': 'sensor1',
    'current_rule': None,
    'scheduled_rule': None,
    'schedule': {},
    'targets': [],
    'switch_closed': bool(Pin(19, Pin.IN, Pin.PULL_DOWN).value())
}


# Subclass Group to detect when refresh method called
class MockGroup(Group):
    def __init__(self, name, sensors):
        super().__init__(name, sensors)

        self.refresh_called = False

    def refresh(self, arg=None):
        self.refresh_called = True
        super().refresh()


class TestSwitch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Switch("sensor1", "sensor1", "switch", "enabled", {}, [], 19)
        cls.group = MockGroup('group1', [cls.instance])
        cls.instance.group = cls.group

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Switch)
        self.assertTrue(self.instance.enabled)

    def test_02_get_attributes(self):
        attributes = self.instance.get_attributes()
        self.assertEqual(attributes, expected_attributes)

    def test_03_trigger(self):
        # Should not be able to trigger this sensor type
        self.assertFalse(self.instance.trigger())

    def test_04_condition_met(self):
        self.assertFalse(self.instance.condition_met())

        # Mock env: simulate turnned on (conditional prevents fail on baremetal)
        self.instance.switch.value(1)
        if self.instance.switch.value():
            self.assertTrue(self.instance.condition_met())

    def test_05_interrupt_handler(self):
        # Ensure group.Refresh not called
        self.group.refresh_called = False

        # Simulate hardware interrupt, confirm group.Refresh called
        self.instance.interrupt_handler()
        self.assertTrue(self.group.refresh_called)

    @cpython_only
    def test_06_switch_closed_attribute(self):
        # Mock closed switch, call interrupt handler, confirm attribute
        self.instance.switch.pin_state = 1
        self.instance.interrupt_handler()
        self.assertTrue(self.instance.switch_closed)

        # Mock open switch, call interrupt handler, confirm attribute
        self.instance.switch.pin_state = 0
        self.instance.interrupt_handler()
        self.assertFalse(self.instance.switch_closed)
