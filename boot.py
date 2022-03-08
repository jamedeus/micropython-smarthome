# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

import webrepl
import network
import time
from machine import Pin, Timer, RTC
import urequests
import json
import os
from random import randrange
import uasyncio as asyncio
import logging
import Config

print("--------Booted--------")

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Main")
log.info("Booted")

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



class RemoteControl:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    async def run(self):
        print('\nRemote control: Awaiting client connection.\n')
        log.info("API ready")
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)

    async def run_client(self, sreader, swriter):
        try:
            while True:
                try:
                    res = await asyncio.wait_for(sreader.readline(), self.timeout)
                except asyncio.TimeoutError:
                    raise OSError

                # Receives null when client closes write stream - break and close read stream
                if not res: break

                data = json.loads(res.rstrip())

                # Will be overwritten if command is valid, checked after conditional before sending invalid syntax error
                reply = False

                if data[0] == "status":
                    print(f"\nAPI: Status request received from {sreader.get_extra_info('peername')[0]}, sending dict\n")
                    reply = Config.config.get_status()
                    type(reply)

                elif data[0] == "reboot":
                    print(f"API: Reboot command received from {sreader.get_extra_info('peername')[0]}")

                    # Send response before rebooting (cannot rely on the send call after conditional)
                    reply = 'OK'
                    swriter.write(json.dumps(reply))
                    await swriter.drain()  # Echo back
                    reboot()



                elif data[0] == "disable" and data[1].startswith("sensor"):
                    for i in Config.config.sensors:
                        if i.name == data[1]:
                            print(f"API: Received command to disable {data[1]}, disabling...")
                            i.disable()
                            reply = 'OK'

                    if not reply: # Detect if loop failed to find a match
                        reply = 'Error: Sensor not found'



                elif data[0] == "enable" and data[1].startswith("sensor"):
                    for i in Config.config.sensors:
                        if i.name == data[1]:
                            print(f"API: Received command to enable {data[1]}, enabling...")
                            i.enable()
                            reply = 'OK'

                    if not reply: # Detect if loop failed to find a match
                        reply = 'Error: Sensor not found'



                elif data[0] == "set_rule" and data[1].startswith("sensor") or data[1].startswith("device"):
                    target = data[1]

                    if target.startswith("sensor"):
                        for i in Config.config.sensors:
                            if i.name == target:
                                print(f"API: Received command to set {target} delay to {data[2]} minutes, setting...")
                                try:
                                    i.current_rule = data[2]
                                    reply = 'OK'
                                except:
                                    reply = 'Error: Bad rule parameter, int required'

                    elif target.startswith("device"):
                        for i in Config.config.devices:
                            if i.name == target:
                                print(f"API: Received command to set {target} brightness to {data[2]}, setting...")
                                try:
                                    i.current_rule = data[2]
                                    reply = 'OK'
                                except:
                                    reply = 'Error: Bad rule parameter. Relay requires "on" or "off", all others require int'

                    else:
                        print(f"API: Received invalid command from {sreader.get_extra_info('peername')[0]}")
                        reply = 'Error: 2nd param must be name of a sensor or device - use status to see options'



                elif data[0] == "ir" and (data[1] == "tv" or data[1] == "ac"):
                    for i in Config.config.devices:
                        if i.device == "ir_blaster":
                            if not data[1] in i.codes:
                                reply = 'Error: No codes found for target "{}"'.format(data[1])
                            else:
                                if not data[2]:
                                    reply = 'Error: Please specify which key to simulate'
                                else:
                                    i.send(data[1], data[2])
                                    reply = 'OK'

                    if not reply:
                        reply = 'Error: No IR blaster configured'



                elif data[0] == "ir" and data[1] == "backlight":
                    if not (data[2] == "on" or data[2] == "off"):
                        reply = 'Error: Backlight setting must be "on" or "off"'
                    else:
                        for i in Config.config.devices:
                            if i.device == "ir_blaster":
                                i.backlight(data[2])
                                reply = 'OK'

                        if not reply:
                            reply = 'Error: No IR blaster configured'



                else:
                    print(f"API: Received invalid command from {sreader.get_extra_info('peername')[0]}")
                    reply = 'Error: first arg must be one of: status, reboot, enable, disable, set_rule'

                # Send the reply
                swriter.write(json.dumps(reply))
                await swriter.drain()
                reply = False

                # Prevent running out of mem after repeated requests
                gc.collect()

        except OSError:
            pass
        # Client disconnected, close socket
        await sreader.wait_closed()



# Called by timer every day at 3 am, regenerate timestamps for next day (epoch time)
def reload_schedule_rules(timer):
    print("3:00 am callback, reloading schedule rules...")
    log.info("3:00 am callback, reloading schedule rules...")
    # Temporary fix: Unable to reload after 2-3 days due to mem fragmentation (no continuous free block long enough for API response)
    # Since this will take a lot of testing to figure out, just reboot until then. TODO - fix memory issue
    reboot()



def reboot(arg="unused"):
    print("Reboot function called, rebooting...")
    log.info("Reboot function called, rebooting...\n")
    import machine
    machine.reset()



async def disk_monitor():
    print("Disk Monitor Started\n")

    # Get filesize/modification time (to detect upload in future)
    old = os.stat("boot.py")

    while True:
        # Check if file changed on disk
        if not os.stat("boot.py") == old:
            # If file changed (new code received from webrepl), reboot
            print("\nReceived new code from webrepl, rebooting...\n")
            log.info("Received new code from webrepl, rebooting...")
            time.sleep(1) # Prevents webrepl_cli.py from hanging after upload (esp reboots too fast)
            reboot()
        # Don't let the log exceed 500 KB, full disk hangs system + can't pull log via webrepl
        elif os.stat('app.log')[6] > 500000:
            print("\nLog exceeded 500 KB, clearing...\n")
            os.remove('log.txt')
            log.info("Deleted old log (exceeded 500 KB size limit)")
        else:
            await asyncio.sleep(1) # Only check once per second



async def main():
    # Check if desktop device configured, start desktop_integration (unless already running)
    for i in Config.config.devices:
        if i.device == "desktop" and not i.integration_running:
            log.info("Desktop integration is being used, creating asyncio task to listen for messages")
            asyncio.create_task(i.desktop_integration())
            i.integration_running = True

    # Create hardware interrupts + create async task for sensor loops
    for sensor in Config.config.sensors:
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



gc.collect()

webrepl.start()

asyncio.run(main())
