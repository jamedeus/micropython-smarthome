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
        if self.current == "off":
            # Necessary and sufficient condition to turn lights off
            return "Override"
        else:
            # Necessary but insufficient condition to turn lights off - will stay on until unless all other sensors also return False
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

                print(f"Monitors changed from {self.current} to {new}")
                self.current = new

                # ISSUE: Cannot run prime sync from here...
                # Maybe better to put this on desktop end + add API command for desktop to turn off lights?
                # Or just run it on both ends?

                if self.current == "Off":
                    for device in self.targets:
                        if not device.state == False:
                            success = device.send(0)

                            if success:
                                device.state = False

            # Poll every second
            await asyncio.sleep(1)


