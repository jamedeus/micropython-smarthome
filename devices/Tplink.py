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

        # Stores parameters in dict when fade in progress
        self.fading = False

        log.info(f"Instantiated Tplink device named {self.name}: ip = {self.ip}, type = {self.device_type}")



    def set_rule(self, rule):
        # Check if rule is valid using subclass method - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)
        if str(valid_rule) == "False":
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

        elif str(valid_rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = valid_rule.split("/")

                # If first rule on boot is fade, set target as current_rule (animation probably overdue)
                if self.current_rule == None:
                    self.current_rule = int(target)
                    print(f"{self.name}: Rule changed to {self.current_rule}")
                    log.info(f"{self.name}: Rule changed to {self.current_rule}")
                    return True

                # If rule changes to fade after boot, start fade and return first step as current_rule
                print(f"{self.name}: fading to {target} in {period} seconds")
                log.info(f"{self.name}: fading to {target} in {period} seconds")

                if not self.current_rule == "Disabled":
                    # Get current brightness
                    brightness = int(self.current_rule)
                else:
                    # Default to 0 if device disabled when fade starts
                    brightness = 0

                if int(target) == brightness:
                    print("Already at target brightness, skipping fade")
                    log.info("Already at target brightness, skipping fade")
                    return True

                # Find fade direction, get number of steps, period between steps
                if int(target) > brightness:
                    steps = int(target) - brightness
                    fade_period = int(period) / steps * 1000

                elif int(target) < brightness:
                    steps = brightness - int(target)
                    fade_period = int(period) / steps * 1000

                # Ensure device is enabled
                self.enabled = True

                # Create fade timer
                SoftwareTimer.timer.create(fade_period, self.fade, self.name + "_fade")

                # Store fade parameters in dict, used by fade method below
                self.fading = {"started": SoftwareTimer.timer.epoch_now(), "starting_brightness": brightness, "target": int(target), "period": fade_period}

                # Return starting point (will be set as current rule by device.set_rule)
                return True

        else:
            self.current_rule = valid_rule
            print(f"{self.name}: Rule changed to {self.current_rule}")
            log.info(f"{self.name}: Rule changed to {self.current_rule}")

            # If fade in progress when rule changed, abort
            if self.fading:
                self.fading = False

            # Rule just changed to disabled
            if self.current_rule == "Disabled":
                self.send(0)
                self.disable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled == False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state == True:
                self.send(1)

            return True



    # TODO Maybe add a 3rd param "init=False" - will be omitted except by Config. If True, and rule is fade,
    # then check Config.schedule, see when fade was supposed to start, and calculate current position in fade
    def rule_validator(self, rule):
        try:
            if str(rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = rule.split("/")

                try:
                    int(target)
                    int(period)
                except ValueError:
                    return False

                if 0 <= int(target) <= 100:
                    return rule
                else:
                    return False

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

        # Abort if disabled mid-fade, or if called after fade complete
        if not self.enabled or not self.fading:
            return True

        # Fade to next step (unless fade already complete)
        if not self.fading["target"] == int(self.current_rule):

            # Use starting time, current time, and period (time for each step) to determine how many steps should have been taken
            steps = (SoftwareTimer.timer.epoch_now() - self.fading["started"]) // self.fading["period"]

            if self.fading["target"] > int(self.current_rule):
                new_rule = self.fading["starting_brightness"] + steps
                if new_rule > self.fading["target"]:
                    new_rule = self.fading["target"]

            elif self.fading["target"] < int(self.current_rule):
                new_rule = self.fading["starting_brightness"] + steps * -1
                if new_rule < self.fading["target"]:
                    new_rule = self.fading["target"]

            self.current_rule = int(new_rule)
            if self.state == True:
                self.send(1)

        # Check if fade complete after step
        if self.fading["target"] == int(self.current_rule):
            # Complete
            self.scheduled_rule = self.current_rule
            self.fading = False

            if self.current_rule == 0:
                self.state = False

        else:
            # Sleep until next step
            next_step = int(self.fading["period"] - ((SoftwareTimer.timer.epoch_now() - self.fading["started"]) % self.fading["period"]))
            SoftwareTimer.timer.create(next_step, self.fade, self.name + "_fade")
