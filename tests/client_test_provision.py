import unittest
from provision import Provisioner
import json


class TestInstantiation(unittest.TestCase):

    def test_node_names(self):
        with open('nodes.json', 'r') as file:
            config = json.load(file)

        # Iterate all nodes, confirm set attributes match config file
        for i in config:
            app = Provisioner(['', i])
            self.assertEqual(app.passwd, 'password')
            self.assertEqual(app.config, config[i]["config"])
            self.assertEqual(app.host, config[i]["ip"])
            del app

    def test_arg_parse(self):
        # Use short flags
        app = Provisioner(['', '-p', 'fasdjkljfsa34', '-c', 'config/bedroom.json', '-ip', '192.168.1.224'])
        self.assertEqual(app.passwd, 'fasdjkljfsa34')
        self.assertEqual(app.config, 'config/bedroom.json')
        self.assertEqual(app.host, '192.168.1.224')

        # Use long flags
        app = Provisioner(
            [
                '',
                '--password',
                'fasdjkljfsa34',
                '--config',
                'config/bedroom.json',
                '--node',
                '192.168.1.224'
            ]
        )
        self.assertEqual(app.passwd, 'fasdjkljfsa34')
        self.assertEqual(app.config, 'config/bedroom.json')
        self.assertEqual(app.host, '192.168.1.224')

        # Omit password, should default to "password"
        app = Provisioner(['', '-c', 'config/bedroom.json', '-ip', '192.168.1.224'])
        self.assertEqual(app.passwd, 'password')
        self.assertEqual(app.config, 'config/bedroom.json')
        self.assertEqual(app.host, '192.168.1.224')

        # Should work in either order
        app = Provisioner(['', '-ip', '192.168.1.224', '-c', 'config/bedroom.json'])
        self.assertEqual(app.passwd, 'password')
        self.assertEqual(app.config, 'config/bedroom.json')
        self.assertEqual(app.host, '192.168.1.224')

        # Should exit with error if config omitted
        with self.assertRaises(SystemExit):
            app = Provisioner(['', '-ip', '192.168.1.224'])

        # Should exit with error if config is not .json
        with self.assertRaises(SystemExit):
            app = Provisioner(['', '-c', 'config/wrong-filetype.txt', '-ip', '192.168.1.224'])

        # Should exit with error if ip omitted
        with self.assertRaises(SystemExit):
            app = Provisioner(['', '-c', 'config/bedroom.json'])

        # Should exit with error if ip invalid
        with self.assertRaises(SystemExit):
            app = Provisioner(['', '-c', 'config/bedroom.json', '-ip', '999.000.999.000'])


class TestGetModules(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.app = Provisioner(['', 'bedroom'])

    def test_all(self):
        # Config containing all device and sensor types
        config = {
            'device1': {
                '_type': 'bulb'
            },
            'device2': {
                '_type': 'dimmer'
            },
            'device3': {
                '_type': 'relay'
            },
            'device4': {
                '_type': 'dumb-relay'
            },
            'device5': {
                '_type': 'desktop'
            },
            'device6': {
                '_type': 'pwm'
            },
            'device7': {
                '_type': 'mosfet'
            },
            'device8': {
                '_type': 'api-target'
            },
            'sensor1': {
                '_type': 'pir'
            },
            'sensor2': {
                '_type': 'si7021'
            },
            'sensor3': {
                '_type': 'dummy'
            },
            'sensor4': {
                '_type': 'desktop'
            },
            'ir_blaster': {}
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/DumbRelay.py',
                'devices/Tplink.py',
                'ir-remote/samsung-codes.json',
                'ir-remote/whynter-codes.json',
                'devices/ApiTarget.py',
                'devices/Desktop_target.py',
                'devices/IrBlaster.py',
                'devices/Mosfet.py',
                'sensors/Sensor.py',
                'devices/Relay.py',
                'sensors/Desktop_trigger.py',
                'devices/Device.py',
                'sensors/Thermostat.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py',
                'sensors/Dummy.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py', 'lib/si7021.py', 'lib/ir_tx/__init__.py', 'lib/ir_tx/nec.py'])

    def test_no_ir_blaster(self):
        # Config containing all devices and sensors except ir_blaster
        config = {
            'device1': {
                '_type': 'bulb'
            },
            'device2': {
                '_type': 'dimmer'
            },
            'device3': {
                '_type': 'relay'
            },
            'device4': {
                '_type': 'dumb-relay'
            },
            'device5': {
                '_type': 'desktop'
            },
            'device6': {
                '_type': 'pwm'
            },
            'device7': {
                '_type': 'mosfet'
            },
            'device8': {
                '_type': 'api-target'
            },
            'sensor1': {
                '_type': 'pir'
            },
            'sensor2': {
                '_type': 'si7021'
            },
            'sensor3': {
                '_type': 'dummy'
            },
            'sensor4': {
                '_type': 'desktop'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/DumbRelay.py',
                'devices/Tplink.py',
                'devices/ApiTarget.py',
                'devices/Desktop_target.py',
                'devices/Mosfet.py',
                'sensors/Sensor.py',
                'devices/Relay.py',
                'sensors/Desktop_trigger.py',
                'devices/Device.py',
                'sensors/Thermostat.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py',
                'sensors/Dummy.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py', 'lib/si7021.py'])

    def test_no_temp_sensor(self):
        # Config containing all devices and sensors except si7021
        config = {
            'device1': {
                '_type': 'bulb'
            },
            'device2': {
                '_type': 'dimmer'
            },
            'device3': {
                '_type': 'relay'
            },
            'device4': {
                '_type': 'dumb-relay'
            },
            'device5': {
                '_type': 'desktop'
            },
            'device6': {
                '_type': 'pwm'
            },
            'device7': {
                '_type': 'mosfet'
            },
            'device8': {
                '_type': 'api-target'
            },
            'sensor1': {
                '_type': 'pir'
            },
            'sensor3': {
                '_type': 'dummy'
            },
            'sensor4': {
                '_type': 'desktop'
            },
            'ir_blaster': {}
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/DumbRelay.py',
                'devices/Tplink.py',
                'ir-remote/samsung-codes.json',
                'ir-remote/whynter-codes.json',
                'devices/ApiTarget.py',
                'devices/Desktop_target.py',
                'devices/IrBlaster.py',
                'devices/Mosfet.py',
                'sensors/Sensor.py',
                'devices/Relay.py',
                'sensors/Desktop_trigger.py',
                'devices/Device.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py',
                'sensors/Dummy.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py', 'lib/ir_tx/__init__.py', 'lib/ir_tx/nec.py'])

    def test_no_sensors_with_libraries(self):
        # Config containing all devices and sensors that don't require libraries (excludes si7021 and ir_blaster)
        config = {
            'device1': {
                '_type': 'bulb'
            },
            'device2': {
                '_type': 'dimmer'
            },
            'device3': {
                '_type': 'relay'
            },
            'device4': {
                '_type': 'dumb-relay'
            },
            'device5': {
                '_type': 'desktop'
            },
            'device6': {
                '_type': 'pwm'
            },
            'device7': {
                '_type': 'mosfet'
            },
            'device8': {
                '_type': 'api-target'
            },
            'sensor1': {
                '_type': 'pir'
            },
            'sensor3': {
                '_type': 'dummy'
            },
            'sensor4': {
                '_type': 'desktop'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/DumbRelay.py',
                'devices/Tplink.py',
                'devices/ApiTarget.py',
                'devices/Desktop_target.py',
                'devices/Mosfet.py',
                'sensors/Sensor.py',
                'devices/Relay.py',
                'sensors/Desktop_trigger.py',
                'devices/Device.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py',
                'sensors/Dummy.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_pir_and_smart_bulb(self):
        # Config containing device/sensor combo used in multiple rooms
        config = {
            'sensor1': {
                '_type': 'pir'
            },
            'device1': {
                '_type': 'bulb'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'sensors/MotionSensor.py',
                'devices/Tplink.py',
                'devices/Device.py',
                'sensors/Sensor.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_pir_and_smart_bulb_and_dimmer(self):
        # Config containing device/sensor pair combo in multiple rooms
        config = {
            'sensor1': {
                '_type': 'pir'
            },
            'device1': {
                '_type': 'bulb'
            },
            'device2': {
                '_type': 'dimmer'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'sensors/MotionSensor.py',
                'devices/Tplink.py',
                'devices/Device.py',
                'sensors/Sensor.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_pir_and_led_strip(self):
        # Config containing device/sensor combo used in multiple rooms
        config = {
            'sensor1': {
                '_type': 'pir'
            },
            'device1': {
                '_type': 'pwm'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/LedStrip.py',
                'sensors/MotionSensor.py',
                'devices/Device.py',
                'sensors/Sensor.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_pir_and_led_strip_and_dumbrelay(self):
        # Config containing device/sensor combo used in multiple rooms
        config = {
            'sensor1': {
                '_type': 'pir'
            },
            'device1': {
                '_type': 'pwm'
            },
            'device2': {
                '_type': 'dumb-relay'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/DumbRelay.py',
                'sensors/Sensor.py',
                'devices/Device.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_pir_and_led_strip_and_relay(self):
        # Config containing device/sensor combo used in kitchen
        config = {
            'sensor1': {
                '_type': 'pir'
            },
            'device1': {
                '_type': 'pwm'
            },
            'device2': {
                '_type': 'relay'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'sensors/Sensor.py',
                'devices/Relay.py',
                'devices/Device.py',
                'devices/LedStrip.py',
                'sensors/MotionSensor.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_thermostat_and_relay(self):
        # Config containing device/sensor pair used for thermostat
        config = {
            'sensor1': {
                '_type': 'si7021'
            },
            'device1': {
                '_type': 'relay'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'devices/Relay.py',
                'sensors/Sensor.py',
                'devices/Device.py',
                'sensors/Thermostat.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py', 'lib/si7021.py'])

    def test_bedroom(self):
        # Config containing all devices/sensors currently used in bedroom
        config = {
            'device1': {
                '_type': 'dimmer'
            },
            'device2': {
                '_type': 'desktop'
            },
            'sensor1': {
                '_type': 'pir'
            },
            'sensor2': {
                '_type': 'pir'
            },
            'sensor3': {
                '_type': 'desktop'
            },
            'sensor4': {
                '_type': 'dummy'
            }
        }

        modules, libs = self.app.get_modules(config)

        self.assertEqual(
            modules,
            {
                'sensors/MotionSensor.py',
                'sensors/Sensor.py',
                'devices/Device.py',
                'sensors/Desktop_trigger.py',
                'devices/Tplink.py',
                'sensors/Dummy.py',
                'devices/Desktop_target.py'
            }
        )
        self.assertEqual(libs, ['lib/logging.py'])

    def test_empty_config(self):
        config = {}

        modules, libs = self.app.get_modules(config)

        # Should still return logging module which is always used
        self.assertEqual(modules, set())
        self.assertEqual(libs, ['lib/logging.py'])


#def gen_config(conf, which, type):
    #if which == "device":
        #count = 1
        #for i in conf:
            #if i.startswith("device"):
                #count += 1

    #elif which == "sensor":
        #count = 1
        #for i in conf:
            #if i.startswith("sensor"):
                #count += 1

    #conf[which + str(count)] = {}
    #conf[which + str(count)]["type"] = type

    #return conf
