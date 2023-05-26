import logging
from Device import Device
import uasyncio as asyncio
import json

# Set name for module's log lines
log = logging.getLogger("ApiTarget")


class ApiTarget(Device):
    def __init__(self, name, nickname, _type, default_rule, ip):
        super().__init__(name, nickname, _type, True, None, default_rule)

        # IP that API command is sent to
        self.ip = ip

    # Takes dict containing 2 entries named "on" and "off"
    # Both entries are lists containing a full API request
    # "on" sent when self.send(1) called, "off" when self.send(0) called
    def validator(self, rule):
        if isinstance(rule, str):
            try:
                # Convert string rule to dict (if received from API)
                rule = json.loads(rule)
            except (TypeError, ValueError):
                return False

        if not isinstance(rule, dict):
            return False

        # Reject if more than 2 sub-rules
        if not len(rule) == 2:
            return False

        for i in rule:
            # Index must be "on" or "off"
            if not i == "on" and not i == "off":
                return False

            if not isinstance(rule[i], list):
                return False

            # "ignore" is not a valid command, it allows only using on/off and ignoring the other
            if rule[i][0] in ['reboot', 'clear_log', 'ignore'] and len(rule[i]) == 1:
                continue

            elif rule[i][0] in ['enable', 'disable', 'reset_rule'] and len(rule[i]) == 2 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
                continue

            elif rule[i][0] in ['condition_met', 'trigger_sensor'] and len(rule[i]) == 2 and rule[i][1].startswith("sensor"):
                continue

            elif rule[i][0] in ['turn_on', 'turn_off'] and len(rule[i]) == 2 and rule[i][1].startswith("device"):
                continue

            elif rule[i][0] in ['enable_in', 'disable_in'] and len(rule[i]) == 3 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
                try:
                    float(rule[i][2])
                    continue
                except ValueError:
                    return False

            elif rule[i][0] == 'set_rule' and len(rule[i]) == 3 and (rule[i][1].startswith("device") or rule[i][1].startswith("sensor")):
                continue

            elif rule[i][0] == 'ir_key':
                if len(rule[i]) == 3 and type(rule[i][1]) == str and type(rule[i][2]) == str:
                    continue
                else:
                    return False

            else:
                # Did not match any valid patterns
                return False

        else:
            # Iteration finished without a return False, rule is valid
            return rule

    def set_rule(self, rule):
        # Check if rule is valid - may return a modified rule (ie cast str to int)
        valid_rule = self.rule_validator(rule)

        # Turn off target before changing rule to disabled (cannot call send after changing, requires dict)
        if valid_rule == "disabled":
            self.send(0)

        if not str(valid_rule) == "False":
            self.current_rule = valid_rule
            log.info(f"{self.name}: Rule changed to {self.current_rule}")
            print(f"{self.name}: Rule changed to {self.current_rule}")

            # Rule just changed to disabled
            if self.current_rule == "disabled":
                self.disable()
            # Rule just changed to enabled, replace with usable rule (default) and enable
            elif self.current_rule == "enabled":
                self.current_rule = self.default_rule
                self.enable()
            # Sensor was previously disabled, enable now that rule has changed
            elif self.enabled is False:
                self.enable()
            # Device is currently on, run send so new rule can take effect
            elif self.state is True:
                self.send(1)

            return True

        else:
            log.error(f"{self.name}: Failed to change rule to {rule}")
            print(f"{self.name}: Failed to change rule to {rule}")
            return False

    async def request(self, msg):
        reader, writer = await asyncio.open_connection(self.ip, 8123)
        try:
            writer.write('{}\n'.format(json.dumps(msg)).encode())
            await writer.drain()
            # TODO change this limit?
            await reader.read(1000)
        except OSError:
            pass
        writer.close()
        await writer.wait_closed()

    def send(self, state=1):
        # Refuse to turn disabled device on, but allow turning off
        if not self.enabled and state:
            # Return True causes group to flip state to True, even though device is off
            # This allows turning off (would be skipped if state already == False)
            return True

        # "On" rule
        if state:
            if self.current_rule["on"][0] == "ignore":
                # If rule is ignore, do nothing
                return True

            asyncio.create_task(self.request(self.current_rule["on"]))

            # Reset motion sensor to allow retriggering the remote motion sensor (restarts reset timer)
            # Retrigger when motion = True only restarts sensor's own resetTimer, but does not send another API command
            for sensor in self.triggered_by:
                if sensor._type == "pir":
                    sensor.motion = False

        # "Off" rule
        else:
            if self.current_rule["off"][0] == "ignore":
                # If rule is ignore, do nothing
                return True

            asyncio.create_task(self.request(self.current_rule["off"]))

        # Tells main loop send succeeded
        return True
