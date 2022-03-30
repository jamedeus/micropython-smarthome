import logging
import urequests
import uasyncio as asyncio
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("Desktop_sensor")



class Desktop_trigger(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets, ip):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        self.ip = ip

        # Current monitor state
        self.current = None

        # Run monitor loop
        asyncio.create_task(self.monitor())



    def set_rule(self, rule):
        if rule == "Enabled" or rule =="Disabled":
            self.current_rule = rule
            log.info(f"Rule changed to {self.current_rule}")
            return True
        else:
            log.error(f"Failed to change rule to {rule}")
            return False



    def get_idle_time(self):
        # TODO find cause of ValueError ("syntax error in JSON")
        return urequests.get('http://' + str(self.ip) + ':5000/idle_time').json()



    def get_monitor_state(self):
        # TODO find cause of ValueError ("syntax error in JSON")
        try:
            return urequests.get('http://' + str(self.ip) + ':5000/state').json()["state"]
        except OSError:
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

                # If monitors just turned off, turn off lights (overrides main loop)
                if self.current == "Off":
                    for device in self.targets:
                        if not device.state == False:
                            success = device.send(0)

                            if success:
                                # Override motion sensors so they don't turn lights back on
                                for i in device.triggered_by:
                                    if i.sensor_type == "pir":
                                        i.motion = False
                                device.state = False

            # Poll every second
            await asyncio.sleep(1)
