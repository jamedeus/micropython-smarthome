import logging
from Device import Device
import SoftwareTimer
import uasyncio as asyncio
import json

# Set name for module's log lines
log = logging.getLogger("ApiTarget")



class ApiTarget(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, ip):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        # IP that API command is sent to
        self.ip = ip



    # TODO test enable/disable, see if methods need to be subclassed (they set device's state, could block loop from sending/send at incorrect time)


    # Takes list containing entire API request
    def rule_validator(self, rule):
        if not isinstance(rule, list):
            return False

        if rule[0] in ['reboot', 'clear_log'] and len(rule) == 1:
            return rule

        elif rule[0] in ['enable', 'disable', 'condition_met', 'trigger_sensor'] and (rule[1].startswith("device") or rule[1].startswith("sensor")) and len(rule) == 2:
            return rule

        elif rule[0] in ['enable_in', 'disable_in', 'set_rule'] and (rule[1].startswith("device") or rule[1].startswith("sensor")) and len(rule) == 3:
            return rule

        else:
            return False



    async def request(self, msg):
        reader, writer = await asyncio.open_connection(self.ip, 8123)
        try:
            writer.write('{}\n'.format(json.dumps(msg)).encode())
            await writer.drain()
            res = await reader.read(1000)
        except OSError:
            pass
        writer.close()
        await writer.wait_closed()



    def send(self, state=1):
        print("send method")
        if not state == 1:
            # Cannot be turned off
            # TODO add on_rule and off_rule (either can be null), will allow using this with switch sensor_type etc.
            return True

        asyncio.create_task(self.request(self.current_rule))

        # Reset motion sensor to allow retriggering the remote motion sensor (restarts reset timer)
        # Retrigger when motion = True only restarts sensor's own resetTimer, but does not send another API command
        for sensor in self.triggered_by:
            if sensor.sensor_type == "pir":
                sensor.motion = False

        return True
