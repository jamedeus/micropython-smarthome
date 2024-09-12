import logging
import asyncio
import requests
from SensorWithLoop import SensorWithLoop

# Set name for module's log lines
log = logging.getLogger("DesktopTrigger")


class DesktopTrigger(SensorWithLoop):
    '''Driver for Linux computers running desktop-integration daemon. Makes API
    call every second to check if computer screen is turned on or off. Turns
    target devices on when screen is on, turns devices off when screen is off.

    Args:
      name:         Unique, sequential config name (sensor1, sensor2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      enabled:      Initial enable state (True or False)
      default_rule: Fallback rule used when no other valid rules are available
      targets:      List of device names (device1 etc) controlled by sensor
      mode:         Either "screen" or "activity", determines sensor condition
      ip:           The IPv4 address of the Linux computer
      port:         The port that the daemon is listening on (default=5000)

    Supports universal rules ("enabled" and "disabled").

    Can be used to keep lights on while user is at computer even if motion
    sensor does not detect motion (sitting still etc).

    If the mode argument is "activity" the sensor condition is met when there
    has been user activity (mouse or keyboard) in the last 60 seconds. If mode
    is "screen" the condition is met whenever the screen is turned on and not
    met when the screen is off, regardless of last user activity.
    '''

    def __init__(self, name, nickname, _type, default_rule, targets, mode, ip, port=5000):
        super().__init__(name, nickname, _type, True, default_rule, targets)

        self.ip = ip
        self.port = port

        # Current monitor state
        self.current = None

        # Determines when condition is met, must be "screen" or "activity"
        if mode.lower() in ["screen", "activity"]:
            self.mode = mode.lower()
        else:
            raise ValueError('Invalid mode, must be "screen" or "activity"')

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

        log.info(
            "Instantiated Desktop named %s: ip = %s, port = %s, mode = %s",
            self.name, self.ip, self.port, self.mode
        )

    def get_idle_time(self):
        '''Makes API call to get time (milliseconds) since last user activity,
        returns response object (JSON).
        '''
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/idle_time', timeout=2)
            if response.status_code == 200:
                return response.json()["idle_time"]
            raise OSError
        except OSError:
            # Wifi interruption, return False - caller will try again in 1 second
            log.error("%s: failed to get idle time (wifi error)", self.name)
            self.print(f"{self.name}: failed to get idle time (wifi error)")
            return False
        except (ValueError, IndexError):
            # Response doesn't contain JSON (different service running on port 5000), disable
            self.print("Fatal error (unexpected response from desktop), disabling")
            log.critical(
                "%s: Fatal error (unexpected response from desktop), disabling",
                self.name
            )
            self.disable()
            return False

    def get_monitor_state(self):
        '''Makes API call to get current computer screen state, returns
        response ("On" or "Off"). Returns False if request fails.
        '''
        try:
            response = requests.get(f'http://{self.ip}:{self.port}/state', timeout=2)
            if response.status_code == 200:
                return response.json()["state"]
            raise OSError
        except OSError:
            # Wifi interruption, return False - caller will try again in 1 second
            log.error("%s: failed to get state (wifi error)", self.name)
            self.print(f"{self.name}: failed to get state (wifi error)")
            return False
        except (ValueError, IndexError):
            # Response doesn't contain JSON (different service running on port 5000), disable
            self.print("Fatal error (unexpected response from desktop), disabling")
            log.critical(
                "%s: Fatal error (unexpected response from desktop), disabling",
                self.name
            )
            self.disable()
            return False

    def _condition_met_screen_mode(self):
        '''Returns True if computer screen is turned on, False if computer
        screen is turned off.
        '''
        return self.current == "On"

    def _condition_met_activity_mode(self):
        '''Returns True if computer user was active in last 60 seconds, False
        if no activity (keyboard or mouse) in last 60 seconds.
        '''
        try:
            return self.current <= 60000
        except TypeError:
            return False

    def condition_met(self):
        '''Checks condition configured with mode argument (screen or activity).
        Screen mode: Return True if computer screen is on, return False if off.
        Activity mode: Return True if user active in last 60 seconds, return
        False if no activity in last 60 seconds.
        '''
        if self.mode == "screen":
            return self._condition_met_screen_mode()
        return self._condition_met_activity_mode()

    def trigger(self):
        '''Called by trigger_sensor API endpoint, simulates sensor condition
        met. If mode is "screen" sets current to "On" (simulate screen turned
        on), if mode is "activity" sets current to 0 (0ms since user active).
        '''
        log.debug("%s: trigger method called", self.name)
        if self.mode == "screen":
            self.current = "On"
        else:
            self.current = 0
        self.refresh_group()
        return True

    def _get_current_screen_mode(self):
        '''Fetches current monitor state ("On" or "Off") from desktop daemon
        API, saves response in self.current attribute checked by condition_met.
        Refreshes group if response has changed since last API call.

        Desktop returns values other than "On" and "Off" in some situations
        (standby, lock screen, etc), these are ignored (self.current retains
        previous response until a new valid response is received).
        '''

        # Get new reading
        new = self.get_monitor_state()
        log.debug("%s: monitor state: %s", self.name, new)

        # At lock screen, or getting "Disabled" for a few seconds (NVIDIA Prime
        # quirk), return without updating self.current
        if new not in ["On", "Off"]:
            return

        if new != self.current:
            self.print(f"Monitor state changed from {self.current} to {new}")
            log.debug(
                "%s: monitors changed from %s to %s",
                self.name, self.current, new
            )
            self.current = new

            if self.current == "Off":
                # Update desktop target's state (allows group to turn screen
                # back on, will get stuck off if state remains True)
                if self.desktop_target:
                    log.debug(
                        "%s: Set desktop target (%s) state to False",
                        self.name, self.desktop_target.name
                    )
                    self.desktop_target.state = False

                # Allow group to turn screen back on if other sensors in group
                # have condition met
                self.group.reset_state()

            # If monitors just turned on, update target's state
            elif self.current == "On":
                if self.desktop_target:
                    log.debug(
                        "%s: Set desktop target (%s) state to True",
                        self.name, self.desktop_target.name
                    )
                    self.desktop_target.state = True

            # Refresh group so new screen state can take effect
            self.refresh_group()

    def _get_current_activity_mode(self):
        '''Fetches time since last user activity (milliseconds) from desktop
        daemon API, saves response in self.current attribute checked by
        condition_met. Calls condition_met and refreshes group if condition
        does not match group state.
        '''

        # Get new reading
        new = self.get_idle_time()
        if new is not False:
            self.current = int(new)
            log.debug("%s: idle time: %s", self.name, self.current)

            if self.condition_met() != self.group.state:
                self.refresh_group()

        else:
            log.error("%s: failed to get idle time (backend error)", self.name)

    async def monitor(self):
        '''Async coroutine that runs while sensor is enabled. Makes API call
        to desktop daemon every second, refreshes group when condition changes.

        Screen mode: Check if computer monitors are turned On or Off, save
        response in self.current, refresh group when response changes.

        Activity mode: Get milliseconds since last user activity, save in
        self.current, refresh group when time exceeds/no longer exceeds 60
        seconds.
        '''
        log.debug("%s: Starting DesktopTrigger.monitor coro", self.name)
        try:
            while True:
                # Check correct condition for configured mode
                if self.mode == "screen":
                    self._get_current_screen_mode()
                else:
                    self._get_current_activity_mode()

                # Poll every second
                await asyncio.sleep(1)

        # Sensor disabled, exit loop
        except asyncio.CancelledError:
            log.debug("%s: Exiting DesktopTrigger.monitor coro", self.name)
            return False

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Replace desktop_target instance with instance.name
        attributes["desktop_target"] = attributes["desktop_target"].name
        return attributes
