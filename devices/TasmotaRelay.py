import logging
import requests
from HttpGet import HttpGet

# Set name for module's log lines
log = logging.getLogger("TasmotaRelay")

# Paths used by Tasmota to turn on, off
on_path = 'cm?cmnd=Power%20On'
off_path = 'cm?cmnd=Power%20Off'


# Used for Sonoff relays running Tasmota
class TasmotaRelay(HttpGet):
    def __init__(self, name, nickname, _type, default_rule, ip):
        super().__init__(name, nickname, _type, default_rule, ip, on_path, off_path)

        log.info(f"Instantiated TasmotaRelay named {self.name}: ip = {self.uri}")

    def check_state(self):
        try:
            return requests.get(
                f'http://{self.uri}/cm?cmnd=Power',
                timeout=2
            ).json()["POWER"]
        except OSError:
            return "Network Error"
