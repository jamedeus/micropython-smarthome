import logging
import urequests
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Relay")


# Used for Sonoff relays running Tasmota
class Relay(Device):
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule, ip):
        super().__init__(name, nickname, device_type, enabled, current_rule, default_rule)

        self.ip = ip

        log.info(f"Instantiated Relay named {self.name}: ip = {self.ip}")

    def check_state(self):
        try:
            return urequests.get('http://' + str(self.ip) + '/cm?cmnd=Power').json()["POWER"]
        except OSError:
            return "Network Error"

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        if state:
            try:
                response = urequests.get('http://' + str(self.ip) + '/cm?cmnd=Power%20On')
                print(f"{self.name}: Turned on")
            except OSError:
                # Wifi interruption, send failed
                return False

        elif not state:
            try:
                response = urequests.get('http://' + str(self.ip) + '/cm?cmnd=Power%20Off')
                print(f"{self.name}: Turned off")
            except OSError:
                # Wifi interruption, send failed
                return False

        if response.status_code == 200:
            return True
        else:
            return False
