from machine import Pin
from Device import Device



class Mosfet(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, pin):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.mosfet = Pin(pin, Pin.OUT, Pin.PULL_DOWN)



    def set_rule(self, rule):
        if rule == "on" or rule =="off":
            self.current_rule = rule
            return True
        else:
            return False



    def send(self, state=1):
        if self.current_rule == "off" and state == 1:
            pass
        else:
            self.mosfet.value(state)

        return True
