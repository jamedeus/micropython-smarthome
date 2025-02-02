import asyncio
import requests
from HttpGet import HttpGet
from DriverLoopMixin import DriverLoopMixin

# Paths used by Tasmota to turn on, off
ON_PATH = 'cm?cmnd=Power%20On'
OFF_PATH = 'cm?cmnd=Power%20Off'


class TasmotaRelay(HttpGet):
    '''Driver for smart relays running Tasmota. Makes Tasmota API calls when
    send method called (turn ON if arg is True, turn OFF if arg is False).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      ip:           The IPv4 address of the Tasmota relay

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, ip, **kwargs):
        super().__init__(
            name=name,
            nickname=nickname,
            _type=_type,
            default_rule=default_rule,
            schedule=schedule,
            uri=ip,
            on_path=ON_PATH,
            off_path=OFF_PATH,
            **kwargs
        )

        # Run monitor loop (requests power state every 5 seconds to keep in
        # sync if user flips wall switch)
        self.monitor_task = asyncio.create_task(self.monitor())

        self.log.info("Instantiated, ip=%s", self.uri)

    def enable(self):
        '''Sets enabled bool to True (allows device to be turned on), ensures
        current_rule contains a usable value, and turns the device on if group
        state is True (one or more sensor targeting device has condition met).
        Restarts monitor loop if stopped (poll device for external changes).
        '''
        return DriverLoopMixin.enable(self, HttpGet)

    def disable(self):
        '''Sets enabled bool to False (prevents device from being turned on),
        turns device off if currently turned on, and stops monitor loop.
        '''
        return DriverLoopMixin.disable(self, HttpGet)

    def check_state(self):
        '''Makes API call to get Tasmota relay power state, return response'''

        try:
            return requests.get(
                f'http://{self.uri}/cm?cmnd=Power',
                timeout=2
            ).json()["POWER"]
        except OSError:
            self.log.error("network error while checking state")
            raise RuntimeError

    async def monitor(self):
        '''Async coroutine that runs while device is enabled. Queries power
        state from Tasmota device every 5 seconds and updates self.state (keeps
        in sync with actual device when user uses wall switch).
        '''
        self.log.debug("Starting TasmotaRelay.monitor coro")
        try:
            while True:
                try:
                    power = self.check_state() == "ON"
                    if power != self.state:
                        self.log.debug("monitor: power state changed to %s", power)
                        self.state = power
                except RuntimeError:
                    # Error during request, ignore
                    pass

                # Poll every 5 seconds
                await asyncio.sleep(5)

        # Device disabled, exit loop
        except asyncio.CancelledError:
            self.log.debug("Exiting TasmotaRelay.monitor coro")
            return False

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        return DriverLoopMixin.get_attributes(self, HttpGet)
