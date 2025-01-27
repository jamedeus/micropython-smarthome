import socket
import asyncio
from struct import pack
from DimmableLight import DimmableLight


class Tplink(DimmableLight):
    '''Driver for TP-Link Kasa dimmers and smart bulbs. Makes API calls to set
    power state and brightness when send method is called.

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
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
        super().__init__(name, nickname, _type, True, default_rule, schedule, min_rule, max_rule)

        self.ip = ip

        # Run monitor loop (requests status every 5 seconds to keep in sync if
        # user changes brightness from wall dimmer)
        self.monitor_task = asyncio.create_task(self.monitor())

        self.log.info("Instantiated, ip=%s", self.ip)

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

    def _check_brightness(self):
        '''Requests status object from Tplink device, parses current brightness
        and returns as integer.
        '''
        response = self._send_payload('{"system":{"get_sysinfo":{}}}')
        try:
            if self._type == "dimmer":
                return int(response.split('"brightness":')[1].split(',')[0])
            return int(response.split('"brightness":')[1].split('}')[0])
        except (AttributeError, IndexError, ValueError):
            self.log.error("Failed to parse brightness from: %s", response)
            return False

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
        '''Async coroutine that runs while device is enabled. Queries current
        brightness from Tplink device every 5 seconds and updates current_rule
        (allows user to change current_rule using dimmer on wall).
        '''
        self.log.debug("Starting Tplink.monitor coro")
        try:
            while True:
                brightness = self._check_brightness()
                if brightness and brightness != self.current_rule:
                    self.log.debug("monitor: current rule changed to %s", brightness)
                    self.current_rule = brightness

                # Poll every 5 seconds
                await asyncio.sleep(5)

        # Device disabled, exit loop
        except asyncio.CancelledError:
            self.log.debug("Exiting Tplink.monitor coro")
            return False
