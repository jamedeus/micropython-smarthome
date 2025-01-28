import socket
import asyncio
from struct import pack
from DimmableLight import DimmableLight
from DeviceWithLoop import DeviceWithLoop


class Tplink(DeviceWithLoop, DimmableLight):
    '''Driver for TP-Link Kasa dimmers and smart bulbs. Makes API calls to set
    power state and brightness when send method is called.

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      min_rule:     The minimum supported integer rule, used by rule validator
      max_rule:     The maximum supported integer rule, used by rule validator
      ip:           The IPv4 address of the TP-Link device

    The _type argument must be set to "dimmer" or "bulb" (determines API call
    syntax, bulbs and dimmers use different syntax).

    The min_rule and max_rule attributes determine the range of supported int
    rules. This can be used to remove a dimmer dead zone (often no brightness
    below around 25%, depending on the type of bulb controlled by the dimmer).
    The web frontend scales this range to 1-100 for visual consistency.

    Supports universal rules ("enabled" and "disabled"), brightness rules (int
    between 1-100), and fade rules (syntax: fade/target_rule/duration_seconds).
    The default_rule must be an integer or fade (not universal rule).
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, min_rule, max_rule, ip):
        DeviceWithLoop.__init__(self, name, nickname, _type, True, default_rule, schedule)
        DimmableLight.__init__(self, name, nickname, _type, True, default_rule, schedule, min_rule, max_rule)

        self.ip = ip

        # Run monitor loop (requests status every 5 seconds to keep in sync if
        # user changes brightness from wall dimmer)
        self.monitor_task = asyncio.create_task(self.monitor())

        self.log.info("Instantiated, ip=%s", self.ip)

    def set_rule(self, rule, scheduled=False):
        '''Takes new rule, validates, if valid sets as current_rule (and
        scheduled_rule if scheduled arg is True) and calls apply_new_rule.

        Args:
          rule:      The new rule, will be set as current_rule if valid
          scheduled: Optional, if True also sets scheduled_rule if rule valid

        If fade rule received (syntax: fade/target_rule/duration_seconds) calls
        _start_fade method (creates interrupts that run when each step is due).

        Aborts in-progress fade if it receives an integer rule that causes rule
        to move in opposite direction of fade (eg if new rule is greater than
        current_rule while fading down).
        '''
        return DimmableLight.set_rule(self, rule, scheduled)

    def rule_validator(self, rule):
        '''Accepts universal rules ("enabled" and "disabled"), integer rules
        between self.min_rule and self.max_rule, and rules that start gradual
        fade (syntax: fade/target_rule/duration_seconds).

        Takes rule, returns rule if valid (may return modified rule, eg cast to
        lowercase), return False if rule is invalid.

        Can be extended to support other rules by replacing the validator
        method (called if rule is neither "enabled" nor "disabled").
        '''
        return DimmableLight.rule_validator(self, rule)

    def encrypt(self, string):
        '''Encrypts an API call using TP-Link's very weak algorithm.'''

        key = 171
        result = pack(">I", len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result

    def decrypt(self, string):
        '''Decrypts an API call using TP-Link's very weak algorithm.'''

        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result

    def _send_payload(self, payload):
        '''Takes payload string, encrypts and sends to Tplink device IP.
        Returns decrypted response from Tplink device.
        '''
        self.log.debug("Sending payload: %s", payload)
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))

            sock_tcp.send(self.encrypt(payload))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            response = self.decrypt(data[4:])
            self.log.debug("Response: %s", response)

            return response

        except Exception as ex:
            self.print(f"Could not connect to host {self.ip}, exception: {ex}")
            self.log.error("Could not connect to host %s", self.ip)

            # Tell calling function that request failed
            return False

    def _parse_response(self, response):
        '''Takes decrypted response from Tplink device, returns False if the
        response contains an error, return True if no error.
        '''

        # Bool (returned when exception occurs in _send_payload)
        if isinstance(response, bool):
            return False
        # Empty object {} (returned when request syntax incorrect)
        if len(response) == 2:
            return False
        # Slice right after "err_code":, if next character is 0 no error
        if response[response.index('err_code') + 10:].startswith('0'):
            return True
        # If next character after "err_code": is not 0 an error occurred
        return False

    def _check_device_status(self):
        '''Requests status object from Tplink device, parses power state and
        current brightness, returns power state (bool) and brightness (int).
        '''
        response = self._send_payload('{"system":{"get_sysinfo":{}}}')
        try:
            if self._type == "dimmer":
                power = bool(int(response.split('"relay_state":')[1].split(',')[0]))
                brightness = int(response.split('"brightness":')[1].split(',')[0])
            else:
                power = bool(int(response.split('"on_off":')[1].split(',')[0]))
                brightness = int(response.split('"brightness":')[1].split('}')[0])
            return power, brightness
        except (AttributeError, IndexError, ValueError):
            self.log.error("Failed to parse status response: %s", response)
            raise RuntimeError  # pylint: disable=W0707

    def send(self, state=1):
        '''Makes API call to turn Tplink device ON if argument is True.
        Makes API call to turn Tplink device OFF if argument is False.
        Sets Tplink device brightness to current_rule.
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

        # Dimmer has separate brightness and on/off commands
        if self._type == "dimmer":
            if not self._parse_response(self._send_payload(
                '{"system":{"set_relay_state":{"state":'
                + str(state)
                + '}}}'
            )):
                return False
            if not self._parse_response(self._send_payload(
                '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":'
                + str(self.current_rule)
                + '}}}'
            )):
                return False

        # Bulb combines brightness and on/off into single command
        else:
            if not self._parse_response(self._send_payload(
                '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":'
                + str(state)
                + ',"transition_period":0,"brightness":'
                + str(self.current_rule)
                + '}}}'
            )):
                return False

        self.print(f"brightness = {self.current_rule}, state = {state}")
        self.log.debug("Success")

        # Tell calling function that request succeeded
        return True

    async def monitor(self):
        '''Async coroutine that runs while device is enabled. Queries power
        state and brightness from Tplink device every 5 seconds and updates
        self.state and self.current_rule respectively (keeps in sync with
        actual device when user uses dimmer on wall).
        '''
        self.log.debug("Starting Tplink.monitor coro")
        try:
            while True:
                try:
                    power, brightness = self._check_device_status()
                    if brightness != self.current_rule:
                        self.log.debug("monitor: current rule changed to %s", brightness)
                        self.current_rule = brightness
                    if power != self.state:
                        self.log.debug("monitor: power state changed to %s", power)
                        self.state = power
                except RuntimeError:
                    # Error during request, ignore
                    pass

                # Poll every 5 seconds
                await asyncio.sleep(5)

        # Device disabled, exit loop
        except asyncio.CancelledError:
            self.log.debug("Exiting Tplink.monitor coro")
            return False

    def get_status(self):
        '''Return JSON-serializable dict containing status information.
        Called by Config.get_status to build API status endpoint response.
        Contains all attributes displayed on the web frontend.
        '''
        return DimmableLight.get_status(self)
