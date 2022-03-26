from machine import Pin
import uasyncio as asyncio
import logging
import time
from Sensor import Sensor
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("MotionSensor")



class MotionSensor(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets, pins, scheduler_name):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Pin setup
        self.sensor = []
        for pin in pins:
            self.sensor.append(Pin(pin, Pin.IN, Pin.PULL_DOWN))

        # Name used when creating software timers - allows 2 sensors using same name to share a reset timer
        self.scheduler_name = scheduler_name

        # Changed by hware interrupt
        self.condition_met = False

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        log.info(f"Instantiated MotionSensor named {self.name} on pin {pin}")



    def enable(self):
        super().enable()

        self.condition_met = False

        # Create hardware interrupts for all sensors in group
        for i in self.sensor:
            i.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)



    def disable(self):
        super().disable()

        # Disable hardware interrupts for all sensors in group
        for i in self.sensor:
            i.irq(handler=None)

        # Stop any reset timer that may be running
        SoftwareTimer.timer.cancel(self.scheduler_name)



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

        # Workaround to allow enabling/disabling in config, permanent solution requires major rewrite
        if self.current_rule == "Disabled":
            self.disable()
            return True

        if self.current_rule == "Enabled":
            self.enable()
            # Immediately replace with sane default so resetTimer can be set
            self.current_rule = 15
            return True

        # If reset timer currently running, replace so new rule takes effect
        if self.condition_met:
            try:
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.resetTimer, self.name)
            except TypeError:
                pass # Prevent crash when rule changed to "None" (no timeout)
            except ValueError:
                pass # Prevent crash when rule changes to "Enabled" or "Disabled"




    # Interrupt routine, called when motion sensor triggered
    def motion_detected(self, pin):
        self.condition_met = True

        # Set reset timer
        if not ("None" in str(self.current_rule) or "Enabled" in str(self.current_rule) or "Disabled" in str(self.current_rule)):
            try:
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.resetTimer, self.scheduler_name)
            except:
                print(f"CAUGHT: name = {self.name}, rule = {self.current_rule}")

        else:
            # Stop any reset timer that may be running from before delay = None
            SoftwareTimer.timer.cancel(self.scheduler_name)



    def resetTimer(self, timer="optional"):
        log.info("resetTimer interrupt called")
        # Reset motion, causes self.loop to fade lights off
        self.condition_met = False
