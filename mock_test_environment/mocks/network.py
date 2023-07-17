STA_IF = "STA_IF"


class WLAN:
    # Singleton, simulate class reading hardware interface
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active = False
            cls._instance.connected = False
        return cls._instance

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
        return ('127.0.0.1', '255.255.255.0', '192.168.1.1', '192.168.1.100')
