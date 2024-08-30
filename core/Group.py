import logging
from util import print_with_timestamp

# Set name for module's log lines
log = logging.getLogger("Group")


class Group():
    def __init__(self, name, sensors):
        self.name = name

        # List of instances for all sensors in group
        self.triggers = sensors

        # List of instances for all devices in group (don't need to iterate, all triggers have same targets)
        self.targets = self.triggers[0].targets

        # Changes to same state as targets after successful on/off command, main loop skips group until change needed
        self.state = None

        # Some sensor types run routines after turning their targets on/off
        # After adding sensor to group, Config calls sensor's add_routines method to populate list with functions
        self.post_action_routines = []

        # Preallocate reference to bound method so it can be called in ISR
        # https://docs.micropython.org/en/latest/reference/isr_rules.html#creation-of-python-objects
        self._refresh = self.refresh

        log.info(f"Instantiated Group named {self.name}")

    def reset_state(self):
        self.state = None

    # Called by decorators in some sensor's add_routines method, appends functions to self.post_action_routines
    def add_post_action_routine(self):
        def _add_post_action_routine(func):
            self.post_action_routines.append(func)
        return _add_post_action_routine

    def check_sensor_conditions(self):
        # Store return value from each sensor in group
        conditions = []

        # Check conditions for all enabled sensors
        for sensor in self.triggers:
            if sensor.enabled:
                conditions.append(sensor.condition_met())

        return conditions

    def determine_correct_action(self, conditions):
        # Determine action to apply to target devices: True = turn on, False = turn off, None = do nothing
        # Turn on: Requires only 1 sensor to return True
        # Turn off: Requires ALL sensors to return False
        # Nothing: Requires 1 sensor to return None and 0 sensors returning True
        if True in conditions:
            action = True
        elif None in conditions:
            action = None
        else:
            action = False

        if not action == self.state:
            return action
        else:
            return None

    def apply_action(self, action):
        # No action needed if group state already matches desired state
        if self.state == action:
            return

        failed = False

        for device in self.targets:
            # Do not turn device on/off if already on/off
            if not action == device.state:
                # int converts True to 1, False to 0
                success = device.send(int(action))

                # Only change device state if send returned True
                if success:
                    device.state = action

                else:
                    failed = True

        # If all succeeded, change group state to prevent re-sending
        if not failed:
            self.state = action

            # Run post-action routines (if any) for all sensors in group
            for function in self.post_action_routines:
                function()

    # Check condition of all sensors in group, turn devices on/off if needed
    # Arg is required for micropython.schedule but unused
    # Called by all sensors when condition changes
    def refresh(self, arg=None):
        action = self.determine_correct_action(self.check_sensor_conditions())
        if action is not None:
            print_with_timestamp(f"{self.name}: Applying action: {action}")
            self.apply_action(action)
