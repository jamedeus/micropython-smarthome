


class Sensor():
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):
        self.name = name

        self.sensor_type = sensor_type

        self.enabled = enabled

        self.current_rule = current_rule

        self.scheduled_rule = scheduled_rule

        self.targets = targets
