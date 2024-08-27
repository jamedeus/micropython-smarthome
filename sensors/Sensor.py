import logging
from micropython import schedule
from Instance import Instance

# Set name for module's log lines
log = logging.getLogger("Sensor")


class Sensor(Instance):
    def __init__(self, name, nickname, _type, enabled, current_rule, default_rule, targets):
        super().__init__(name, nickname, _type, enabled, current_rule, default_rule)

        # List of Device instances controlled by Sensor, used by Config.build_groups
        # to determine which sensors belong in same Group instance
        self.targets = targets

    def refresh_group(self):
        # Check conditions of all sensors in group
        if hasattr(self, 'group'):
            self.print(f"Refreshing {self.group.name}")
            schedule(self.group._refresh, None)

    def enable(self):
        super().enable()

        # Check conditions of all sensors in group
        self.refresh_group()

    def disable(self):
        super().disable()

        # Check conditions of all sensors in group
        self.refresh_group()

    # Allow API commands to simulate the sensor being triggered
    # Disabled by default, must be overridden in supported subclasses
    def trigger(self):
        return False

    # Called by Config after adding Sensor to Group. Appends functions to Group's post_action_routines list
    # Placeholder function for subclasses with no post-routines, overwritten if they do
    def add_routines(self):
        return

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint, more verbose than status
    def get_attributes(self):
        attributes = super().get_attributes()

        # Make dict json-compatible
        for i in self.__dict__:
            # Remove object references
            if i in ("i2c", "temp_sensor", "sensor", "switch"):
                del attributes[i]

            # Replace desktop_target instance with instance.name
            elif i == "desktop_target":
                if attributes["desktop_target"] is not None:
                    attributes["desktop_target"] = attributes["desktop_target"].name

            # Replace monitor_task with True or False
            elif i == "monitor_task":
                if attributes["monitor_task"] is not None:
                    attributes["monitor_task"] = True
                else:
                    attributes["monitor_task"] = False

        # Replace device instances with instance.name attribute
        attributes["targets"] = []
        for i in self.targets:
            attributes["targets"].append(i.name)

        return attributes

    # Return JSON-serializable dict containing state information
    # Called by Config.get_status to build API status response
    def get_status(self):
        status = super().get_status()
        status['condition_met'] = self.condition_met()
        status['targets'] = [t.name for t in self.targets]
        return status
