import logging
from HttpGet import HttpGet

# Set name for module's log lines
log = logging.getLogger("DesktopTarget")


class DesktopTarget(HttpGet):
    '''Driver for Linux computers running desktop-integration daemon. Makes API
    call to turn computer screen on/off when send method is called.

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      ip:           The IPv4 address of the Linux computer
      port:         The port that the daemon is listening on (default=5000)

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, ip, port=5000):
        super().__init__(name, nickname, _type, default_rule, f"{ip}:{port}", "on", "off")

        log.info("Instantiated Desktop named %s: uri = %s", self.name, self.uri)

    def send(self, state=1):
        '''Makes API call to turn screen ON if argument is True.
        Makes API call to turn screen OFF if argument is False.
        '''
        log.debug(
            "%s: send method called, rule=%s, state=%s",
            self.name, self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        try:
            response = self.request(self.get_url(state))
            log.debug("%s: response status: %s", self.name, response.status_code)
            if response.status_code == 200:
                if state:
                    self.print("Turned on")
                else:
                    self.print("Turned off")
                return True
            # Off command 503 response indicates user is not idle
            if response.status_code == 503 and not state:
                self.print("User not idle, keeping screen on")
                return True
            # Unexpected status code
            raise ValueError
        except OSError:
            # Wifi interruption, send failed
            log.error("%s: send failed (wifi error)", self.name)
            return False
        except ValueError:
            # Unexpected response (different service running on port 5000), disable
            if self.enabled:
                self.print("Fatal error (unexpected response from desktop), disabling")
                log.critical(
                    "%s: Fatal error (unexpected response from desktop), disabling",
                    self.name
                )
                self.disable()

        return False
