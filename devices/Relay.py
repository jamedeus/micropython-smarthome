import logging
from machine import Pin
from Device import Device


class Relay(Device):
    '''Driver for relay breakout boards and other devices controlled by an
    output pin. Changes state of output pin connected to device when send
    method is called (HIGH if arg is True, LOW if arg is False).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      pin:          The ESP32 pin connected to the relay or other device

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, pin):
        super().__init__(name, nickname, _type, True, default_rule)

        # Set name for module's log lines
        self.log = logging.getLogger("Relay")

        self.output = Pin(int(pin), Pin.OUT, Pin.PULL_DOWN)

        self.log.info("Instantiated Relay named %s on pin %s", self.name, pin)

    def send(self, state=1):
        '''Sets pin level HIGH if arg is True.
        Sets pin level LOW if arg is False.
        '''
        self.log.debug(
            "%s: send method called, rule=%s, state=%s",
            self.name, self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        self.output.value(state)
        return True

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["output"]
        return attributes
