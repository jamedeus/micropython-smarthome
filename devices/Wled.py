import logging
import requests
from util import print_with_timestamp
from DimmableLight import DimmableLight

# Set name for module's log lines
log = logging.getLogger("WLED")


# Used for WLED instances, originally intended for monitor bias lights
class Wled(DimmableLight):
    def __init__(self, name, nickname, _type, default_rule, min_rule, max_rule, ip):
        super().__init__(name, nickname, _type, True, None, default_rule, min_rule, max_rule)

        self.ip = ip

        log.info(f"Instantiated Wled named {self.name}: ip = {self.ip}")

    # Returns JSON API payload to set power state and brightness
    # Power state set by argument, brightness set to current_rule
    def get_payload(self, state=True):
        if state:
            return {"on": True, "bri": self.current_rule}
        else:
            return {"on": False, "bri": self.current_rule}

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        try:
            response = requests.post(
                f'http://{self.ip}/json/state',
                json=self.get_payload(state),
                timeout=2
            )
            self.print(f"brightness = {self.current_rule}, state = {state}")
        except OSError:
            # Wifi error, send failed
            print_with_timestamp(f"{self.name}: send failed (wifi error)")
            log.info(f"{self.name}: send failed (wifi error)")
            return False

        if response.status_code == 200:
            return True
        else:
            return False
