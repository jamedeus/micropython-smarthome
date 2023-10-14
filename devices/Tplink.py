import socket
import logging
from struct import pack
from DimmableLight import DimmableLight

# Set name for module's log lines
log = logging.getLogger("Tplink")


# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(DimmableLight):
    def __init__(self, name, nickname, _type, default_rule, min_rule, max_rule, ip):
        super().__init__(name, nickname, _type, True, None, default_rule, min_rule, max_rule)

        self.ip = ip

        # Stores parameters in dict when fade in progress
        self.fading = False

        log.info(f"Instantiated Tplink device named {self.name}: ip = {self.ip}, type = {self._type}")

    # Encrypt messages to tp-link smarthome devices
    def encrypt(self, string):
        key = 171
        result = pack(">I", len(string))
        for i in string:
            a = key ^ ord(i)
            key = a
            result += bytes([a])
        return result

    # Decrypt messages from tp-link smarthome devices
    def decrypt(self, string):
        key = 171
        result = ""
        for i in string:
            a = key ^ i
            key = i
            result += chr(a)
        return result

    def send(self, state=1):
        log.info(f"{self.name}: send method called, brightness={self.current_rule}, state={state}")

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

            # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
            if self._type == "dimmer":
                # Set on/off state, read response (dimmer wont listen for next command until reply read)
                sock_tcp.send(self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}'))
                data = sock_tcp.recv(2048)

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            decrypted = self.decrypt(data[4:])  # Remove in final version (or put in debug conditional)

            self.print(f"brightness = {self.current_rule}, state = {state}")
            log.debug(f"{self.name}: Success")

            # Tell calling function that request succeeded
            return True

        except Exception as ex:
            self.print(f"Could not connect to host {self.ip}, exception: {ex}")
            log.info(f"{self.name}: Could not connect to host {self.ip}")

            # Tell calling function that request failed
            return False
