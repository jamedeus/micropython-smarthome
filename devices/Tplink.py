import socket
from struct import pack
import logging
from Device import Device
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("Tplink")



# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        self.ip = ip

        # Stores target brightness during fade animation
        self.fade_target = None

        # Delay between each step in fade (ms)
        self.fade_period = None

        # Timestamp (ms) when fade began, used to catch up if something blocks
        self.fade_started = None

        # Starting brightness
        self.fade_start_bright = None

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

                    # Get current brightness
                    brightness = int(self.current_rule)

                    if int(target) == brightness:
                        print("Already at target brightness, skipping fade")
                        log.debug("Already at target brightness, skipping fade")
                        return int(target)

                    self.fade_target = int(target)

                    # Find fade direction, get number of steps, period between steps
                    if self.fade_target > brightness:
                        steps = self.fade_target - brightness
                        self.fade_period = int(period) / steps * 1000

                    elif self.fade_target < brightness:
                        steps = brightness - self.fade_target
                        self.fade_period = int(period) / steps * 1000

                    # Ensure device is enabled
                    self.enable()

                    self.fade_started = SoftwareTimer.timer.epoch_now()
                    self.fade_start_bright = brightness

                    SoftwareTimer.timer.create(self.fade_period, self.fade, "fade")

                    # Return starting point (will be set as current rule by device.set_rule)
                    return brightness

            elif rule == "Disabled":
                return rule

            elif 0 <= int(rule) <= 100:
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



    # Called by SoftwareTimer during fade animation, initialized in rule_validator above
    def fade(self):

        # Abort if disabled mid-fade
        if not self.enabled:
            return True

        if not self.fade_target == int(self.current_rule):

            # Use starting time, current time, and time for each step (fade_period) to determine how many steps should have been taken
            steps = (SoftwareTimer.timer.epoch_now() - self.fade_started) // self.fade_period

            if self.fade_target > int(self.current_rule):
                new_rule = int(self.fade_start_bright) + steps
                if new_rule > self.fade_target:
                    new_rule = self.fade_target

            elif self.fade_target < int(self.current_rule):
                new_rule = int(self.fade_start_bright) + steps * -1
                if new_rule < self.fade_target:
                    new_rule = self.fade_target

            self.set_rule(new_rule)

            # Sleep until next step
            next_step = int(self.fade_period - ((SoftwareTimer.timer.epoch_now() - self.fade_started) % self.fade_period))
            SoftwareTimer.timer.create(next_step, self.fade, "fade")

        else:
            # Animation complete
            self.scheduled_rule = self.current_rule
            self.fade_target = None
            self.fade_period = None
            self.fade_started = None
            self.fade_start_bright = None

            if self.current_rule == 0:
                self.state = False
