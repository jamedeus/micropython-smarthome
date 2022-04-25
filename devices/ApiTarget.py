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
            #return "Request failed"
        try:
            response = json.loads(res)
        except ValueError:
            pass
            #return "Error: Unable to decode response"
        writer.close()
        await writer.wait_closed()



    def send(self, state=1):
        if not state == 1:
            # Cannot be turned off
            return True

        asyncio.create_task(self.request(self.current_rule))

        # Tell main loop send succeeded
        # Note that when used to trigger a motion sensor this will prevent re-triggering (to restart reset timer)
        # Workaround: Set an extremely short rule for motionSensor that triggers this (can still fail if constant motion detected)
        return True
