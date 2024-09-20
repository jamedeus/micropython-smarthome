import logging
import requests
from HttpGet import HttpGet

# Paths used by Tasmota to turn on, off
ON_PATH = 'cm?cmnd=Power%20On'
OFF_PATH = 'cm?cmnd=Power%20Off'


class TasmotaRelay(HttpGet):
    '''Driver for smart relays running Tasmota. Makes Tasmota API calls when
    send method called (turn ON if arg is True, turn OFF if arg is False).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      ip:           The IPv4 address of the Tasmota relay

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, ip):
        super().__init__(name, nickname, _type, default_rule, ip, ON_PATH, OFF_PATH)

        # Set name for module's log lines
        self.log = logging.getLogger("TasmotaRelay")

        self.log.info("Instantiated TasmotaRelay named %s: ip = %s", self.name, self.uri)

    def check_state(self):
        '''Makes API call to get Tasmota relay power state, return response'''

        try:
            return requests.get(
                f'http://{self.uri}/cm?cmnd=Power',
                timeout=2
            ).json()["POWER"]
        except OSError:
            self.log.error("%s: network error while checking state", self.name)
            return "Network Error"
