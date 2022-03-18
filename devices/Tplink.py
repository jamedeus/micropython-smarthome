import socket
from struct import pack
import logging
from Device import Device

# Set name for module's log lines
log = logging.getLogger("Tplink")



# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        log.info(f"Instantiated Tplink device named {self.name}: ip = {self.ip}, type = {self.device_type}")



    def set_rule(self, rule):
        try:
            if 1 <= int(rule) <= 100:
                self.current_rule = int(rule)
                log.info(f"Rule changed to {self.current_rule}")
                return True
            else:
                log.error(f"Failed to change rule to {rule}")
                return False
        except ValueError:
            log.error(f"Failed to change rule to {rule}")
            return False



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
        log.info("Tplink.send method called, IP=" + str(self.ip) + ", Brightness=" + str(self.current_rule) + ", state=" + str(state))
        if self.device_type == "dimmer":
            cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(self.current_rule) + '}}}'
        else:
            cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(self.current_rule) + '}}}'

        # Send command and receive reply
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))

            # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
            if self.device_type == "dimmer":
                sock_tcp.send(self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')) # Set on/off state before brightness
                data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            decrypted = self.decrypt(data[4:]) # Remove in final version (or put in debug conditional)

            print(f"{self.name}: brightness = {self.current_rule}, state = {state}")
            log.debug("Success")

            return True # Tell calling function that request succeeded

        except: # Failed
            print(f"Could not connect to host {self.ip}")
            log.info("Could not connect to host " + str(self.ip))

            return False # Tell calling function that request failed
