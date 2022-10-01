import logging
import urequests
import uasyncio as asyncio
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Desktop_sensor")



class Desktop_trigger(Sensor):
    def __init__(self, name, nickname, sensor_type, enabled, current_rule, default_rule, targets, ip):
        super().__init__(name, nickname, sensor_type, enabled, current_rule, default_rule, targets)

        self.ip = ip

        # Current monitor state
        self.current = None

        # Find desktop target so monitor loop (below) can update target's state attribute when screen turn on/off
        for i in self.targets:
            if i.device_type == "desktop" and i.ip == self.ip:
                self.desktop_target = i
                break
        else:
            self.desktop_target = None

        # Run monitor loop
        asyncio.create_task(self.monitor())

        log.info(f"Instantiated Desktop named {self.name}: ip = {self.ip}")



    def rule_validator(self, rule):
        try:
            if rule.lower() == "enabled" or rule.lower() =="disabled":
                return rule.lower()
            else:
                return False
        except AttributeError:
            return False



    def get_idle_time(self):
        # TODO find cause of ValueError ("syntax error in JSON")
        return urequests.get('http://' + str(self.ip) + ':5000/idle_time').json()



    def get_monitor_state(self):
        # TODO find cause of ValueError ("syntax error in JSON")
        try:
            return urequests.get('http://' + str(self.ip) + ':5000/state').json()["state"]
        except (OSError, IndexError):
            # Wifi interruption, return False - caller will try again in 1 second
            return False



    def condition_met(self):
        if self.current == "On":
            return True
        else:
            return False



    # In some situations desktop returns values other than "On" and "Off" (at lock screen, standby, etc)
    # If main loop queried directly, would have to retry until valid reading returned, blocking
    # To prevent, loop just queries self.current attr. This loop monitors and only updates self.current when valid value received
    async def monitor(self):
        self.current = self.get_monitor_state()

        while True:
            new = self.get_monitor_state()

            if new != self.current:

                if new != "On" and new != "Off":
                    # At lock screen, or getting "Disabled" for a few seconds (NVIDIA Prime sync quirk)
                    # Keep old value for self.current, wait 1 second, try again
                    await asyncio.sleep(1)
                    continue

                print(f"{self.name}: Monitors changed from {self.current} to {new}")
                log.debug(f"{self.name}: Monitors changed from {self.current} to {new}")
                self.current = new

                # If monitors just turned off (indicates user NOT present), turn off lights
                if self.current == "Off":
                    # Override motion sensors, all sensors will now read False (unless dummy/switch present, cannot be overriden)
                    for sensor in self.group.triggers:
                        if sensor.sensor_type == "pir":
                            sensor.motion = False

                    # Update target's state. This enables loop to turn screen back on if needed (dummy/switch present)
                    if self.desktop_target:
                        self.desktop_target.state = False

                    # Force group to apply actions so above overrides can take effect
                    # If no dummy/switch is present (or if reading False), all devices will turn OFF
                    # If dummy/switch reading True is present, lights will stay ON and screen will turn back ON to match
                    self.group.reset_state()

                # If monitors just turned on, update target's state
                elif self.current == "On":
                    if self.desktop_target:
                        self.desktop_target.state = True

            # Poll every second
            await asyncio.sleep(1)
