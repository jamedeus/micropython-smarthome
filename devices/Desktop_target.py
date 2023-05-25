import logging
import urequests
from Device import Device
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("Desktop_target")


class Desktop_target(Device):
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule, ip):
        super().__init__(name, nickname, device_type, enabled, current_rule, default_rule)

        self.ip = ip

        log.info(f"Instantiated Desktop named {self.name}: ip = {self.ip}")

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
        except ValueError:
            # Response doesn't contain JSON (different service running on port 5000), disable
            if self.enabled:
                print(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                log.info(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                self.disable()

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        if state:
            # Make sure a previous off command (has 5 sec delay) doesn't turn screen off immediately after turning on
            SoftwareTimer.timer.cancel(self.name)
            try:
                response = urequests.get('http://' + str(self.ip) + ':5000/on')
                if response.status_code != 200:
                    raise ValueError
                print(f"{self.name}: Turned screen on")
                log.debug(f"{self.name}: Turned ON")
            except OSError:
                # TODO make timer accept callback with args, then add to timer queue instead of going back to main loop
                #SoftwareTimer.timer.create(5000, self.send, self.name)
                # Wifi interruption, send failed
                return False
            except ValueError:
                # Response doesn't contain JSON (different service running on port 5000), disable
                if self.enabled:
                    print(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                    log.info(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                    self.disable()

        elif not state:
            # Give user 5 seconds to react before screen turns off
            SoftwareTimer.timer.create(5000, self.off, self.name)

            return True

        if response.status_code == 200:
            return True
        else:
            return False
