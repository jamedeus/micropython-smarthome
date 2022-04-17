import uasyncio as asyncio
import logging

# Set name for module's log lines
log = logging.getLogger("Sensor")



class Sensor():
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):

        self.name = name

        self.sensor_type = sensor_type

        self.enabled = enabled

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = scheduled_rule

        # Will hold sequential schedule rules so they can be quickly changed when interrupt runs
        self.rule_queue = []

        # List of instances
        self.targets = targets



    def enable(self):
        self.enabled = True



    def disable(self):
        self.enabled = False



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        rule = self.rule_validator(rule)
        if not str(rule) == "False":
            self.current_rule = rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "Disabled":
                # TODO there are probably scenarios where lights can get stuck on here
                self.disable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled == False:
                self.enable()

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False



    def next_rule(self):
        log.debug(f"{self.name}: Scheduled rule change")
        print(f"{self.name}: Scheduled rule change")
        if self.set_rule(self.rule_queue.pop(0)):
            # If new rule is valid, also change scheduled_rule
            self.scheduled_rule = self.current_rule
