import logging
from machine import Pin
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Mosfet")


class Mosfet(Device):
    '''Driver for mosfet used as a switch. Changes state of pin connected to
    mosfet when send method called (HIGH if arg is True, LOW if arg is False).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      pin:          The ESP32 pin connected to the mosfet

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, pin):
        super().__init__(name, nickname, _type, True, None, default_rule)

        self.mosfet = Pin(int(pin), Pin.OUT, Pin.PULL_DOWN)

        log.info(f"Instantiated Mosfet named {self.name} on pin {pin}")

    def send(self, state=1):
        '''Sets pin level HIGH if arg is True.
        Sets pin level LOW if arg is False.
        '''

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        self.mosfet.value(state)
        return True

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["mosfet"]
        return attributes
