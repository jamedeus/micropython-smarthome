import json
import socket
import logging
import network
from Api import app
from Device import Device
from util import is_device, is_sensor, is_device_or_sensor

# Set name for module's log lines
log = logging.getLogger("ApiTarget")


class ApiTarget(Device):
    '''Software-only device driver that sends API calls to another node (or to
    self) when turned on and off. A separate API call can be configured for the
    on and off actions. Can be used to allow a sensor on one node to control a
    device on a second node in scenarios where connecting both to the same node
    is not practical (eg 2 motion sensors on opposite ends of a large room).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      ip:           The IPv4 address of the target node (can be own IP address)
      port:         Only used in unit testing (allows overridding the API port)

    Supports universal rules ("enabled" and "disabled") and dicts containing a
    pair of API calls (dict must contain "on" and "off" keys, each containing a
    list of params using the same syntax as api_client.py command line args).
    The default_rule must be a dict (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, ip, port=8123):
        super().__init__(name, nickname, _type, True, None, default_rule)

        # IP that API command is sent to
        self.ip = ip

        # Port defaults to 8123 except in unit tests
        self.port = port

        # IP of ESP32, used to detect self-target
        self.node_ip = None
        self.get_node_ip()

        # Prevent instantiating with invalid default_rule
        if str(self.default_rule).lower() in ("enabled", "disabled"):
            log.critical(
                "%s: Received invalid default_rule: %s",
                self.name, self.default_rule
            )
            raise AttributeError

    def get_node_ip(self):
        '''Returns own IPv4 address (stored in node_ip attribute). Sets node_ip
        attribute on first call.
        '''
        if self.node_ip is None:
            wlan = network.WLAN(network.WLAN.IF_STA)
            if wlan.isconnected():
                self.node_ip = wlan.ifconfig()[0]
        return self.node_ip

    def validator(self, rule):
        '''Accepts dict containing "on" and "off" keys. Each key must contain
        a list of parameters for a full API call, using the same syntax as
        api_client.py command line arguments.
        '''
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
            if i not in ["on", "off"]:
                return False

            # Check against all valid sub-rule patterns
            if not self.sub_rule_validator(rule[i]):
                return False

        # Iteration finished without a return False, rule is valid
        return rule

    def sub_rule_validator(self, rule):
        '''Takes sub-rule (contents of "on" or "off" key in full rule). Returns
        True if sub-rule contains a valid API call, returns False if invalid.
        '''
        if not isinstance(rule, list):
            return False

        # Endpoints that require no args
        # "ignore" is not a valid command, it allows only using on/off and ignoring the other
        if rule[0] in ['reboot', 'clear_log', 'ignore'] and len(rule) == 1:
            return True

        # Endpoints that require a device or sensor arg
        if rule[0] in ['enable', 'disable', 'reset_rule'] and len(rule) == 2 and is_device_or_sensor(rule[1]):
            return True

        # Endpoints that require a sensor arg
        if rule[0] in ['condition_met', 'trigger_sensor'] and len(rule) == 2 and is_sensor(rule[1]):
            return True

        # Endpoints that require a device arg
        if rule[0] in ['turn_on', 'turn_off'] and len(rule) == 2 and is_device(rule[1]):
            return True

        # Endpoints that require a device/sensor arg and int/float arg
        if rule[0] in ['enable_in', 'disable_in'] and len(rule) == 3 and is_device_or_sensor(rule[1]):
            try:
                float(rule[2])
                return True
            except ValueError:
                return False

        # Endpoint requires a device/sensor arg and rule arg
        # Rule arg not validated (device/sensor type not known), client returns error if invalid
        if rule[0] == 'set_rule' and len(rule) == 3 and is_device_or_sensor(rule[1]):
            return True

        # Endpoint requires IR target and IR key args
        # Target and keys not validated (client codes not known), client returns error if invalid
        if rule[0] == 'ir_key':
            if len(rule) == 3 and isinstance(rule[1], str) and isinstance(rule[2], str):
                return True
            return False

        # Did not match any valid patterns
        return False

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and updates attributes.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid

        If new rule is "disabled" turns device off.
        If new rule is "enabled" replaces with default_rule and calls enable.
        If device is already on calls send method so new rule takes effect.
        '''

        # Check if rule is valid - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)

        # Turn off target before changing rule to disabled
        # (cannot call send after changing, requires dict)
        if valid_rule == "disabled":
            self.send(0)

        if valid_rule is not False:
            self.current_rule = valid_rule
            if scheduled:
                self.scheduled_rule = valid_rule
            log.info("%s: Rule changed to %s", self.name, self.current_rule)
            self.print(f"Rule changed to {self.current_rule}")

            # Update instance attributes to reflect new rule
            self.apply_new_rule()

            return True

        log.error("%s: Failed to change rule to %s", self.name, rule)
        self.print(f"Failed to change rule to {rule}")
        return False

    def log_failed_request(self, msg, err):
        '''Called when an API call receives an error response. Takes full
        payload and response, writes multiline log with indent for readability.
        '''
        log.error("""%s: Send method failed
        Payload: %s
        Response: %s""", self.name, msg, err)
        self.print(f"Send method failed with payload {msg}")
        self.print(f"Response: {err}")

    def request(self, msg):
        '''Called by send method. Takes API command and sends to target IP.
        Returns True if request successful, False if request failed.
        '''
        s = socket.socket()
        s.settimeout(1)
        try:
            s.connect((self.ip, self.port))
            s.sendall(f'{json.dumps(msg)}\n'.encode())
            res = s.recv(1000).decode()
            res = json.loads(res)
        except (OSError, ValueError):
            res = False
        s.close()

        # Return False if request failed
        if not res:
            return False

        # Log payload + error and return False if response contains error
        if "Error" in res.keys() or "ERROR" in res.keys():
            self.log_failed_request(msg, res)
            return False

        # Return True if request successful
        return True

    def send(self, state=1):
        '''Sends API call in current_rule "on" key if argument is True.
        Sends API call in current_rule "off" key if argument is False.
        '''

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        # Prevent exception if current rule is string ("Disabled")
        # TODO fix incorrect API response if turn_off called while rule is Disabled
        if not isinstance(self.current_rule, dict):
            return True

        # Get correct command for state argument
        if state:
            command = self.current_rule["on"]
        else:
            command = self.current_rule["off"]

        # Return early if rule is "ignore"
        if command[0] == "ignore":
            return True

        # Send request, return False if failed
        if self.ip != self.get_node_ip():
            if not self.request(command):
                return False

        # Self targeting, pass request directly to API backend
        else:
            if not self.send_to_self(command):
                return False

        # If targeted by motion sensor: reset motion attribute after successful on command
        # Allows retriggering sensor to send again - otherwise motion only restarts reset timer
        # TODO does group.refresh break this?
        if state:
            for sensor in self.triggered_by:
                if sensor._type in ["pir", "ld2410"]:
                    sensor.motion = False

        # Tells group send succeeded
        return True

    def send_to_self(self, command):
        '''Called by send method (instead of request) when target IP is self.
        Passes current_rule directly to API backend without opening connection
        (request method is synchronous, blocks Api.run_client method).
        '''
        path = command[0]
        args = command[1:]

        try:
            reply = app.url_map[path](args)
        except KeyError:
            return False

        # Log payload + error and return False if response contains error
        if "Error" in reply.keys() or "ERROR" in reply.keys():
            self.log_failed_request(command, reply)
            return False

        # Return True if request successful
        return True
