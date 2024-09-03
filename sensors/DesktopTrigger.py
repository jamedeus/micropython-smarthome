import logging
import asyncio
import requests
from Sensor import Sensor

# Set name for module's log lines
log = logging.getLogger("DesktopTrigger")


class DesktopTrigger(Sensor):
    '''Driver for Linux computers running desktop-integration daemon. Makes API
    call every second to check if computer screen is turned on or off. Turns
    target devices on when screen is on, turns devices off when screen is off.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      current_rule: Initial rule, has different effects depending on subclass
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      ip:           The IPv4 address of the Linux computer
      port:         The port that the daemon is listening on (default=5000)

    Supports universal rules ("enabled" and "disabled").

    Can be used to keep lights on while user is at computer even if motion
    sensor does not detect motion (sitting still etc).
    '''

    def __init__(self, name, nickname, _type, default_rule, targets, ip, port=5000):
        super().__init__(name, nickname, _type, True, None, default_rule, targets)

        self.ip = ip
        self.port = port

        # Current monitor state
        self.current = None

        # Find desktop target so monitor loop (below) can update target's state
        # attribute when screen turns on/off
        for i in self.targets:
            if i._type == "desktop" and i.uri == f"{self.ip}:{self.port}":
                self.desktop_target = i
                break
        else:
            self.desktop_target = None

        # Run monitor loop
        self.monitor_task = asyncio.create_task(self.monitor())

        log.info(f"Instantiated Desktop named {self.name}: ip = {self.ip}, port = {self.port}")

    def enable(self):
        '''Sets enabled bool to True (allows sensor to be checked), ensures
        current_rule contains a usable value, refreshes group (check sensor),
        restarts monitor loop if stopped (checks user activity every second).
        '''

        # Restart loop if stopped
        if self.monitor_task is None:
            self.print(f"{self.name}: Start monitor loop")
            self.monitor_task = asyncio.create_task(self.monitor())
        super().enable()

    def disable(self):
        '''Sets enabled bool to False (prevents sensor from being checked),
        stops monitor loop, and refreshes group (turn devices OFF if other
        sensor conditions not met).
        '''

        # Stop loop if running
        if self.monitor_task is not None:
            self.print(f"{self.name}: Stop monitor loop")
            self.monitor_task.cancel()
            # Allow enable method to restart loop
            self.monitor_task = None
        super().disable()

    def get_idle_time(self):
        '''Makes API call to get time (milliseconds) since last user activity,
        returns response object (JSON).
        '''
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/idle_time', timeout=2)
            if response.status_code == 200:
                return response.json()
            raise OSError
        except OSError:
            # Desktop offline or different service running on port 5000, disable
            self.print("Fatal error (unable to connect to desktop), disabling")
            log.info(f"{self.name}: Fatal error (unable to connect to desktop), disabling")
            self.disable()
            return False

    def get_monitor_state(self):
        '''Makes API call to get current computer screen state, returns
        response ("On" or "Off"). Returns False if request fails.
        '''
        try:
            return requests.get(
                f'http://{self.ip}:{self.port}/state',
                timeout=2
            ).json()["state"]
        except (OSError, IndexError):
            # Wifi interruption, return False - caller will try again in 1 second
            self.print(f"{self.name}: failed to get state (wifi error)")
            return False
        except ValueError:
            # Response doesn't contain JSON (different service running on port 5000), disable
            self.print("Fatal error (unexpected response from desktop), disabling")
            log.info(f"{self.name}: Fatal error (unexpected response from desktop), disabling")
            self.disable()
            return False

    def condition_met(self):
        '''Returns True if computer screen is turned on, False if computer
        screen is turned off.
        '''
        if self.current == "On":
            return True
        else:
            return False

    def trigger(self):
        '''Called by trigger_sensor API endpoint, simulates sensor condition
        met (computer screen turned on).
        '''
        self.current = "On"
        self.refresh_group()
        return True

    async def monitor(self):
        '''Async coroutine that runs while sensor is enabled. Makes API call
        every second to check monitor state, saves in self.current attribute.

        Desktop returns values other than "On" and "Off" in some situations
        (standby, lock screen, etc), so condition_met cannot rely on a single
        get_monitor_state call. Instead state is continuously monitored and the
        condition_met method returns response from most-recent check.
        '''

        log.debug(f"{self.name}: Starting DesktopTrigger.monitor coro")
        try:
            while True:
                # Get new reading
                new = self.get_monitor_state()

                # At lock screen, or getting "Disabled" for a few seconds (NVIDIA Prime sync quirk)
                # Discard new reading, wait 1 second, try again
                if new != "On" and new != "Off":
                    await asyncio.sleep(1)
                    continue

                # State changed, overwrite self.current with new reading
                if new != self.current:
                    self.print(f"Monitors changed from {self.current} to {new}")
                    log.debug(f"{self.name}: Monitors changed from {self.current} to {new}")
                    self.current = new

                    # TODO make this behavior configurable
                    # If monitors just turned off (indicates user NOT present), turn off lights
                    if self.current == "Off":
                        # Override motion sensors to False, devices will turn off unless dummy/switch/thermostat present
                        for sensor in self.group.triggers:
                            if sensor._type == "pir":
                                sensor.motion = False

                        # Update target's state, enables loop to turn screen back on if needed (dummy/switch present)
                        if self.desktop_target:
                            self.desktop_target.state = False

                        # Force group to apply actions so above overrides can take effect
                        # If no dummy/switch is present (or if reading False), all devices will turn OFF
                        # If dummy/switch reading True is present, lights stay ON and screen turns back ON to match
                        self.group.reset_state()

                    # If monitors just turned on, update target's state
                    elif self.current == "On":
                        if self.desktop_target:
                            self.desktop_target.state = True

                    # Refresh group
                    self.refresh_group()

                # Poll every second
                await asyncio.sleep(1)

        # Sensor disabled, exit loop
        except asyncio.CancelledError:
            log.debug(f"{self.name}: Exiting DesktopTrigger.monitor coro")
            return False

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()

        # Replace desktop_target instance with instance.name
        attributes["desktop_target"] = attributes["desktop_target"].name

        # Replace monitor_task with True or False
        if attributes["monitor_task"] is not None:
            attributes["monitor_task"] = True
        else:
            attributes["monitor_task"] = False

        return attributes
