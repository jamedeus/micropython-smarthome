# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
from machine import Pin, Timer, RTC, PWM
import urequests
import socket
from struct import pack
import json
import os
from random import randrange
import uasyncio as asyncio

print("--------Booted--------")

# Hardware timer used to keep lights on for 5 min
timer = Timer(0)
# Timer re-runs startup every day at 3:00 am (reload schedule rules, sunrise/sunset times, etc)
config_timer = Timer(1)
# Used to reboot if startup hangs for longer than 1 minute
reboot_timer = Timer(2)
# Used when it is time to switch to the next schedule rule
next_rule_timer = Timer(3)

# Timer sets this to True at 3:00 am, causes main loop to reload config
reload_config = False

# Turn onboard LED on, indicates setup in progress
led = Pin(2, Pin.OUT, value=1)



class Config():
    def __init__(self, conf):
        print("\nInstantiating config object...\n")
        log("Instantiating config object...")

        # Load wifi credentials tuple
        self.credentials = (conf["wifi"]["ssid"], conf["wifi"]["password"])

        # Load metadata parameters - (unused so far)
        self.identifier = conf["metadata"]["id"]
        self.location = conf["metadata"]["location"]
        self.floor = conf["metadata"]["floor"]

        # Call function to connect to wifi + hit APIs
        self.api_calls()

        # Remember if a task has been created running desktop_integration
        self.desktop = False

        # Create empty dictionairy, will contain sub-dict for each device
        self.devices = {}

        # Iterate json
        for device in conf:
            if not device.startswith("device"): continue

            # Instantiate each device as appropriate class
            if conf[device]["type"] == "dimmer" or conf[device]["type"] == "bulb":
                instance = Tplink( device, conf[device]["ip"], conf[device]["type"], None )
            elif conf[device]["type"] == "relay" or conf[device]["type"] == "desktop":
                instance = Relay( device, conf[device]["ip"], conf[device]["type"], None )
            elif conf[device]["type"] == "pwm":
                instance = LedStrip( device, conf[device]["type"], conf[device]["pin"], None )

            # Add to config.devices dict with class object as key + json sub-dict as value
            self.devices[instance] = conf[device]
            # Overwrite schedule section with unix timestamp rules
            self.devices[instance]["schedule"] = self.convert_rules(conf[device]["schedule"])

        # Create empty dictionairy, will contain sub-dict for each sensor
        self.sensors = {}

        for sensor in conf:
            if not sensor.startswith("sensor"): continue

            # Get class instances of each of the sensor's targets
            targets = []
            for target in conf[sensor]["targets"]:
                for device in self.devices:
                    if device.name == target:
                        targets.append(device)

            # Instantiate sensor as appropriate class
            if conf[sensor]["type"] == "pir":
                instance = MotionSensor(sensor, conf[sensor]["pin"], conf[sensor]["type"], targets, None)

            # Add to config.sensors dict with class object as key + json sub-dict as value
            self.sensors[instance] = conf[sensor]
            # Overwrite schedule section with unix timestamp rules
            self.sensors[instance]["schedule"] = self.convert_rules(conf[sensor]["schedule"])

        self.rule_parser()

        # Get epoch time of next 3:00 am (re-run timestamp to epoch conversion)
        epoch = time.mktime(time.localtime())
        now = time.localtime(epoch)
        if now[3] < 3:
            next_reset = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
        else:
            next_reset = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, now[6], now[7])) # In testing, only needed to increment day - other parameters roll over correctly

        # Set timer to reload schedule rules at a random time between 3-4 am (prevent multiple units hitting API at same second)
        next_reset = (next_reset - epoch + randrange(3600)) * 1000
        config_timer.init(period=next_reset, mode=Timer.ONE_SHOT, callback=reload_schedule_rules)

        log("Finished instantiating config")



    def get_status(self):
        status_dict = {}
        status_dict["metadata"] = {}
        status_dict["metadata"]["id"] = self.identifier
        status_dict["metadata"]["floor"] = self.floor
        status_dict["metadata"]["location"] = self.location

        status_dict["devices"] = {}
        for i in self.devices:
            status_dict["devices"][i.name] = {}
            status_dict["devices"][i.name]["type"] = i.device
            status_dict["devices"][i.name]["current_rule"] = i.current_rule

        status_dict["sensors"] = {}
        for i in self.sensors:
            status_dict["sensors"][i.name] = {}
            status_dict["sensors"][i.name]["type"] = i.device
            status_dict["sensors"][i.name]["current_rule"] = i.current_rule
            status_dict["sensors"][i.name]["targets"] = []
            for t in i.targets:
                status_dict["sensors"][i.name]["targets"].append(t.name)
                for q in status_dict["devices"]:
                    if q == t.name:
                        status_dict["devices"][q]["turned_on"] = i.state
            status_dict["sensors"][i.name]["enabled"] = i.active

        return status_dict



    def api_calls(self):
        # Auto-reboot if startup doesn't complete in 1 min (prevents API calls hanging, canceled at bottom of function)
        reboot_timer.init(period=60000, mode=Timer.ONE_SHOT, callback=reboot)

        # Turn onboard LED on, indicates setup in progress
        led = Pin(2, Pin.OUT, value=1)

        # Connect to wifi
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected(): wlan.connect(self.credentials[0], self.credentials[1])

        # Wait until finished connecting before proceeding
        while not wlan.isconnected():
            continue
        else:
            print(f"Successfully connected to {self.credentials[0]}")

        failed_attempts = 0

        # Prevent no-mem error when API response received
        # TODO - Keep testing. This fixed all failures with try/except commented, but they happen again with try/except
        gc.collect()

        # Set current time from internet in correct timezone, retry until successful (note: ntptime is easier but doesn't support timezone)
        # TODO: Continue to optimize this - it seems to only fail when inside try/except (about 50% of the time), otherwise it always works...
        # Since RTC call will traceback if request fail, could just rely on reboot_timer to recover from failure
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/timezone?apiKey=ddcf9be5a455453e99d84de3dfe825bc&tz=America/Los_Angeles")
                now = time.localtime(int(response.json()["date_time_unix"]) - 946713600) # Convert unix epoch (from API) to micropython epoch (starts in 2000), then get time tuple
                RTC().datetime((now[0], now[1], now[2], now[6], now[3], now[4], now[5], 0)) # Set RTC - micropython is stupid and uses different parameter order for RTC
                response.close()
                break
            except:
                print("Failed setting system time, retrying...")
                log("Failed setting system time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5: reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass

        # Prevent no-mem error when API response received
        gc.collect()

        # Get sunrise/sunset time, retry until successful
        while True:
            try:
                response = urequests.get("https://api.ipgeolocation.io/astronomy?apiKey=ddcf9be5a455453e99d84de3dfe825bc&lat=45.524722&long=-122.6771891")
                # Parse out sunrise/sunset, convert to 24h format
                self.sunrise = response.json()["sunrise"]
                self.sunset = response.json()["sunset"]
                response.close()
                break # Break loop once request succeeds
            except:
                print("Failed getting sunrise/sunset time, retrying...")
                log("Failed getting sunrise/sunset time, retrying...")
                failed_attempts += 1
                if failed_attempts > 5: reboot()
                time.sleep_ms(1500) # If failed, wait 1.5 seconds before retrying
                gc.collect() # Free up memory before retrying
                pass # Allow loop to continue

        log("Finished API calls...")

        # Stop timer once API calls finish
        reboot_timer.deinit()

        # Turn off LED to confirm setup completed successfully
        led.value(0)



    # Receives a dictionairy of schedule rules with HH:MM timestamps
    # Returns a dictionairy of the same rules with unix epoch timestamps (next run only)
    # Called every day at 3:00 am since epoch times only work once
    def convert_rules(self, rules):
        # Create empty dict to store new schedule rules
        result = {}

        # Check for sunrise/sunet rules, replace "sunrise"/"sunset" with today's timestamps (converted to epoch time in loop below)
        if "sunrise" in rules:
            rules[self.sunrise] = rules["sunrise"]
            del rules["sunrise"]
        if "sunset" in rules:
            rules[self.sunset] = rules["sunset"]
            del rules["sunset"]

        # Get rule start times, sort chronologically
        schedule = list(rules)
        schedule.sort()

        # Get epoch time in current timezone
        epoch = time.mktime(time.localtime())
        # Get time tuple in current timezone
        now = time.localtime(epoch)

        for rule in schedule:
            # Returns epoch time of rule, uses all current parameters but substitutes hour + min from schedule and 0 for seconds
            trigger_time = time.mktime((now[0], now[1], now[2], int(rule.split(":")[0]), int(rule.split(":")[1]), 0, now[6], now[7]))

            # Add to results: Key = unix timestamp, value = value from original rules dict
            result[trigger_time] = rules[rule]
            # Also add a rule at the same time yesterday and tomorrow - temporary workaround for bug TODO - review this, see if there is a better approach
            result[trigger_time-86400] = rules[rule]
            result[trigger_time+86400] = rules[rule]

        # Return the finished dictionairy
        return result



    # Receive sub-dictionairy containing schedule rules, compare each against current time, return correct rule
    def rule_parser(self, arg="unused"):
        # Store timestamp of next rule, for callback timer
        next_rule = None

        items = {}

        for i in self.devices:
            items[i] = self.devices[i]["schedule"]

        for i in self.sensors:
            items[i] = self.sensors[i]["schedule"]

        # Iterate all devices in config
        for i in items:
            # Get list of rule trigger times, sort chronologically
            schedule = list(items[i])
            schedule.sort()

            # Get epoch time in current timezone
            epoch = time.mktime(time.localtime())

            for rule in range(0, len(schedule)):
                if rule is not len(schedule) - 1: # If current rule isn't the last rule, then end = next rule
                    end = schedule[rule+1]
                else: # If current rule IS last rule, then end = 3am (when rules are refreshed)
                    now = time.localtime(epoch)
                    if now[3] < 3:
                        end = time.mktime((now[0], now[1], now[2], 3, 0, 0, now[6], now[7]))
                    else:
                        weekday = now[6] + 1
                        if weekday == 7: weekday = 0
                        end = time.mktime((now[0], now[1], now[2]+1, 3, 0, 0, weekday, now[7]+1))

                # Check if actual epoch time is between current rule and next rule
                if schedule[rule] <= epoch < end:

                    if i.name.startswith("device"):
                        i.current_rule = self.devices[i]["schedule"][schedule[rule]]
                    elif i.name.startswith("sensor"):
                        i.current_rule = self.sensors[i]["schedule"][schedule[rule]]

                    # Find the next rule (out of all devices)
                    # On first iteration, set next rule for current device
                    if next_rule == None:
                        next_rule = end
                    # After first, overwrite current next_rule if the next rule for current device is sooner
                    else:
                        if end < next_rule:
                            next_rule = end

                    # Stop inner loop once match found, move to next device in main loop
                    break

                #else:
                    # TODO - Test whether this functionality is worth restoring (was advantageous when this funct ran every time ligths turned on, not sure if it is now)
                    # If rule has already expired, add 24 hours (move to tomorrow same time) and delete original
                    # This fixes rules between midnight - 3am (all rules are set for current day, so these are already in the past)
                    # Originally tried this in convert_rules(), but that causes *all* rules to be in future, so no match is found here
                    #config[device]["schedule"][schedule[rule] + 86400] = config[device]["schedule"][schedule[rule]]
                    #del config[device]["schedule"][schedule[rule]]

            else:
                log("rule_parser: No match found for " + str(device))
                print("no match found")
                print()

        # Set a callback timer for the next rule
        miliseconds = (next_rule - epoch) * 1000
        next_rule_timer.init(period=miliseconds, mode=Timer.ONE_SHOT, callback=self.rule_parser)
        print(f"rule_parser callback timer set for {next_rule}")

        # If lights are currently on, set bool to False (forces main loop to turn lights on, new brightness takes effect)
        for i in self.sensors:
            if "MotionSensor" in str(type(i)) and i.state == True:
                i.state = False



class LedStrip():
    def __init__(self, name, device, pin, current_rule):
        self.name = name
        self.device = device

        self.pwm = PWM(Pin(pin), duty=0)

        self.bright = 0 # Store current brightness, allows smooth transition when rule changes

        self.current_rule = current_rule
        log("Created LedStrip class instance named " + str(self.name) + ": pin = " + str(pin))



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




class MotionSensor():
    def __init__(self, name, pin, device, targets, current_rule):
        # Pin setup
        self.sensor = Pin(pin, Pin.IN, Pin.PULL_DOWN)

        self.name = name
        self.device = device
        self.current_rule = current_rule

        # For each target: find device instance with matching name, add to list
        self.targets = targets

        # Changed by hware interrupt
        self.motion = False

        # Remember target state, don't turn on/off if already on/off
        self.state = None

        # Remember if loop is running (prevents multiple asyncio tasks running same loop)
        self.loop_started = False



    def enable(self):
        self.sensor.irq(trigger=Pin.IRQ_RISING, handler=self.motion_detected)
        # Allows remote clients to query whether interrupt is active or not
        self.active = True
        if not self.loop_started == True:
            self.loop_started = True
            asyncio.create_task(self.loop())



    def disable(self):
        self.sensor.irq(handler=None)
        timer.deinit()
        # Allows remote clients to query whether interrupt is active or not
        self.active = False
        self.loop_started = False # Loop checks this variable, kills asyncio task if False



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
        log("resetTimer interrupt called")
        # Reset motion, causes self.loop to fade lights off
        self.motion = False



    async def loop(self):
        while True:

            if self.motion:

                if self.state is not True: # Only turn on if currently off
                    log("Motion detected")
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
                    log("Main loop: Turning lights off...")

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



class RemoteControl:
    def __init__(self, host='0.0.0.0', port=6969, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    async def run(self):
        print('\nRemote control: Awaiting client connection.\n')
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)

    async def run_client(self, sreader, swriter):
        global config
        try:
            while True:
                try:
                    res = await asyncio.wait_for(sreader.readline(), self.timeout)
                except asyncio.TimeoutError:
                    res = b''
                if res == b'':
                    raise OSError

                data = json.loads(res.rstrip())

                if data[0] == "status":
                    # TODO: Figure out a way to receive on client side (socket.recv() doesn't work)
                    print("received status request - not yet implemented, ignored")
                elif data[0] == "reboot":
                    print(f"\nAPI: Reboot command received from {sreader.get_extra_info('peername')[0]}\n")
                    reboot()
                elif data[0] == "disable" and data[1].startswith("sensor"):
                    for i in config.sensors:
                        if i.name == data[1]:
                            print(f"Received command to disable {data[1]}, disabling...")
                            i.disable()
                elif data[0] == "enable" and data[1].startswith("sensor"):
                    for i in config.sensors:
                        if i.name == data[1]:
                            print(f"Received command to enable {data[1]}, enabling...")
                            i.enable()
                elif data[0] == "set_rule" and data[1].startswith("sensor") or data[1].startswith("device"):
                    target = data[1]

                    if target.startswith("sensor"):
                        for i in config.sensors:
                            if i.name == target:
                                print(f"Received command to set {target} delay to {data[2]} minutes, setting...")
                                i.current_rule = data[2]

                    elif target.startswith("device"):
                        for i in config.devices:
                            if i.name == target:
                                print(f"Received command to set {target} brightness to {data[2]}, setting...")
                                i.current_rule = int(data[2])

                    # Prevent running out of mem after repeated requests
                    gc.collect()

        except OSError:
            pass
        await sreader.wait_closed()



class DesktopIntegration:
    def __init__(self, host='0.0.0.0', port=4200, backlog=5, timeout=10):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    async def run(self):
        print('\nDesktop integration running.\n')
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)

    async def run_client(self, sreader, swriter):
        global config
        try:
            while True:
                try:
                    res = await asyncio.wait_for(sreader.readline(), self.timeout)
                except asyncio.TimeoutError:
                    res = b''
                if res == b'':
                    raise OSError

                data = json.loads(res.rstrip())

                if data[0] == "on": # Unsure if this will be used - currently desktop only turns lights off (when monitors sleep)
                    print("Desktop turned lights ON")
                    log("Desktop turned lights ON")
                    # Set sensor instance attributes so it knows that desktop changed state
                    for sensor in config.sensors:
                        if config.sensors[sensor]["type"] == "pir":
                            sensor.state = True
                            sensor.motion = True
                elif data[0] == "off": # Allow main loop to continue when desktop turns lights off
                    print("Desktop turned lights OFF")
                    log("Desktop turned lights OFF")
                    # Set sensor instance attributes so it knows that desktop changed state
                    for sensor in config.sensors:
                        if config.sensors[sensor]["type"] == "pir":
                            sensor.state = False
                            sensor.motion = False

                # Prevent running out of mem after repeated requests
                gc.collect()

        except OSError:
            pass
        await sreader.wait_closed()



# Takes string as argument, writes to log file with YYYY/MM/DD HH:MM:SS timestamp
def log(message):
    now = time.localtime()
    line = str(now[0]) + "/"
    for i in range(1,3):
        if len(str(now[i])) == 1:
            line = line + "0" + str(now[i]) + "/"
        else:
            line = line + str(now[i]) + "/"
    else:
        line = line[0:-1] + " " # Replace trailing "/" with " "
    for i in range(3,6):
        if len(str(now[i])) == 1:
            line = line + "0" + str(now[i]) + ":"
        else:
            line = line + str(now[i]) + ":"
    else:
        line = line + " " + message + "\n"

    with open('log.txt', 'a') as file:
        file.write(line)



# Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
def reload_schedule_rules(timer):
    print("3:00 am callback, reloading schedule rules...")
    log("3:00 am callback, reloading schedule rules...")
    # Temporary fix: Unable to reload after 2-3 days due to mem fragmentation (no continuous free block long enough for API response)
    # Since this will take a lot of testing to figure out, just reboot until then. TODO - fix memory issue
    reboot()



def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



async def disk_monitor():
    print("Disk Monitor Started\n")

    # Get filesize/modification time (to detect upload in future)
    old_code = os.stat("boot.py")
    old_config = os.stat("config.json")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old_code:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            log("Received new code from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reboot()
        elif not os.stat("config.json") == old_config:
            print("\nReceived new config from webrepl, rebooting...\n")
            log("Received new config from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reboot()
        # Don't let the log exceed 500 KB, full disk hangs system + can't pull log via webrepl
        elif os.stat('log.txt')[6] > 500000:
            print("\nLog exceeded 500 KB, clearing...\n")
            os.remove('log.txt')
            log("Deleted old log (exceeded 500 KB size limit)")
        else:
            await asyncio.sleep(1) # Only check once per second



async def main():
    # Check if desktop device configured, start desktop_integration (unless already running)
    for i in config.devices:
        if i.device == "desktop" and not config.desktop:
            log("Desktop integration is being used, creating asyncio task to listen for messages")
            desktop = DesktopIntegration()
            asyncio.create_task(desktop.run())
            config.desktop = True

    # Create hardware interrupts + create async task for sensor loops
    for sensor in config.sensors:
        if not sensor.loop_started:
            sensor.enable()

    # Start listening for remote commands
    server = RemoteControl()
    asyncio.create_task(server.run())

    # Listen for new code upload (auto-reboot when updated), prevent log from filling disk
    asyncio.create_task(disk_monitor())

    # Keep running, all tasks stop if function exits
    while True:
        await asyncio.sleep(1)



# Check if log file exists, create if not
try:
    os.stat('log.txt')
except OSError: # File does not exist
    log("Created log file")

# Instantiate config object - init method replaces old startup function (convert rules, connect to wifi, API calls, etc)
config = Config(json.load(open('config.json', 'r')))
# TODO - close file, see if it fixes mem fragmentation

webrepl.start()

asyncio.run(main())
