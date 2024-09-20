import socket
import logging
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

    def __init__(self, name, nickname, _type, default_rule, min_rule, max_rule, ip):
        super().__init__(name, nickname, _type, True, default_rule, min_rule, max_rule)

        # Set name for module's log lines
        self.log = logging.getLogger("Tplink")

        self.ip = ip

        # Stores parameters in dict when fade in progress
        self.fading = False

        self.log.info(
            "Instantiated Tplink device named %s: ip = %s, type = %s",
            self.name, self.ip, self._type
        )

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

    def send(self, state=1):
        '''Makes API call to turn Tplink device ON if argument is True.
        Makes API call to turn Tplink device OFF if argument is False.
        Sets Tplink device brightness to current_rule.
        '''
        self.log.debug(
            "%s: send method called, rule=%s, state=%s",
            self.name, self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        if self._type == "dimmer":
            cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(self.current_rule) + '}}}'
        else:
            cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(self.current_rule) + '}}}'

        # Send command and receive reply
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))

            # Dimmer has separate brightness and on/off commands, bulb combines into 1 command
            if self._type == "dimmer":
                # Set on/off state, read response (dimmer won't listen for next
                # command until reply read)
                sock_tcp.send(
                    self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')
                )
                sock_tcp.recv(2048)

            # Set brightness, read response
            sock_tcp.send(self.encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            decrypted = self.decrypt(data[4:])
            self.log.debug("%s: Response: %s", self.name, decrypted)

            self.print(f"brightness = {self.current_rule}, state = {state}")
            self.log.debug("%s: Success", self.name)

            # Tell calling function that request succeeded
            return True

        except Exception as ex:
            self.print(f"Could not connect to host {self.ip}, exception: {ex}")
            self.log.error("%s: Could not connect to host %s", self.name, self.ip)

            # Tell calling function that request failed
            return False
