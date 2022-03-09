import uasyncio as asyncio


class Sensor():
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets):
        self.name = name

        self.sensor_type = sensor_type

        self.enabled = enabled

        self.current_rule = current_rule

        self.scheduled_rule = scheduled_rule

        self.targets = targets



    def enable(self):
        self.enabled = True
        if not self.loop_started == True:
            self.loop_started = True
            asyncio.create_task(self.loop())



    def disable(self):
        self.enabled = False
        self.loop_started = False # Loop checks this variable, kills asyncio task if False
