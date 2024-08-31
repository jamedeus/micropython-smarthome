import logging
from machine import Pin
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Mosfet")


class Mosfet(Device):
    def __init__(self, name, nickname, _type, default_rule, pin):
        super().__init__(name, nickname, _type, True, None, default_rule)

        self.mosfet = Pin(int(pin), Pin.OUT, Pin.PULL_DOWN)

        log.info(f"Instantiated Mosfet named {self.name} on pin {pin}")

    def send(self, state=1):
        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        self.mosfet.value(state)
        return True

    # Return JSON-serializable dict containing all current attributes
    # Called by API get_attributes endpoint, more verbose than status
    def get_attributes(self):
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["mosfet"]
        return attributes
