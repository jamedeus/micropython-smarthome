from machine import Pin
import logging
from Sensor import Sensor
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("MotionSensor")



class MotionSensor(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets, pin):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)

        # Pin setup
        self.sensor = Pin(pin, Pin.IN, Pin.PULL_DOWN)

        # Create hardware interrupt
        self.enable()

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        log.info(f"Instantiated MotionSensor named {self.name} on pin {pin}")



    def enable(self):
        super().enable()

        self.motion = False

        # Create hardware interrupt
        self.sensor.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)



    def disable(self):
        super().disable()

        # Disable hardware interrupt
        self.sensor.irq(handler=None)

        # Stop any reset timer that may be running
        SoftwareTimer.timer.cancel(self.name)



    def condition_met(self):
        return self.motion



    def rule_validator(self, rule):
        try:
            if rule == "Disabled":
                return rule
            elif rule is None:
                return rule
            elif isinstance(rule, bool):
                return False
            else:
                return float(rule)
        except (ValueError, TypeError):
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
            except ValueError:
                pass # Prevent crash when rule changes to "Enabled" or "Disabled"




    # Interrupt routine, called when motion sensor triggered
    def motion_detected(self, pin=""):
        if not self.motion:
            print(f"{self.name}: Motion detected")
            log.debug(f"{self.name}: Motion detected")

        self.motion = True

        # Set reset timer
        if not ("None" in str(self.current_rule) or "Enabled" in str(self.current_rule) or "Disabled" in str(self.current_rule)):
            try:
                off = float(self.current_rule) * 60000
                SoftwareTimer.timer.create(off, self.resetTimer, self.name)
            except:
                print(f"CAUGHT: name = {self.name}, rule = {self.current_rule}")

        else:
            # Stop any reset timer that may be running from before delay = None
            SoftwareTimer.timer.cancel(self.name)



    def resetTimer(self, timer="optional"):
        log.info(f"{self.name}: resetTimer interrupt")
        # Reset motion, causes main loop to fade lights off
        self.motion = False
