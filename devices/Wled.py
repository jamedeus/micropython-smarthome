import logging
import requests
from util import print_with_timestamp
from DimmableLight import DimmableLight

# Set name for module's log lines
log = logging.getLogger("WLED")


class Wled(DimmableLight):
    '''Driver for WLED instances. Makes API calls to set power state and
    brightness when send method is called. Does not support changing color or
    effects (must be pre-configured with WLED interface).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      min_rule:     The minimum supported integer rule, used by rule validator
      max_rule:     The maximum supported integer rule, used by rule validator
      ip:           The IPv4 address of the TP-Link device

    The min_rule and max_rule attributes determine the range of supported int
    rules. This can be used to remove very low duty cycles from the supported
    range if they are too dim or cause flickering. The web frontend scales this
    range to 1-100 for visual consistency.

    Supports universal rules ("enabled" and "disabled"), brightness rules (int
    between 1-255), and fade rules (syntax: fade/target_rule/duration_seconds).
    The default_rule must be an integer or fade (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, min_rule, max_rule, ip):
        super().__init__(name, nickname, _type, True, None, default_rule, min_rule, max_rule)

        self.ip = ip

        log.info(f"Instantiated Wled named {self.name}: ip = {self.ip}")

    def get_payload(self, state=True):
        '''Returns WLED API payload (JSON) to set power state and brightness.
        Power state is set by state argument, brightness set to current_rule.
        '''
        if state:
            return {"on": True, "bri": self.current_rule}
        else:
            return {"on": False, "bri": self.current_rule}

    def send(self, state=1):
        '''Makes API call to turn WLED instance ON if argument is True.
        Makes API call to turn WLED instance OFF if argument is False.
        Sets WLED instance brightness to current_rule.
        '''
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
