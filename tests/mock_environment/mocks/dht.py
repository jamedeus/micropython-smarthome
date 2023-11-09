from machine import Pin


class DHT22:
    def __init__(self, pin_instance):
        self.pin = pin_instance
        # Defaults used before measure has been called
        self.temp = 0.0
        self.humid = 0.0

    def measure(self):
        # Throw error if pin is not correct instance
        if not isinstance(self.pin, Pin):
            raise ValueError("expecting a pin")
        # Set arbitrary constants
        self.temp = 21.0
        self.humid = 42.0

    def temperature(self):
        return self.temp

    def humidity(self):
        return self.humid
