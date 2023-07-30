class Si7021:
    def __init__(self, i2c):
        self.temperature = 21.0
        self.relative_humidity = 42.069


def convert_celcius_to_fahrenheit(celcius):
    return celcius * 1.8 + 32
