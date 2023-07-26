from threading import Timer

AP_IF = 1
STA_IF = 0
STAT_ASSOC_FAIL = 203
STAT_BEACON_TIMEOUT = 200
STAT_CONNECTING = 1001
STAT_GOT_IP = 1010
STAT_HANDSHAKE_TIMEOUT = 204
STAT_IDLE = 1000
STAT_NO_AP_FOUND = 201
STAT_WRONG_PASSWORD = 202


class WLAN:
    # Singleton, simulate class reading hardware interface
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._active = False
            cls._instance._status = STAT_IDLE
            cls._instance.connected = False
        return cls._instance

    def active(self, state=None):
        if state is None:
            return self._active
        else:
            self._active = state

    def status(self):
        return self._status

    def isconnected(self):
        return self.connected

    # Connect after 100ms delay
    def connect(self, ssid, password):
        self._status = STAT_CONNECTING
        if ssid != "wrong":
            Timer(0.1, self.finish_connecting).start()
        else:
            Timer(0.1, self.fail_connection).start()

    # Runs 100ms after connect called
    def finish_connecting(self):
        self.connected = True
        self._status = STAT_GOT_IP

    # Simulate incorrect ssid, runs 100ms after connect
    def fail_connection(self):
        self.connected = False
        self._status = STAT_NO_AP_FOUND

    def disconnect(self):
        self.connected = False

    def ifconfig(*args):
        return ('127.0.0.1', '255.255.255.0', '192.168.1.1', '192.168.1.100')
