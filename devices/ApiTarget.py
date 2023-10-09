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
            log.critical(f"{self.name}: Received invalid default_rule: {self.default_rule}")
            raise AttributeError

    # Returns node_ip attribute (sets attribute on first call)
    def get_node_ip(self):
        if self.node_ip is None:
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                self.node_ip = wlan.ifconfig()[0]
        return self.node_ip

    # Takes dict containing 2 entries named "on" and "off"
    # Both entries are lists containing a full API request
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

            # Check against all valid sub-rule patterns
            if not self.sub_rule_validator(rule[i]):
                return False

        else:
            # Iteration finished without a return False, rule is valid
            return rule

    # Takes sub-rule (on or off), returns True if valid, False if invalid
    def sub_rule_validator(self, rule):
        if not isinstance(rule, list):
            return False

        # Endpoints that require no args
        # "ignore" is not a valid command, it allows only using on/off and ignoring the other
        if rule[0] in ['reboot', 'clear_log', 'ignore'] and len(rule) == 1:
            return True

        # Endpoints that require a device or sensor arg
        elif rule[0] in ['enable', 'disable', 'reset_rule'] and len(rule) == 2 and is_device_or_sensor(rule[1]):
            return True

        # Endpoints that require a sensor arg
        elif rule[0] in ['condition_met', 'trigger_sensor'] and len(rule) == 2 and is_sensor(rule[1]):
            return True

        # Endpoints that require a device arg
        elif rule[0] in ['turn_on', 'turn_off'] and len(rule) == 2 and is_device(rule[1]):
            return True

        # Endpoints that require a device/sensor arg and int/float arg
        elif rule[0] in ['enable_in', 'disable_in'] and len(rule) == 3 and is_device_or_sensor(rule[1]):
            try:
                float(rule[2])
                return True
            except ValueError:
                return False

        # Endpoint requires a device/sensor arg and rule arg
        # Rule arg not validated (device/sensor type not known), client returns error if invalid
        elif rule[0] == 'set_rule' and len(rule) == 3 and is_device_or_sensor(rule[1]):
            return True

        # Endpoint requires IR target and IR key args
        # Target and keys not validated (configured codes not known), client returns error if invalid
        elif rule[0] == 'ir_key':
            if len(rule) == 3 and type(rule[1]) == str and type(rule[2]) == str:
                return True
            else:
                return False

        else:
            # Did not match any valid patterns
            return False

    def set_rule(self, rule):
        # Check if rule is valid - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)

        # Turn off target before changing rule to disabled (cannot call send after changing, requires dict)
        if valid_rule == "disabled":
            self.send(0)

        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled is False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state is True:
                self.send(1)

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

    # Takes payload and response, writes multiline log with indent for readability
    def log_failed_request(self, msg, err):
        log.error(f"""{self.name}: Send method failed
        Payload: {msg}
        Response: {err}""")
        print(f"{self.name}: Send method failed with payload {msg}")
        print(f"{self.name}: Response: {err}")

    def request(self, msg):
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
        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        # Prevent exception if current rule is string ("Disabled")
        # TODO fix incorrect API response if turn_off called while rule is Disabled
        elif type(self.current_rule) != dict:
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

        # Self targetting, pass request directly to API backend
        else:
            if not self.send_to_self(command):
                return False

        # If targeted by motion sensor: reset motion attribute after successful on command
        # Allows retriggering sensor to send again - otherwise motion only restarts reset timer
        # TODO does group.refresh break this?
        if state:
            for sensor in self.triggered_by:
                if sensor._type == "pir":
                    sensor.motion = False

        # Tells group send succeeded
        return True

    # Passes current_rule directly to API backend without opening connection
    # Synchronous request method blocks API.run_client when self-targetting
    def send_to_self(self, command):
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
