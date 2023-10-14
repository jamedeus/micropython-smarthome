import logging
from HttpGet import HttpGet

# Set name for module's log lines
log = logging.getLogger("Desktop_target")


class Desktop_target(HttpGet):
    def __init__(self, name, nickname, _type, default_rule, ip, port=5000):
        super().__init__(name, nickname, _type, default_rule, f"{ip}:{port}", "on", "off")

        log.info(f"Instantiated Desktop named {self.name}: uri = {self.uri}")

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        try:
            response = self.request(self.get_url(state))
            if response.status_code == 200:
                if state:
                    print(f"{self.name}: Turned on")
                else:
                    print(f"{self.name}: Turned off")
                return True
            # Off command 503 response indicates user is not idle
            elif response.status_code == 503 and not state:
                print(f"{self.name}: User not idle, keeping screen on")
                return True
            else:
                raise ValueError
        except OSError:
            # Wifi interruption, send failed
            return False
        except ValueError:
            # Unexpected response (different service running on port 5000), disable
            if self.enabled:
                print(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                log.info(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
                self.disable()

        return False
