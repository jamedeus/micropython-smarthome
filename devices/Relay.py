import uasyncio as asyncio
import socket
import logging
import time



# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("Relay")



# Used for ESP8266 Relays + Desktops (running desktop-integration.py)
class Relay():
    def __init__(self, name, ip, device, current_rule):
        self.name = name
        self.ip = ip
        self.device = device
        self.current_rule = current_rule # The rule actually being followed
        self.scheduled_rule = current_rule # The rule scheduled for current time - may be overriden, stored here so can revert
        self.enabled = True
        self.integration_running = False

        log.info("Created Relay class instance named " + str(self.name) + ": ip = " + str(self.ip))



    def enable(self):
        self.enabled = True
        global config
        for i in config.sensors:
            if i.device == "pir" and i.scheduled_rule == "None":
                i.current_rule = i.scheduled_rule  # Revert to scheduled rule once desktop is enabled again
        log.info(f"{self.name} enabled")



    def disable(self):
        self.enabled = False
        global config
        for i in config.sensors:
            if i.device == "pir" and i.current_rule == "None": # If sensor currently has no reset timer (ie relying on desktop to turn off lights when screen goes off)
                i.current_rule = "15" # Set reset time to 15 minutes so lights don't get stuck on
        log.info(f"{self.name} disabled")



    def send(self, state=1):
        log.info("Relay.send method called, IP = " + str(self.ip) + ", state = " + str(state))

        if not self.enabled:
            log.info("Device is currently disabled, skipping")
            return True # Tell sensor that send succeeded so it doesn't retry forever

        if self.current_rule == "off" and state == 1:
            pass
        else:
            try:
                s = socket.socket()
                s.settimeout(10)
                print(f"Running send_relay, ip={self.ip}")
                s.connect((self.ip, 4200))
                if state:
                    print("Turned desktop ON")
                    s.send("on".encode())
                else:
                    print("Turned desktop OFF")
                    s.send("off".encode())
                s.close()
                log.info("Relay.send finished")

                return True # Tell calling function that request succeeded
            except OSError:
                # Desktop is either off or at login screen - disable device until it comes back online
                self.disable()
            except:
                return False # Tell calling function that request failed, will retry until it succeeds
            # TODO - receive response (msg OK/Invalid), log errors



    async def desktop_integration(self, config):
        # TODO find better way to pass config object to desktop_integration_client
        self.config = config
        print('\nDesktop integration running.\n')
        log.info("Desktop integration running")
        self.server = await asyncio.start_server(self.desktop_integration_client, host='0.0.0.0', port=4200, backlog=5)

        # TODO add handshake here, try to connect to self.ip until successful. Desktop gets node IP from handshake, remove hardcoded IP in desktop-integration.py

        while True:
            await asyncio.sleep(100)



    async def desktop_integration_client(self, sreader, swriter):
        try:
            while True:
                try:
                    res = await asyncio.wait_for(sreader.readline(), timeout=10)
                except asyncio.TimeoutError:
                    res = b''
                if res == b'':
                    raise OSError

                data = res.decode()

                if data == "on": # Unsure if this will be used - currently desktop only turns lights off (when monitors sleep)
                    print("Desktop turned lights ON")
                    log.info("Desktop turned lights ON")
                    # Set sensor instance attributes so it knows that desktop changed state
                    for sensor in self.config.sensors:
                        if self.config.sensors[sensor]["type"] == "pir":
                            sensor.state = True
                            sensor.motion = True
                elif data == "off": # Allow main loop to continue when desktop turns lights off
                    print("Desktop turned lights OFF")
                    log.info("Desktop turned lights OFF")
                    # Set sensor instance attributes so it knows that desktop changed state
                    for sensor in self.config.sensors:
                        if self.config.sensors[sensor]["type"] == "pir":
                            sensor.state = False
                            sensor.motion = False
                elif data == "enable":
                    print("Desktop re-enabled (user logged in)")
                    self.enable()

                elif data == "disable":
                    print("Desktop disabled (at login screen)")
                    self.disable()

                # Prevent running out of mem after repeated requests
                gc.collect()

        except OSError:
            pass
        await sreader.wait_closed()
