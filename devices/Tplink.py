import socket
from struct import pack
import logging
from Device import Device
import SoftwareTimer
import time
import gc

# Set name for module's log lines
log = logging.getLogger("Tplink")



# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        # Where to stop
        self.fade_target = None

        log.info(f"Instantiated Tplink device named {self.name}: ip = {self.ip}, type = {self.device_type}")



    # TODO Maybe add a 3rd param "init=False" - will be omitted except by Config. If True, and rule is fade,
    # then check Config.schedule, see when fade was supposed to start, and calculate current position in fade
    def rule_validator(self, rule):
        try:
            if str(rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = rule.split("/")

                if self.current_rule == None:
                    # If first rule on boot is fade, set target as current_rule (animation probably overdue)
                    return int(target)
                else:
                    # If rule changes to fade after boot, start fade and return first step as current_rule
                    print(f"{self.name}: fading to {target} in {period} seconds")
                    log.debug(f"{self.name}: fading to {target} in {period} seconds")

                    # Find current brightness
                    if self.state:
                        brightness = int(self.current_rule)
                    else:
                        brightness = 0

                    first_step = brightness
                    self.current_rule = brightness

                    if int(target) == brightness:
                        print("Already at target brightness, skipping fade")
                        log.debug("Already at target brightness, skipping fade")
                        return int(target)

                    self.fade_target = int(target)

                    # Find fade direction, get number of steps, period between steps
                    if self.fade_target > brightness:
                        steps = self.fade_target - brightness
                        bright_step = 1
                        fade_period = int(period) / steps * 1000

                    elif self.fade_target < brightness:
                        steps = brightness - self.fade_target
                        bright_step = -1
                        fade_period = int(period) / steps * 1000

                    gc.collect()

                    # Create timer for each step in fade animation
                    next_step = 0
                    while self.fade_target != brightness:
                        brightness += bright_step
                        next_step += fade_period
                        SoftwareTimer.timer.create(next_step, self.fade, "fade")

                    # Ensure device is enabled
                    self.enable()

                    # Return starting point (will be set as current rule by device.set_rule)
                    return first_step

            elif rule == "Disabled":
                return rule

            elif 1 <= int(rule) <= 100:
                return int(rule)

            else:
                return False

        except ValueError:
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
        log.info(f"{self.name}: send method called, brightness={self.current_rule}, state={state}")

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

        except Exception as ex: # Failed
            print(f"Could not connect to host {self.ip}, exception: {ex}")
            log.info(f"{self.name}: Could not connect to host {self.ip}")

            return False # Tell calling function that request failed



    # Fade brightness from current to target over a period of n seconds (defaults to fade on over 30 min)
    def fade(self):

        # Stops fade if device disabled while in progress
        if not self.enabled:
            return True

        # Fade already started, called again by timer
        else:

            if self.fade_target > int(self.current_rule):
                self.current_rule = int(self.current_rule) + 1
                self.send(1)
                self.state = True

            elif self.fade_target < int(self.current_rule):
                self.current_rule = int(self.current_rule) - 1
                self.send(1)
                self.state = True

            if self.fade_target == int(self.current_rule):
                # Animation complete
                self.scheduled_rule = self.current_rule
                if self.current_rule == 0:
                    self.state = False
