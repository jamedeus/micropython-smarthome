STA_IF = "STA_IF"


class WLAN:
    def __init__(self, interface=STA_IF):
        self._active = False
        self.connected = False

    def active(self, state=None):
        if state is None:
            return self._active
        else:
            self._active = state

    def isconnected(self):
        return self.connected

    def connect(self, ssid, password):
        self.connected = True
