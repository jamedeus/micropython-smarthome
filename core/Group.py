import logging


class Group():
    '''Class used to group one or more sensors with identical targets.
    Instantiated by Config.build_groups.

    Args:
      name:         Unique, sequential name (group1, group2, etc)
      sensors:      List of sensor instances with identical targets

    Sensors call the refresh method when their condition changes (checks all
    sensor conditions, determines correct action, calls all device send methods
    if correct action does not match current state).

    Devices are turned on when one or more sensor conditions are True.
    Devices are turned off when all sensor conditions are False.
    Devices do not change if one or more sensor conditions are None and no
    sensor conditions are True.
    '''

    def __init__(self, name, sensors):

        # Set name for module's log lines
        self.log = logging.getLogger(f"{name}")

        self.name = name

        # List of instances for all sensors in group
        self.triggers = sensors

        # List of instances for all devices in group
        # (don't need to iterate, all triggers have same targets)
        self.targets = self.triggers[0].targets

        # Changes to match device state after successful refresh (no failed
        # device.send calls). Allows sensor to skip refresh when no changes
        # needed (current state already matches target state).
        self.state = None

        # Some sensor types run routines after turning their targets on/off.
        # After adding sensor to group, Config calls sensor's add_routines
        # method to populate this list with functions to call.
        self.post_action_routines = []

        # Preallocate reference to bound method so it can be called in ISR
        # https://docs.micropython.org/en/latest/reference/isr_rules.html#creation-of-python-objects
        self._refresh = self.refresh

        self.log.info("Instantiated Group")

    def reset_state(self):
        '''Changes group.state to None (used to bypass check in apply_action
        that skips send methods if group.state matches action arg).
        '''
        self.log.debug("reset state to None")
        self.state = None

    def add_post_action_routine(self):
        '''Decorator used inside sensor add_routines methods.
        Appends sensor functions to self.post_action_routines (each function is
        called after a successful group.refresh with no failed send calls).
        '''
        def _add_post_action_routine(func):
            self.post_action_routines.append(func)
        return _add_post_action_routine

    def check_sensor_conditions(self):
        '''Calls condition_met method of each sensor in group, returns list
        with response from each sensor.
        '''

        # Store return value from each sensor in group
        conditions = []

        # Check conditions for all enabled sensors
        for sensor in self.triggers:
            if sensor.enabled:
                conditions.append(sensor.condition_met())

        self.log.debug("Sensor conditions: %s", conditions)
        return conditions

    def determine_correct_action(self, conditions):
        '''Takes sensor conditions returned by check_sensor_conditions, returns
        correct action to apply to target devices (True = turn on, False = turn
        off, None = do nothing).

        Turn on: Requires 1 or more sensor(s) to return True
        Turn off: Requires ALL sensors to return False
        Nothing: Requires 1 sensor to return None and 0 sensors returning True
        '''
        if True in conditions:
            return True
        if None in conditions:
            return None
        return False

    def apply_action(self, action):
        '''Takes action (bool), calls send method of every device in group.
        Sets device.state to match action if send call succeeds.
        Sets group.state to match action if all send calls succeeded.
        Sets group.state to None if any send calls fail.
        '''

        # No action needed if group state already matches desired state
        if self.state == action:
            self.log.debug("current state already matches action")
            return

        failed = False

        for device in self.targets:
            # Do not turn device on/off if already on/off
            if not action == device.state:
                self.log.debug("applying action to %s", device.name)
                # int converts True to 1, False to 0
                success = device.send(int(action))

                # Only change device state if send returned True
                if success:
                    device.state = action

                else:
                    failed = True
            else:
                self.log.debug(
                    "%s: skipping %s (state already matches action)",
                    self.name, device.name
                )

        # If all succeeded, change group state to prevent re-sending
        if not failed:
            self.log.debug("finished applying action, no errors")
            self.state = action

            # Run post-action routines (if any) for all sensors in group
            for function in self.post_action_routines:
                function()

        # Reset group state if send failed (prevents getting stuck - if action
        # is True and group.state remains False due to a failed send then when
        # action changes to False it will match current state and send will not
        # be called. Changing to None allows any action to be applied).
        else:
            self.log.debug("encountered errors while applying action")
            self.reset_state()

    def refresh(self, *args):
        '''Checks all sensors conditions, turns devices on or off if needed.
        Called by all sensors when condition changes.
        Args not used (required for micropython schedule).
        '''
        self.log.debug("refresh group")
        action = self.determine_correct_action(self.check_sensor_conditions())
        self.log.debug("correct action: %s", action)
        if action is not None:
            self.log.info("applying action: %s", action)
            self.apply_action(action)
