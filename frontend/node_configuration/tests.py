from django.test import TestCase, Client
import json
from .views import validateConfig
from .models import Config

# Simulated input from user creating config with frontend
request_payload = {"friendlyName":"Unit Test Config","location":"build pipeline","floor":"0","ssid":"jamnet","password":"cjZY8PTa4ZQ6S83A","sensors":{"sensor1":{"id":"sensor1","new":False,"modified":False,"type":"pir","nickname":"Motion","pin":"4","default_rule":5,"targets":["device1","device2","device5","device6"],"schedule":{"08:00":"5","22:00":"1"}},"sensor2":{"id":"sensor2","new":False,"modified":False,"type":"switch","nickname":"Switch","pin":"5","default_rule":"enabled","targets":["device4","device7"],"schedule":{}},"sensor3":{"id":"sensor3","new":False,"modified":False,"type":"dummy","nickname":"Override","default_rule":"on","targets":["device3"],"schedule":{"06:00":"on","18:00":"off"}},"sensor4":{"id":"sensor4","new":False,"modified":False,"type":"desktop","nickname":"Activity","ip":"192.168.1.150","default_rule":"enabled","targets":["device1","device2","device5","device6"],"schedule":{"08:00":"enabled","22:00":"disabled"}},"sensor5":{"id":"sensor5","new":False,"modified":False,"type":"si7021","nickname":"Temperature","mode":"cool","tolerance":"3","default_rule":71,"targets":["device4","device7"],"schedule":{"08:00":"73","22:00":"69"}}},"devices":{"device1":{"id":"device1","new":False,"modified":False,"type":"dimmer","nickname":"Overhead","ip":"192.168.1.105","default_rule":100,"schedule":{"08:00":"100","22:00":"35"}},"device2":{"id":"device2","new":False,"modified":False,"type":"bulb","nickname":"Lamp","ip":"192.168.1.106","default_rule":75,"schedule":{"08:00":"100","22:00":"35"}},"device3":{"id":"device3","new":False,"modified":False,"type":"relay","nickname":"Porch Light","ip":"192.168.1.107","default_rule":"enabled","schedule":{"06:00":"disabled","18:00":"enabled"}},"device4":{"id":"device4","new":False,"modified":False,"type":"dumb-relay","nickname":"Fan","pin":"18","default_rule":"disabled","schedule":{}},"device5":{"id":"device5","new":False,"modified":False,"type":"desktop","nickname":"Screen","ip":"192.168.1.150","default_rule":"enabled","schedule":{"08:00":"enabled","22:00":"disabled"}},"device6":{"id":"device6","new":False,"modified":False,"type":"pwm","nickname":"Cabinet Lights","pin":"26","min":"0","max":"1023","default_rule":721,"schedule":{}},"device7":{"id":"device7","new":False,"modified":False,"type":"mosfet","nickname":"Humidifier","pin":"19","default_rule":"disabled","schedule":{}},"device8":{"id":"device8","new":False,"modified":False,"type":"wled","nickname":"TV Bias Lights","ip":"192.168.1.110","default_rule":128,"schedule":{"08:00":"100"}},"device9":{"id":"device9","new":True,"modified":False,"type":"ir-blaster","pin":"23","target":["tv"],"schedule":{}}}}



# Test config generator backend function
class GenerateConfigFileTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_generate_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')

        # Confirm model was created
        self.assertEqual(len(Config.objects.all()), 1)
        config = Config.objects.all()[0]

        # Confirm output file is same as existing
        with open('node_configuration/unit-test-config.json') as file:
            compare = json.load(file)
            self.assertEqual(config.config, compare)

    def test_duplicate_config_name(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view, confirm response + model created
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')
        self.assertEqual(len(Config.objects.all()), 1)

        # Post again, should throw error (duplicate name), should not create model
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')
        self.assertEqual(len(Config.objects.all()), 1)



# Test the validateConfig function called when user submits config generator form
class ValidateConfigTests(TestCase):
    def setUp(self):
        with open('node_configuration/unit-test-config.json') as file:
            self.valid_config = json.load(file)

    def test_valid_config(self):
        result = validateConfig(self.valid_config)
        self.assertTrue(result)

    def test_invalid_floor(self):
        config = self.valid_config.copy()
        config['metadata']['floor'] = 'top'
        result = validateConfig(config)
        self.assertEqual(result, 'Invalid floor, must be integer')

    def test_duplicate_nicknames(self):
        config = self.valid_config.copy()
        config['device4']['nickname'] = config['device1']['nickname']
        result = validateConfig(config)
        self.assertEqual(result, 'Contains duplicate nicknames')

    def test_duplicate_pins(self):
        config = self.valid_config.copy()
        config['sensor2']['pin'] = config['sensor1']['pin']
        result = validateConfig(config)
        self.assertEqual(result, 'Contains duplicate pins')

    def test_invalid_device_pin(self):
        config = self.valid_config.copy()
        config['device1']['pin'] = '14'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid device pin {config["device1"]["pin"]} used')

    def test_invalid_sensor_pin(self):
        config = self.valid_config.copy()
        config['sensor1']['pin'] = '3'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid sensor pin {config["sensor1"]["pin"]} used')

    def test_noninteger_pin(self):
        config = self.valid_config.copy()
        config['sensor1']['pin'] = 'three'
        result = validateConfig(config)
        self.assertEqual(result, 'Invalid pin (non-integer)')

    def test_invalid_device_type(self):
        config = self.valid_config.copy()
        config['device1']['type'] = 'nuclear'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid device type {config["device1"]["type"]} used')

    def test_invalid_sensor_type(self):
        config = self.valid_config.copy()
        config['sensor1']['type'] = 'ozone-sensor'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid sensor type {config["sensor1"]["type"]} used')

    def test_invalid_ip(self):
        config = self.valid_config.copy()
        config['device1']['ip'] = '192.168.1.500'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid IP {config["device1"]["ip"]}')

    def test_thermostat_tolerance_out_of_range(self):
        config = self.valid_config.copy()
        config['sensor5']['tolerance'] = 12.5
        result = validateConfig(config)
        self.assertEqual(result, f'Thermostat tolerance out of range (0.1 - 10.0)')

    def test_invalid_thermostat_tolerance(self):
        config = self.valid_config.copy()
        config['sensor5']['tolerance'] = 'low'
        result = validateConfig(config)
        self.assertEqual(result, f'Invalid thermostat tolerance {config["sensor5"]["tolerance"]}')

    def test_pwm_min_greater_than_max(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 1023
        config['device6']['max'] = 500
        config['device6']['default_rule'] = 700
        result = validateConfig(config)
        self.assertEqual(result, 'PWM min cannot be greater than max')

    def test_pwm_limits_negative(self):
        config = self.valid_config.copy()
        config['device6']['min'] = -50
        config['device6']['max'] = -5
        result = validateConfig(config)
        self.assertEqual(result, 'PWM limits cannot be less than 0')

    def test_pwm_limits_over_max(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 1023
        config['device6']['max'] = 4096
        result = validateConfig(config)
        self.assertEqual(result, 'PWM limits cannot be greater than 1023')

    def test_pwm_invalid_default_rule(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 500
        config['device6']['max'] = 1000
        config['device6']['default_rule'] = 1100
        result = validateConfig(config)
        self.assertEqual(result, 'PWM default rule invalid, must be between max and min')

    def test_pwm_invalid_default_rule(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 500
        config['device6']['max'] = 1000
        config['device6']['schedule']['01:00'] = 1023
        result = validateConfig(config)
        self.assertEqual(result, 'PWM invalid schedule rule 1023, must be between max and min')

    def test_pwm_noninteger_limit(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 'off'
        result = validateConfig(config)
        self.assertEqual(result, 'Invalid PWM limits or rules, must be int between 0 and 1023')
