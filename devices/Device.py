

class Device():
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule):
        self.name = name

        self.device_type = device_type

        self.enabled = enabled

        # The rule actually followed when the device is triggered (can be changed through API)
        self.current_rule = current_rule

        # The rule that should be followed at the current time (used to undo API changes to current_rule)
        self.scheduled_rule = scheduled_rule

        # Will be populated with instances of all triggering sensors later
        self.triggered_by = []



    def enable(self):
        self.enabled = True

        # Enable self in sensor's targets dict
        for sensor in self.triggered_by:
            sensor.targets[self] = True


    def disable(self):
        self.enabled = False

        # Disable self in sensor's targets dict
        for sensor in self.triggered_by:
            sensor.targets[self] = False
