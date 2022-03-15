import uasyncio as asyncio



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

        # Dictionary, keys are device instances, value is True/False for Enabled/Disabled
        self.targets = targets

        # Remember if loop is running (prevents multiple asyncio tasks running same loop)
        self.loop_started = False



    # Each sub-class has a different loop, all can be started/stopped with .enable()/.disable() syntax
    def enable(self):
        self.enabled = True
        if not self.loop_started == True:
            self.loop_started = True
            asyncio.create_task(self.loop())



    def disable(self):
        self.enabled = False
        self.loop_started = False # Loop checks this variable, kills asyncio task if False



    def next_rule(self):
        self.scheduled_rule = self.rule_queue.pop(0)
        self.current_rule = self.scheduled_rule
