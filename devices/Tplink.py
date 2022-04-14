import socket
from struct import pack
import logging
from Device import Device
import SoftwareTimer
import time

# Set name for module's log lines
log = logging.getLogger("Tplink")



# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        # Remember if fade animation is in progress
        self.fading = False

        # How often to increment
        self.fade_period = None

        # Where to stop
        self.fade_target = None

        log.info(f"Instantiated Tplink device named {self.name}: ip = {self.ip}, type = {self.device_type}")



    def set_rule(self, rule):
        try:
            if 1 <= int(rule) <= 100:
                self.current_rule = int(rule)
                log.info(f"{self.name}: Rule changed to {self.current_rule}")
                return True
            else:
                log.error(f"{self.name}: Failed to change rule to {rule}")
                return False
        except ValueError:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            return False



    def next_rule(self):
        if not str(self.rule_queue[0]).startswith("fade"):
            super().next_rule()
        else:
            # Parse parameters from rule
            cmd, target, period = self.rule_queue.pop(0).split("/")

            # Ensure device is enabled - do not call method, flips state and interferes with brightness check in fade
            self.enabled = True

            # Start fade animation
            self.fade(target, period)



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

        # TODO Temporary fix, prevents crash if current rule = fade when node boots. Find better solution
        try:
            int(self.current_rule)
        except ValueError:
            # Override with sane default
            self.current_rule = 50

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
            log.debug(f"{self.name}: Success")

            return True # Tell calling function that request succeeded

        except: # Failed
            print(f"Could not connect to host {self.ip}")
            log.info(f"{self.name}: Could not connect to host {self.ip}")

            return False # Tell calling function that request failed



    # Fade brightness from current to target over a period of n seconds (defaults to fade on over 30 min)
    def fade(self, target=98, period=1800):

        # Stops fade if device disabled while in progress
        if not self.enabled:
            return True



        # First time func called
        if not self.fading:
            print(f"{self.name}: fading to {target} in {period} seconds")

            # Find current brightness
            if self.state:
                brightness = int(self.current_rule)
            else:
                brightness = 0

            # Get delay between steps, set current_rule for first step
            if int(target) > brightness:
                steps = int(target) - brightness
                self.fade_period = float(period) / steps * 1000
                self.current_rule = int(self.current_rule) + 1

            elif int(target) < brightness:
                steps = brightness - int(target)
                self.fade_period = float(period) / steps * 1000
                self.current_rule = int(self.current_rule) - 1

            elif int(target) == brightness:
                print("Already at target brightness, skipping fade")
                # Already at target brightness, do nothing
                return True

            self.fade_target = int(target)
            self.fading = True

            # Let memory allocate before calling send
            time.sleep_ms(100)

            # First fade step
            self.send(1)

            # Create callback, will go to else now that self.fading = True
            SoftwareTimer.timer.create(self.fade_period, self.fade, "scheduler")



        # Fade already started, called again by timer
        else:

            if self.fade_target > int(self.current_rule):
                self.current_rule = int(self.current_rule) + 1
                self.send(1)

            elif self.fade_target < int(self.current_rule):
                self.current_rule = int(self.current_rule) - 1
                self.send(1)

            if self.fade_target == int(self.current_rule):
                # Animation complete
                self.scheduled_rule = self.current_rule
                self.fading = False
                return True
            else:
                SoftwareTimer.timer.create(self.fade_period, self.fade, "scheduler")
