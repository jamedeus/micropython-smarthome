import re
import requests
from Device import Device

# Regular expression matches domain or IP with optional port number and sub-path
uri_pattern = re.compile(
    r'(([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)|'
    r'((\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)))'
    r'(:\d\d?\d?\d?)?'
    r'(\/[a-zA-Z0-9\-._~!$&\'()*+,;=:@]+)*'
    r'$'
)


class HttpGet(Device):
    '''Base class for all devices which make an HTTP GET request when turned on
    or off. Inherits from Device and adds URI and path attributes (used to
    determine target URL) and send method (makes GET request).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      uri:          The base URL with no path
      on_path:      The path added to uri for ON action
      off_path:      The path added to uri for OFF action

    Can be used as a standalone device or subclassed by drivers which make
    HTTP GET requests and require additional methods.

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, uri, on_path, off_path):
        super().__init__(name, nickname, _type, True, default_rule, schedule)

        # Can be IP or domain, remove protocol if present
        self.uri = str(uri).replace('http://', '').replace('https://', '')

        # Prevent instantiating with invalid URI
        if not re.match(uri_pattern, self.uri):
            self.log.critical("Received invalid URI: %s", self.uri)
            raise AttributeError

        # Paths added to URI for on, off respectively
        self.on_path = on_path
        self.off_path = off_path

        # Remove leading / (prevent double)
        if self.on_path.startswith('/'):
            self.on_path = self.on_path[1:]
        if self.off_path.startswith('/'):
            self.off_path = self.off_path[1:]

        self.log.info("Instantiated, uri=%s", self.uri)

    def get_url(self, state):
        '''Returns URL for ON action if argument is True.
        Returns URL for OFF action if argument is False.
        '''
        if state:
            return f'http://{self.uri}/{self.on_path}'
        return f'http://{self.uri}/{self.off_path}'

    def request(self, url):
        '''Takes URL, makes request, returns response object'''

        return requests.get(url, timeout=2)

    def send(self, state=1):
        '''Makes request to ON action URL if argument is True.
        Makes request to OFF action URL if argument is False.
        '''
        self.log.debug(
            "send method called, rule=%s, state=%s",
            self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off (returning
        # True makes group set device state to True - allows turning off when
        # condition changes, would be skipped if device state already False)
        if not self.enabled and state:
            return True

        try:
            response = self.request(self.get_url(state))
            self.log.debug("response status: %s", response.status_code)
            if state:
                self.print("Turned on")
            else:
                self.print("Turned off")
        except OSError:
            # Wifi interruption, send failed
            self.log.error("send method failed (wifi error)")
            self.print(f"{self.name}: send failed (wifi error)")
            return False

        # Request succeeded if status code is 200
        return bool(response.status_code == 200)
