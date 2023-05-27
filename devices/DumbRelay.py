import logging
from machine import Pin
from Device import Device

# Set name for module's log lines
log = logging.getLogger("DumbRelay")


# Used for relay breakout board
class DumbRelay(Device):
    def __init__(self, name, nickname, _type, default_rule, pin):
        super().__init__(name, nickname, _type, True, None, default_rule)

        self.relay = Pin(int(pin), Pin.OUT)

        log.info(f"Instantiated Relay named {self.name} on pin {pin}")

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        self.relay.value(state)
        return True
