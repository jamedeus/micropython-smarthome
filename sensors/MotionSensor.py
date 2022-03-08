from machine import Pin, Timer
import uasyncio as asyncio
import logging
import time

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("MotionSensor")



class MotionSensor():
    def __init__(self, name, pin, device, targets, current_rule):
        # Pin setup
        self.sensor = Pin(pin, Pin.IN, Pin.PULL_DOWN)

        self.name = name
        self.device = device
        self.current_rule = current_rule # The rule actually being followed
        self.scheduled_rule = current_rule # The rule scheduled for current time - may be overriden, stored here so can revert

        # For each target: find device instance with matching name, add to list
        self.targets = targets

        # Changed by hware interrupt
        self.motion = False

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        # Remember if loop is running (prevents multiple asyncio tasks running same loop)
        self.loop_started = False

        log.info(f"Instantiated motion sensor on pin {pin}")



    def enable(self):
        self.sensor.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)
        # Allows remote clients to query whether interrupt is active or not
        self.active = True
        if not self.loop_started == True:
            self.loop_started = True
            asyncio.create_task(self.loop())
        log.info(f"{self.name} enabled")



    def disable(self):
        self.sensor.irq(handler=None)
        timer.deinit()
        # Allows remote clients to query whether interrupt is active or not
        self.active = False
        self.loop_started = False # Loop checks this variable, kills asyncio task if False
        log.info(f"{self.name} disabled")



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
                        responses.append(device.send(0)) # Send method returns either True or False

                    # If all succeded, set bool to prevent retrying
                    if not False in responses:
                        self.state = False

            # If sensor was disabled
            if not self.loop_started:
                self.motion = False
                return True # Kill async task

            await asyncio.sleep_ms(20)
