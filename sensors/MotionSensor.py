from machine import Pin
import uasyncio as asyncio
import logging
import time
from Sensor import Sensor
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("MotionSensor")



class MotionSensor(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets, pins):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Pin setup
        self.sensor = []
        for pin in pins:
            self.sensor.append(Pin(pin, Pin.IN, Pin.PULL_DOWN))

        # Changed by hware interrupt
        self.motion = False

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        log.info(f"Instantiated MotionSensor named {self.name} on pin {pin}")



    def enable(self):
        super().enable()

        self.motion = False

        # Create hardware interrupts for all sensors in group
        for i in self.sensor:
            i.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)



    def disable(self):
        super().disable()

        # Disable hardware interrupts for all sensors in group
        for i in self.sensor:
            i.irq(handler=None)

        # Stop any reset timer that may be running
        SoftwareTimer.timer.cancel(self.name)



    def set_rule(self, rule):
        try:
            self.current_rule = float(rule)
            log.info(f"Rule changed to {self.current_rule}")
            return True
        except ValueError:
            log.error(f"Failed to change rule to {rule}")
            return False



    def next_rule(self):
        super().next_rule()

        # If reset timer currently running, replace so new rule takes effect
        if self.motion:
            try:
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.resetTimer, self.name)
            except TypeError:
                pass # Prevent crash when rule changed to "None" (no timeout)



    # Interrupt routine, called when motion sensor triggered
    def motion_detected(self, pin):
        self.motion = True

        # Set reset timer
        if not "None" in str(self.current_rule):

            off = float(self.current_rule) * 60000
            SoftwareTimer.timer.create(off, self.resetTimer, self.name)

        else:
            # Stop any reset timer that may be running from before delay = None
            SoftwareTimer.timer.cancel(self.name)



    def resetTimer(self, timer="optional"):
        log.info("resetTimer interrupt called")
        # Reset motion, causes self.loop to fade lights off
        self.motion = False



    async def loop(self):
        while True:

            if self.motion:

                if self.state is not True: # Only turn on if currently off
                    log.info(f"{self.name}: Motion detected")
                    print("motion detected")

                    # Record whether each send succeeded/failed
                    responses = []

                    # Call send method of each class instance, argument = turn ON
                    for device in self.targets:
                        # Only send if the target is enabled
                        if self.targets[device]:
                            responses.append(device.send(1)) # Send method returns either True or False

                    # If all succeded, set bool to prevent retrying
                    if not False in responses:
                        self.state = True

            else:
                if self.state is not False: # Only turn off if currently on
                    log.info(f"{self.name}: Turning lights off...")

                    # Record whether each send succeeded/failed
                    responses = []

                    # Call send method of each class instance, argument = turn OFF
                    for device in self.targets:
                        # Only send if the target is enabled
                        if self.targets[device]:
                            responses.append(device.send(0)) # Send method returns either True or False

                    # If all succeded, set bool to prevent retrying
                    if not False in responses:
                        self.state = False

            # If sensor was disabled
            if not self.loop_started:
                self.motion = False
                return True # Kill async task

            await asyncio.sleep_ms(20)
