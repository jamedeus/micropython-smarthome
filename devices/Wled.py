import logging
import urequests
from DimmableLight import DimmableLight

# Set name for module's log lines
log = logging.getLogger("WLED")


# Used for WLED instances, originally intended for monitor bias lights
class Wled(DimmableLight):
    def __init__(self, name, nickname, _type, default_rule, min_bright, max_bright, ip):
        super().__init__(name, nickname, _type, True, None, default_rule, min_bright, max_bright)

        self.ip = ip

        log.info(f"Instantiated Wled named {self.name}: ip = {self.ip}")

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        try:
            response = urequests.get(f'http://{self.ip}/win&A={self.current_rule}&T={state}')
            print(f"{self.name}: brightness = {self.current_rule}, state = {state}")
        except OSError:
            # Wifi interruption, send failed
            return False

        if response.status_code == 200:
            return True
        else:
            return False
