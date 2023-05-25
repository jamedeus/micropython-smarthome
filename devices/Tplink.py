import socket
from struct import pack
import logging
from Device import Device
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("Tplink")


# Used to control TP-Link Kasa dimmers + smart bulbs
class Tplink(Device):
    def __init__(self, name, nickname, device_type, enabled, current_rule, default_rule, ip):
        super().__init__(name, nickname, device_type, enabled, current_rule, default_rule)

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
            if self.current_rule is None:
                self.current_rule = int(target)
                print(f"{self.name}: Rule changed to {self.current_rule}")
                log.info(f"{self.name}: Rule changed to {self.current_rule}")
                return True

            # If rule changes to fade after boot, start fade and return first step as current_rule
            print(f"{self.name}: fading to {target} in {period} seconds")
            log.info(f"{self.name}: fading to {target} in {period} seconds")

            if not self.current_rule == "disabled":
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
            self.fading = {
                "started": SoftwareTimer.timer.epoch_now(),
                "starting_brightness": brightness,
                "target": int(
                    target
                ),
                "period": fade_period
            }

            # Store fade direction, determines if fade aborts when user changes brightness
            if self.fading["target"] < self.fading["starting_brightness"]:
                self.fading["down"] = True
            else:
                self.fading["down"] = False

            # Return starting point (will be set as current rule by device.set_rule)
            return True

        else:
            # Abort fade if user changed brightness in opposite direction
            if self.fading:
                if self.fading["down"] and valid_rule > self.current_rule:
                    self.fading = False
                elif not self.fading["down"] and valid_rule < self.current_rule:
                    self.fading = False

            self.current_rule = valid_rule
            print(f"{self.name}: Rule changed to {self.current_rule}")
            log.info(f"{self.name}: Rule changed to {self.current_rule}")

            # Abort fade if new rule exceeded target
            self.fade_complete()

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                self.send(0)
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Device was previously disabled, enable now that rule has changed
            elif self.enabled is False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state is True:
                self.send(1)

            return True

    # TODO Maybe add a 3rd param "init=False" - will be omitted except by Config. If True, and rule is fade,
    # then check Config.schedule, see when fade was supposed to start, and calculate current position in fade
    def validator(self, rule):
        try:
            if str(rule).startswith("fade"):
                # Parse parameters from rule
                cmd, target, period = rule.split("/")

                if int(period) < 0:
                    return False

                if 0 <= int(target) <= 100:
                    return rule
                else:
                    return False

            # Reject "False" before reaching conditional below (would cast False to 0 and accept as valid rule)
            elif isinstance(rule, bool):
                return False

            elif 0 <= int(rule) <= 100:
                return int(rule)

            else:
                return False

        except (ValueError, TypeError):
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

        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

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
                # Set on/off state, read response (dimmer wont listen for next command until reply read)
                sock_tcp.send(self.encrypt('{"system":{"set_relay_state":{"state":' + str(state) + '}}}'))
                data = sock_tcp.recv(2048)

            # Set brightness
            sock_tcp.send(self.encrypt(cmd))
            data = sock_tcp.recv(2048)
            sock_tcp.close()

            decrypted = self.decrypt(data[4:])  # Remove in final version (or put in debug conditional)

            print(f"{self.name}: brightness = {self.current_rule}, state = {state}")
            log.debug(f"{self.name}: Success")

            # Tell calling function that request succeeded
            return True

        except Exception as ex:
            print(f"Could not connect to host {self.ip}, exception: {ex}")
            log.info(f"{self.name}: Could not connect to host {self.ip}")

            # Tell calling function that request failed
            return False

    # Cleanup and return True if fade is complete, return False if not
    # Fade is complete when current_rule matches or exceeds fade target
    # A user-changed rule will stop the fade, but will not overwrite scheduled_rule (target used)
    # TODO user-initiated fade will break scheduled_rule
    def fade_complete(self):
        # Fade complete if device disabled mid-fade, or called when not fading
        if not self.enabled or not self.fading:
            self.fading = False
            return True

        # When fading down: complete if current_rule equal or less than target
        if self.fading["down"] and self.current_rule <= self.fading["target"]:
            self.scheduled_rule = self.fading["target"]
            self.fading = False

            if self.current_rule == 0:
                self.state = False
            return True

        # When fading up: complete if current_rule equal or greater than target
        elif not self.fading["down"] and self.current_rule >= self.fading["target"]:
            self.scheduled_rule = self.fading["target"]
            self.fading = False
            return True

        # Fade not complete
        else:
            return False

    # Called by SoftwareTimer during fade animation, initialized in rule_validator above
    def fade(self):
        # Fade to next step (unless fade already complete)
        if not self.fade_complete():
            # Use starting time, current time, period (time per step) to determine how many steps should have been taken
            steps = (SoftwareTimer.timer.epoch_now() - self.fading["started"]) // self.fading["period"]

            # Fading up
            if not self.fading["down"]:
                new_rule = self.fading["starting_brightness"] + steps
                if new_rule > self.fading["target"]:
                    new_rule = self.fading["target"]

            # Fading down
            elif self.fading["down"]:
                new_rule = self.fading["starting_brightness"] + steps * -1
                if new_rule < self.fading["target"]:
                    new_rule = self.fading["target"]

            self.scheduled_rule = int(new_rule)

            # Don't override user-set brightness
            if (self.fading["down"] and int(new_rule) < self.current_rule) or (not self.fading["down"] and int(new_rule) > self.current_rule):
                # Set new rule without calling set_rule method (would abort fade)
                self.current_rule = int(new_rule)
                if self.state is True:
                    self.send(1)

        # Start timer for next step (unless fade already complete)
        if not self.fade_complete():
            # Sleep until next step
            next_step = int(self.fading["period"] - ((SoftwareTimer.timer.epoch_now() - self.fading["started"]) % self.fading["period"]))
            SoftwareTimer.timer.create(next_step, self.fade, self.name + "_fade")
