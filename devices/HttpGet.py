import re
import logging
import urequests
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Http")

# Regular expression matches domain or IP with optional port number and sub-path
uri_pattern = re.compile(
    r'(([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)|'
    r'((\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)))'
    r'(:\d\d?\d?\d?)?'
    r'(\/[a-zA-Z0-9\-._~!$&\'()*+,;=:@]+)*'
    r'$'
)


# Extensible base class for devices that make HTTP requests
# Takes URI (can be IP or domain) and 2 paths which are appended
# to the URI for on and off commands respectively. Subclasses
# should hardcode the on and off paths where possible to avoid
# error-prone user configuration.
class HttpGet(Device):
    def __init__(self, name, nickname, _type, default_rule, uri, on_path, off_path):
        super().__init__(name, nickname, _type, True, None, default_rule)

        # Can be IP or domain, remove protocol if present
        self.uri = str(uri).replace('http://', '').replace('https://', '')

        # Prevent instantiating with invalid URI
        if not re.match(uri_pattern, self.uri):
            log.critical(f"{self.name}: Received invalid URI: {self.uri}")
            raise AttributeError

        # Paths added to URI for on, off respectively
        self.on_path = on_path
        self.off_path = off_path

        log.info(f"Instantiated HttpGet named {self.name}: URI = {self.uri}")

    # Takes bool, returns on and off URLs for True and False respectively
    def get_url(self, state):
        if state:
            return f'http://{self.uri}/{self.on_path}'
        else:
            return f'http://{self.uri}/{self.off_path}'

    # Takes URL, makes request, returns response object
    def request(self, url):
        return urequests.get(url)

    # Takes bool, turns on if True, turns off if False
    # Returns True if HTTP response is 200, otherwise returns False
    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        try:
            response = self.request(self.get_url(state))
            if state:
                self.print("Turned on")
            else:
                self.print("Turned off")
        except OSError:
            # Wifi interruption, send failed
            return False

        if response.status_code == 200:
            return True
        else:
            return False
