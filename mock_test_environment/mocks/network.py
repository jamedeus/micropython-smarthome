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

    def ifconfig(*args):
        return ('192.168.1.123', '255.255.255.0', '192.168.1.1', '192.168.1.100')
