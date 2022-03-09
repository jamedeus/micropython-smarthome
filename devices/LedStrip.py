from machine import Pin, PWM
import logging
import time
from Device import Device



# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("LedStrip")



class LedStrip(Device):
    def __init__(self, name, device_type, enabled, current_rule, scheduled_rule, pin):
        super().__init__(name, device_type, enabled, current_rule, scheduled_rule)

        # TODO - Find optimal PWM freq. Default (5 KHz) causes very noticable coil whine in downstairs bathroom at 128 duty cycle.
        # Raising significantly reduces max brightness (exceeded MOSFET switching time), may just need different power supply?
        self.pwm = PWM(Pin(pin), duty=0)

        self.bright = 0 # Store current brightness, allows smooth transition when rule changes

        log.info("Created LedStrip class instance named " + str(self.name) + ": pin = " + str(pin))



    def send(self, state=1):
        if state:
            target = self.current_rule
        else:
            target = 0

        # Exit if current already matches target, prevent division by 0 below
        if self.bright == target: return True

        # Fade DOWN
        if self.bright > target:
            # Calculate correct delay for 1 second fade
            steps = self.bright - target
            delay = int(1000000 / steps)

            while self.bright > target:
                self.bright -= 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

        # Fade UP
        else:
            # Calculate correct delay for 1 second fade
            steps = target - self.bright
            delay = int(1000000 / steps)

            while self.bright < target:
                self.bright += 1
                self.pwm.duty(self.bright)
                time.sleep_us(delay)

        return True # Tell calling function that request succeeded
