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
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            return True
        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            return False



    def off(self):
        try:
            response = urequests.get('http://' + str(self.ip) + ':5000/idle_time')

            # Do not turn off screen unless user idle for >1 minute
            if int(response.json()["idle_time"]) > 60000:
                print(f"{self.name}: Turned screen off")
                log.debug(f"{self.name}: Turned OFF")
                response = urequests.get('http://' + str(self.ip) + ':5000/off')
            else:
                print(f"{self.name}: User not idle, keeping screen on")
                log.debug(f"{self.name}: User not idle, keeping screen on")
        except OSError:
            # Wifi interruption, put back in timer queue for 5 seconds and try again
            SoftwareTimer.timer.create(5000, self.off, self.name)



    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        if not self.enabled:
            log.info(f"{self.name}: Device is currently disabled, skipping")
            return True # Tell sensor that send succeeded so it doesn't retry forever

        # TODO disable instead? Prevents 100ms delay from log line
        if self.current_rule == "off" and state == 1:
            return True # Tell sensor that send succeeded so it doesn't retry forever

        else:
            if state:
                # Make sure a previous off command (has 5 sec delay) doesn't turn screen off immediately after turning on
                SoftwareTimer.timer.cancel(self.name)
                try:
                    response = urequests.get('http://' + str(self.ip) + ':5000/on')
                    print(f"{self.name}: Turned screen on")
                    log.debug(f"{self.name}: Turned ON")
                except OSError:
                    # TODO make possible for timer to accept args, then add to timer queue instead of going back to main loop
                    #SoftwareTimer.timer.create(5000, self.send, self.name)
                    # Wifi interruption, send failed
                    return False

            elif not state:
                # Give user 5 seconds to react before screen turns off
                SoftwareTimer.timer.create(5000, self.off, self.name)

                return True

            if response.status_code == 200:
                return True
            else:
                return False
