import logging
import urequests
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Relay")



# Used for Sonoff relays running Tasmota
class Relay(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        log.info(f"Instantiated Relay named {self.name}: ip = {self.ip}")



    def set_rule(self, rule):
        if rule == "on" or rule =="off":
            self.current_rule = rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            return True
        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            return False



    def check_state(self):
        try:
            return urequests.get('http://' + str(self.ip) + '/cm?cmnd=Power').json()["POWER"]
        except OSError:
            return "Network Error"



    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        if not self.enabled:
            log.info(f"{self.name}: currently disabled, skipping")
            return True # Tell sensor that send succeeded so it doesn't retry forever

        if self.current_rule == "off" and state == 1:
            return True # Tell sensor that send succeeded so it doesn't retry forever
        else:

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
