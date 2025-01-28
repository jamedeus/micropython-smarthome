from machine import Pin
from Device import Device


class Relay(Device):
    '''Driver for relay breakout boards and other devices controlled by an
    output pin. Changes state of output pin connected to device when send
    method is called (HIGH if arg is True, LOW if arg is False).

    Args:
      name:         Unique, sequential config name (device1, device2, etc)
      nickname:     User-configured friendly name shown on frontend
      _type:        Instance type, determines driver class and frontend UI
      default_rule: Fallback rule used when no other valid rules are available
      schedule:     Dict with timestamps/keywords as keys, rules as values
      pin:          The ESP32 pin connected to the relay or other device

    Supports universal rules ("enabled" and "disabled").
    '''

    def __init__(self, name, nickname, _type, default_rule, schedule, pin, **kwargs):
        self.output = Pin(int(pin), Pin.OUT, Pin.PULL_DOWN)

        super().__init__(
            name=name,
            nickname=nickname,
            _type=_type,
            default_rule=default_rule,
            schedule=schedule,
            **kwargs
        )

        self.log.info("Instantiated, pin=%s", pin)

    def send(self, state=1):
        '''Sets pin level HIGH if arg is True.
        Sets pin level LOW if arg is False.
        '''
        self.log.debug(
            "send method called, rule=%s, state=%s",
            self.current_rule, state
        )

        # Refuse to turn disabled device on, but allow turning off (returning
        # True makes group set device state to True - allows turning off when
        # condition changes, would be skipped if device state already False)
        if not self.enabled and state:
            return True

        self.output.value(state)
        return True

    def get_attributes(self):
        '''Return JSON-serializable dict containing all current attributes
        Called by API get_attributes endpoint, more verbose than status
        '''
        attributes = super().get_attributes()
        # Remove Pin object (not serializable)
        del attributes["output"]
        return attributes
