from threading import Timer

STAT_ASSOC_FAIL = 203
STAT_BEACON_TIMEOUT = 200
STAT_CONNECTING = 1001
STAT_GOT_IP = 1010
STAT_HANDSHAKE_TIMEOUT = 204
STAT_IDLE = 1000
STAT_NO_AP_FOUND = 201
STAT_WRONG_PASSWORD = 202


class WLAN:
    # Singleton for each interface
    # Simulate class reading hardware interfaces
    _instance_sta = None
    _instance_ap = None

    # Interface constants
    IF_AP = 1
    IF_STA = 0

    # Security constants
    SEC_OPEN = 0
    SEC_WEP = 1
    SEC_WPA = 2
    SEC_WPA2 = 3
    SEC_WPA_WPA2 = 4
    SEC_WPA2_ENT = 5
    SEC_WPA3 = 6
    SEC_WPA2_WPA3 = 7
    SEC_WAPI = 8
    SEC_OWE = 9

    # Power management constants
    PM_NONE = 0
    PM_PERFORMANCE = 1
    PM_POWERSAVE = 2

    def __new__(cls, interface=IF_STA, *args, **kwargs):
        # Station singleton
        if interface == cls.IF_STA:
            if cls._instance_sta is None:
                cls._instance_sta = super().__new__(cls)
                cls._instance_sta._active = False
                cls._instance_sta._status = STAT_IDLE
                cls._instance_sta.connected = False
                cls._instance_sta.interface = cls.IF_STA
                cls._instance_sta.reconnects = -1
                cls._instance_sta.ssid = ''
                cls._instance_sta._ifconfig = ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')
            return cls._instance_sta

        # Access point singleton
        elif interface == cls.IF_AP:
            if cls._instance_ap is None:
                cls._instance_ap = super().__new__(cls)
                cls._instance_ap._active = False
                cls._instance_ap._status = None
                cls._instance_ap.connected = False
                cls._instance_ap.interface = cls.IF_AP
                cls._instance_ap.ssid = 'ESP_80AEE9'
                cls._instance_ap._ifconfig = ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
            return cls._instance_ap

        else:
            raise ValueError

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
        # Only station can connect, must not already be connected
        if self.interface == self.IF_STA and self._status != STAT_GOT_IP:
            self._status = STAT_CONNECTING
            if password != "wrong":
                Timer(0.1, self.finish_connecting).start()
            else:
                Timer(0.1, self.fail_connection).start()

        # Access point cannot connect
        else:
            raise OSError("Wifi Internal Error")

    # Runs 100ms after connect called
    def finish_connecting(self):
        self.connected = True
        self._status = STAT_GOT_IP
        self._ifconfig = ('127.0.0.1', '255.255.255.0', '192.168.1.1', '192.168.1.100')

    # Simulate incorrect ssid, runs 100ms after connect
    def fail_connection(self):
        self.connected = False
        self._status = STAT_WRONG_PASSWORD

    def disconnect(self):
        self.connected = False

        if self.interface == self.IF_STA:
            self._ifconfig = ('0.0.0.0', '0.0.0.0', '0.0.0.0', '0.0.0.0')
            self._status = 8

    def config(self, lookup=None, reconnects=None, ssid=None):
        if lookup is not None:
            if lookup == "mac":
                return b'x!\x84\x80\xae\xe9'
            elif lookup == "reconnects" and "reconnects" in self.__dict__:
                return self.reconnects
            elif lookup == "ssid":
                return self.ssid
            else:
                raise ValueError("unknown config param")

        elif reconnects is not None:
            if self.interface == self.IF_STA:
                self.reconnects = reconnects
            else:
                raise OSError("STA required")

        elif ssid is not None:
            if self.interface == self.IF_STA:
                raise OSError("AP required")
            else:
                self.ssid = ssid

        else:
            raise TypeError("can query only one param")

    def ifconfig(self, config_tuple=None):
        if not config_tuple:
            return self._ifconfig
        if not isinstance(config_tuple, tuple):
            raise ValueError("invalid arguments")
        if len(config_tuple) != 4:
            raise ValueError(f"requested length 4 but object has length {len(config_tuple)}")
        else:
            self._ifconfig = config_tuple
