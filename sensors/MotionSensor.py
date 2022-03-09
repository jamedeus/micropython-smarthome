from machine import Pin, Timer
import uasyncio as asyncio
import logging
import time
from Sensor import Sensor

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("MotionSensor")



class MotionSensor(Sensor):
    def __init__(self, name, sensor_type, enabled, current_rule, scheduled_rule, targets, pin):
        super().__init__(name, sensor_type, enabled, current_rule, scheduled_rule, targets)
        # Pin setup
        self.sensor = Pin(pin, Pin.IN, Pin.PULL_DOWN)

        # Changed by hware interrupt
        self.motion = False

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        # Remember if loop is running (prevents multiple asyncio tasks running same loop)
        self.loop_started = False

        log.info(f"Instantiated motion sensor on pin {pin}")



    def enable(self):
        super().enable()

        self.motion = False
        self.sensor.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)



    def disable(self):
        super().disable()

        self.sensor.irq(handler=None)
        timer.deinit()



    def set_rule(self, rule):
        try:
            self.current_rule = float(rule)
            return True
        except ValueError:
            return False



    # Interrupt routine, called when motion sensor triggered
    def motion_detected(self, pin):
        self.motion = True

        # Set reset timer
        # TODO - since can't reliably know how many sensors, move to software timers and self them
        if not "None" in str(self.current_rule):
            off = int(float(self.current_rule) * 60000) # Convert to ms
            # Start timer (restarts every time motion detected), calls function that resumes main loop when it times out
            timer.init(period=off, mode=Timer.ONE_SHOT, callback=self.resetTimer)
        else:
            # Stop any reset timer that may be running from before delay = None
            timer.deinit()



    def resetTimer(self, timer):
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
