import socket
from struct import pack
import logging



# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Tplink")



# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink():
    def __init__(self, name, ip, device, current_rule):
        self.name = name
        self.ip = ip
        self.device = device
        self.current_rule = current_rule # The rule actually being followed
        self.scheduled_rule = current_rule # The rule scheduled for current time - may be overriden, stored here so can revert

        log.info("Created Tplink class instance named " + str(self.name) + ": ip = " + str(self.ip) + ", type = " + str(self.device))



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
        if self.device == "dimmer":
            cmd = '{"smartlife.iot.dimmer":{"set_brightness":{"brightness":' + str(self.current_rule) + '}}}'
        else:
            cmd = '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"ignore_default":1,"on_off":' + str(state) + ',"transition_period":0,"brightness":' + str(self.current_rule) + '}}}'

        # Send command and receive reply
        try:
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(10)
            sock_tcp.connect((self.ip, 9999))
            #sock_tcp.settimeout(None)
            log.debug("Connected")

            # Dimmer has seperate brightness and on/off commands, bulb combines into 1 command
            if self.device == "dimmer":
                sock_tcp.send(self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}')) # Set on/off state before brightness
                data = sock_tcp.recv(2048) # Dimmer wont listen for next command until it's reply is received
                log.debug("Sent state (dimmer)")

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
            log.debug("Sent brightness")
            data = sock_tcp.recv(2048)
            log.debug("Received reply")
            sock_tcp.close()

            decrypted = self.decrypt(data[4:]) # Remove in final version (or put in debug conditional)

            print("Sent:     ", cmd)
            print("Received: ", decrypted)

            return True # Tell calling function that request succeeded

        except: # Failed
            print(f"Could not connect to host {self.ip}")
            log.info("Could not connect to host " + str(self.ip))

            return False # Tell calling function that request failed
