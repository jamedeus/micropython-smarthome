import logging
import urequests
import uasyncio as asyncio
from Device import Device
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("Desktop_target")



class Desktop_target(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        log.info(f"Instantiated Desktop named {self.name}: ip = {self.ip}")



    def set_rule(self, rule):
        if rule == "on" or rule =="off":
            self.current_rule = rule
            log.info(f"Rule changed to {self.current_rule}")
            return True
        else:
            log.error(f"Failed to change rule to {rule}")
            return False



    def off(self):
        response = urequests.get('http://' + str(self.ip) + ':5000/idle_time')

        # Do not turn off screen unless user idle for >1 minute
        if int(response.json()["idle_time"]) > 5:
            print(f"{self.name}: Turned screen off")
            response = urequests.get('http://' + str(self.ip) + ':5000/off')
        else:
            print(f"{self.name}: User not idle, keeping screen on")



    def send(self, state=1):
        log.info(f"Desktop.send method called, ip = {self.ip}, state = {state}")

        if not self.enabled:
            log.info("Device is currently disabled, skipping")
            return True # Tell sensor that send succeeded so it doesn't retry forever

        # TODO disable instead? Prevents 100ms delay from log line
        if self.current_rule == "off" and state == 1:
            return True # Tell sensor that send succeeded so it doesn't retry forever

        else:
            if state:
                # Make sure a previous off command (has 5 sec delay) doesn't turn screen off immediately after turning on
                SoftwareTimer.timer.cancel(self.name)
                response = urequests.get('http://' + str(self.ip) + ':5000/on')
                print("Turned screen on")

            elif not state:
                # Give user 5 seconds to react before screen turns off
                SoftwareTimer.timer.create(5000, self.off, self.name)

                return True

            if response.status_code == 200:
                return True
            else:
                return False
