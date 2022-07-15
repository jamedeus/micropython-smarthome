import uasyncio as asyncio
import logging

# Set name for module's log lines
log = logging.getLogger("Group")



class Group():
    def __init__(self, name, sensors):
        self.name = name

        self.triggers = sensors

        # All have same targets
        self.targets = self.triggers[0].targets

        self.state = None

        log.info(f"Instantiated Group named {self.name}")


    def reset_state(self):
        self.state = None


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
        # Turn off: Requries ALL sensors to return False
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
            # Do not turn device on/off if already on/off, or if device is disabled
            if device.enabled and not action == device.state:
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

            for i in self.triggers:
                # When thermostat turns targets on/off, clear recent readings (used to detect failed on/off command) to prevent false positives
                if i.sensor_type == "si7021":
                    i.recent_temps = []
