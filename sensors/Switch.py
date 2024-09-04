# This module can be used with reed switches, toggle switches, push buttons, etc.
# Connect the switch with a ohm resister in series between an input pin and 3.3v pin

import logging
from machine import Pin
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Switch_Sensor")


class Switch(Sensor):
    '''Driver for switch connected to ESP32 input pin, other side of switch
    must be connected to +3.3v. Turns target devices on when switch is closed,
    turns devices off when switch is open.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      pin:          The ESP32 pin connected to the switch

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, targets, pin):
        super().__init__(name, nickname, _type, True, default_rule, targets)

        self.switch = Pin(int(pin), Pin.IN, Pin.PULL_DOWN)

        # Create hardware interrupt, refresh group when switch changes state
        self.switch.irq(handler=self.interrupt_handler, trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING)

        # Track whether switch open or closed (allows checking state via API)
        self.switch_closed = bool(self.switch.value())

        log.info("Instantiated switch sensor named %s", self.name)

    def interrupt_handler(self, _=None):
        '''Interrupt handler called when switch is opened or closed, turns
        target devices on or off depending on switch state.
        '''
        self.switch_closed = bool(self.switch.value())
        self.refresh_group()

    def condition_met(self):
        '''Returns True if switch is closed, False if switch is open.'''

        if self.switch.value():
            return True
        return False

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["switch"]
        return attributes
