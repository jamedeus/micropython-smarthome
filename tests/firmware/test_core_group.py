# pylint: disable=missing-function-docstring,missing-class-docstring

import asyncio
import unittest
import app_context
from Group import Group
from Device import Device
from Sensor import Sensor


class MockDevice(Device):
    def __init__(self, name, nickname, _type, enabled, default_rule, schedule):
        super().__init__(name, nickname, _type, enabled, default_rule, schedule)

        # Used to confirm that send method was called
        self.send_method_called = False

        # Used to simulate failed send call
        self.send_result = True

        # Used to simulate hardware device turned on by send method
        self.hardware_state = None

    def send(self, state):
        self.send_method_called = True
        if not self.enabled and state:
            return True
        self.hardware_state = bool(state)
        return self.send_result


class MockSensor(Sensor):
    def __init__(self, name, nickname, _type, enabled, default_rule, schedule, targets):
        super().__init__(name, nickname, _type, enabled, default_rule, schedule, targets)

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
        cls.device = MockDevice('device1', 'device1', 'device', True, 'enabled', {})
        cls.sensor = MockSensor('sensor1', 'sensor1', 'sensor', True, 'enabled', {}, [cls.device])
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
        # Should return True if any conditions are True
        self.assertTrue(self.group.determine_correct_action([False, True, None]))

        # Should return None if any condition is None and no conditions are True
        self.assertEqual(self.group.determine_correct_action([False, False, None]), None)

        # Should return False if all conditions are False
        self.assertFalse(self.group.determine_correct_action([False, False, False]))

    def test_05_apply_action(self):
        # Confirm send method not called if action matches group state
        self.group.state = True
        self.group.apply_action(True)
        self.assertFalse(self.device.send_method_called)
        self.assertFalse(self.sensor.routine_called)

        # Confirm that send method is called, group state changes to reflect applied action
        self.group.apply_action(False)
        self.assertFalse(self.group.state)
        self.assertTrue(self.device.send_method_called)
        self.device.send_method_called = False
        self.assertTrue(self.sensor.routine_called)
        self.sensor.routine_called = False

        # Confirm that group state changes to None when send methods fail
        self.device.send_result = False
        self.group.apply_action(True)
        self.assertEqual(self.group.state, None)
        self.assertTrue(self.device.send_method_called)
        self.assertFalse(self.sensor.routine_called)
        self.device.send_method_called = False
        # Confirm that retry was scheduled
        asyncio.run(asyncio.sleep_ms(10))
        self.assertTrue("group1_retry" in str(app_context.timer_instance.schedule))

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

    def test_07_retry(self):
        # Reset mock device: send method not called, send result = True
        self.device.send_method_called = False
        self.device.send_result = True

        # Simulate sensor triggered
        self.sensor.condition = True

        # Call retry (simulate callback that runs 5 seconds after failed
        # refresh), confirm device turned on
        self.group.retry()
        self.assertTrue(self.device.send_method_called)

    # Original bug: Disabling a device while turned on did not turn off, but did flip state to False
    # This resulted in device staying on even after sensors turned other devices in group off. If
    # device was enabled while sensor conditions not met, it still would not be turned off because
    # state (False) matched correct action (turn off). This meant it was impossible to turn the
    # light off without triggering + resetting sensors (or using API).
    def test_08_regression_correct_state_when_re_enabled(self):
        # Ensure Device enabled, simulate turning on
        self.device.enable()
        self.group.state = False
        self.group.apply_action(True)

        # Confirm Device turned on, LED state is correct, group state is correct
        self.assertEqual(self.device.hardware_state, True)
        self.assertTrue(self.device.state)
        self.assertTrue(self.group.state)

        # Disable, should turn off automatically (before fix would stay on)
        self.device.disable()
        self.assertFalse(self.device.enabled)

        # Confirm turned off
        self.assertFalse(self.device.state)
        self.assertEqual(self.device.hardware_state, False)

        # Simulate reset_timer expiring while disabled
        self.group.state = False

        # Re-enable to reproduce issue, before fix device would still be on
        self.device.enable()

        # Should be turned off
        self.assertFalse(self.device.state)
        self.assertEqual(self.device.hardware_state, False)

    # Original bug: Disabled devices manually turned on by user could not be turned off by loop.
    # This became an issue when on/off rules were removed, requiring use of enabled/disabled.
    # After fix disabled devices may be turned off, preventing lights from getting stuck. Disabled
    # devices do NOT respond to on commands, but do flip their state to True to stay in sync with
    # rest of group - this is necessary to allow turning off, since a device with state == False
    # will be skipped by loop (already off), and user flipping light switch doesn't effect state
    def test_09_regression_turn_off_while_disabled(self):
        # Disable Device, simulate user turning on (cannot call send while disabled)
        self.device.disable()
        self.device.hardware_state = True
        self.assertFalse(self.device.enabled)
        self.assertEqual(self.device.hardware_state, True)
        # State is uneffected when manually turned on
        self.assertFalse(self.device.state)

        # Simulate triggered sensor turning group on
        self.group.state = False
        self.group.apply_action(True)
        # Device state should change, now matches actual state (possible for loop to turn off)
        self.assertTrue(self.device.state)

        # Simulate group turning off after sensor resets
        self.group.state = True
        self.group.apply_action(False)

        # Device should now be turned off
        self.assertFalse(self.device.state)
        self.assertEqual(self.device.hardware_state, False)

        # Simulate group turning on again - relay should NOT turn on
        self.group.apply_action(True)
        self.assertTrue(self.device.state)

        # Should still be off
        self.assertEqual(self.device.hardware_state, False)

        # State should be True even though device is disabled and off
        self.assertTrue(self.device.state)

    # Original bug: Group state was only updated after apply_action ran with no
    # errors in device send calls. If errors occurred the group state would not
    # change, which could result in a sensor interupt being ignored (new action
    # matches outdated group state). Example: If group state is True and action
    # changes to False devices turn off, but if 1 fails group state still True.
    # When action changes back to True devices will not turn on (action matches
    # current group state because it didn't change after the failed send).
    #
    # Group.apply_action now resets state to None when an error occurs to allow
    # applying opposite action when sensor conditions change (or retry failed
    # send if group refreshed again).
    def test_10_regression_failed_send_causes_group_to_stop_responding(self):
        # Ensure device and sensor are enabled
        self.device.enable()
        self.sensor.enable()

        # Simulate group turned off
        self.group.state = False
        self.device.state = None
        self.device.hardware_state = False
        self.device.send_method_called = False

        # Simulate sensor condition changing to True, device send method
        # failing to turn on
        self.sensor.condition = True
        self.device.send_result = False
        self.sensor.refresh_group()

        # Confirm device.send called, device.state did not change, group.state
        # was reset to None (should not remain False)
        self.assertTrue(self.device.send_method_called)
        self.assertEqual(self.device.state, None)
        self.assertEqual(self.group.state, None)

        # Simulate device coming back online (send method will succeed)
        self.device.send_result = True
        self.device.send_method_called = False

        # Simulate sensor condition changing to False
        self.sensor.condition = False
        self.sensor.refresh_group()

        # Confirm group called device send method (before fix sensor change was
        # ignored because new action matched existing state) and set device and
        # group states to False
        self.assertTrue(self.device.send_method_called)
        self.assertFalse(self.device.state)
        self.assertFalse(self.group.state)
