import re
import json
import logging
import urequests
from Device import Device

# Set name for module's log lines
log = logging.getLogger("HttpGet")

url_pattern = re.compile(
    r'^(https?:\/\/)'  # Optional http or https
    r'(([a-zA-Z0-9-]+(\.[a-zA-Z0-9-]+)+)|'  # Either domain
    r'((\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)\.(\d\d?\d?)))'  # or IP
    r'(:\d\d?\d?\d?)?'  # Optional port number
    r'(\/[a-zA-Z0-9\-._~!$&\'()*+,;=:@]+)*'  # Optional sub-paths
    r'(\?[a-zA-Z0-9_&=.-]*)?'  # Optional querystring
    r'$'
)


# Sends Http GET request
class HttpGet(Device):
    def __init__(self, name, nickname, _type, default_rule,):
        super().__init__(name, nickname, _type, True, None, default_rule)

        # Prevent instantiating with invalid default rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError

        log.info(f"Instantiated HttpGet named {self.name}")

    # Takes dict containing 2 entries named "on" and "off"
    # Both entries must contain a valid URL
    # "on" sent when self.send(1) called, "off" when self.send(0) called
    def validator(self, rule):
        if isinstance(rule, str):
            try:
                # Convert string rule to dict (if received from API)
                rule = json.loads(rule)
            except (TypeError, ValueError, OSError):
                return False

        if not isinstance(rule, dict):
            return False

        # Reject if more than 2 sub-rules
        if not len(rule) == 2:
            return False

        for i in rule:
            # Index must be "on" or "off"
            if not i == "on" and not i == "off":
                return False

            # Value must be a valid URL
            if not re.match(url_pattern, str(rule)):
                return False

        else:
            # Iteration finished without a return False, rule is valid
            return rule

    def send(self, state=1):
        log.info(f"{self.name}: send method called, state = {state}")

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        # Get correct sub rule
        if state:
            url = self.current_rule["on"]
        else:
            url = self.current_rule["off"]

        # Send request
        try:
            response = urequests.get(url)
        except OSError:
            # Wifi interruption, send failed
            return False

        if response.status_code == 200:
            return True
        else:
            return False
