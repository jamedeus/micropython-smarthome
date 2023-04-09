from django.test import TestCase, Client
from django.conf import settings
import json, os
from .views import validateConfig, get_modules, get_api_target_menu_options
from .models import Config, Node, WifiCredentials

# Large JSON objects, helper functions
from .unit_test_helpers import request_payload, create_test_nodes, clean_up_test_nodes



# Test function that generates JSON used to populate API target set_rule menu
class ApiTargetMenuOptionsTest(TestCase):
    def test_empty_database(self):
        # Should return empty template when no Nodes exist
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}})

    def test_from_api_frontend(self):
        # Create nodes
        create_test_nodes()

        # Request options with no argument (used by Api frontend)
        options = get_api_target_menu_options()

        # Should return valid options for each device and sensor of all existing nodes
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'test1': '192.168.1.123', 'test2': '192.168.1.124', 'test3': '192.168.1.125'}, 'self-target': {}, 'test1': {'device1-Cabinet Lights (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device2-Overhead Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor']}, 'test2': {'device1-Air Conditioner (api-target)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Thermostat (si7021)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot']}, 'test3': {'device1-Bathroom LEDs (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device2-Bathroom Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device3-Entry Light (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (Bath) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor'], 'sensor2-Motion Sensor (Entry) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor']}})

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_from_edit_config(self):
        # Create nodes
        create_test_nodes()

        # Request options with friendly name as argument (used by edit_config)
        options = get_api_target_menu_options('test1')

        # Should return valid options for each device and sensor of all existing nodes, except test1
        # Should include test1's options in self-target section, should not be in main section
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'test2': '192.168.1.124', 'test3': '192.168.1.125'}, 'self-target': {'device1-Cabinet Lights (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device2-Overhead Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor']}, 'test2': {'device1-Air Conditioner (api-target)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Thermostat (si7021)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot']}, 'test3': {'device1-Bathroom LEDs (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device2-Bathroom Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'device3-Entry Light (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (Bath) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor'], 'sensor2-Motion Sensor (Entry) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'reboot', 'trigger_sensor']}})

        # Remove test configs from disk
        clean_up_test_nodes()



# Test setting default wifi credentials
class WifiCredentialsTests(TestCase):
    def test_setting_credentials(self):
        # Database should be empty
        self.assertEqual(len(WifiCredentials.objects.all()), 0)

        # Set default credentials, verify response + database
        response = self.client.post('/set_default_credentials', json.dumps({'ssid': 'AzureDiamond', 'password': 'hunter2'}), content_type='application/json')
        self.assertEqual(response.json(), 'Default credentials set')
        self.assertEqual(len(WifiCredentials.objects.all()), 1)

        # Overwrite credentials, verify model only contains 1 entry
        response = self.client.post('/set_default_credentials', json.dumps({'ssid': 'NewWifi', 'password': 'hunter2'}), content_type='application/json')
        self.assertEqual(response.json(), 'Default credentials set')
        self.assertEqual(len(WifiCredentials.objects.all()), 1)



# Test duplicate detection
class DuplicateDetectionTests(TestCase):
    def test_check_duplicate(self):
        # Should accept new name
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test Config'}), content_type='application/json')
        self.assertEqual(response.json(), 'Name OK.')

        # Create config with same name
        Client().post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')

        # Should now reject (identical name)
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test Config'}), content_type='application/json')
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should reject regardless of capitalization
        response = self.client.post('/check_duplicate', json.dumps({'name': 'unit test config'}), content_type='application/json')
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should accept different name
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test'}), content_type='application/json')
        self.assertEqual(response.json(), 'Name OK.')



# Test delete config
class DeleteConfigTests(TestCase):
    def setUp(self):
        # Generate Config, will be deleted below
        self.client = Client()
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Delete the Config created in setUp, confirm response message, confirm removed from database + disk
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Deleted unit-test-config.json')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertFalse(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_non_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Attempt to delete non-existing Config, confirm fails with correct message
        response = self.client.post('/delete_config', json.dumps('does-not-exist.json'), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Failed to delete does-not-exist.json, does not exist')

        # Confirm Config still exists
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_invalid_permission(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Make read-only
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o444)
        os.chmod(settings.CONFIG_DIR, 0o554)

        # Attempt to delete, confirm fails with permission denied error
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'), content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), 'Failed to delete, permission denied. This will break other features, check your filesystem permissions.')

        # Confirm Config still exists
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

        # Undo permissions
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o664)
        os.chmod(settings.CONFIG_DIR, 0o775)



class DeleteNodeTests(TestCase):
    def setUp(self):
        # Generate Config for test Node
        self.client = Client()
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

        # Create Node, add Config reverse relation
        self.node = Node.objects.create(friendly_name="Test Node", ip="192.168.1.123", floor="5")
        self.config = Config.objects.all()[0]
        self.config.node = self.node
        self.config.save()

    def test_delete_existing_node(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Delete the Node created in setUp, confirm response message, confirm removed from database + disk
        response = self.client.post('/delete_node', json.dumps('Test Node'), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Deleted Test Node')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)
        self.assertFalse(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_non_existing_node(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Attempt to delete non-existing Node, confirm fails with correct message
        response = self.client.post('/delete_node', json.dumps('Wrong Node'), content_type='application/json')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), 'Failed to delete Wrong Node, does not exist')

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_invalid_permission(self):
        # Confirm starting conditions
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Make read-only
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o444)
        os.chmod(settings.CONFIG_DIR, 0o554)

        # Attempt to delete, confirm fails with permission denied error
        response = self.client.post('/delete_node', json.dumps('Test Node'), content_type='application/json')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), 'Failed to delete, permission denied. This will break other features, check your filesystem permissions.')

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

        # Undo permissions
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o664)
        os.chmod(settings.CONFIG_DIR, 0o775)



# Test function that takes config file, returns list of dependencies for upload
class GetModulesTests(TestCase):
    def setUp(self):
        with open('node_configuration/unit-test-config.json') as file:
            self.config = json.load(file)

    def test_get_modules_full_config(self):
        modules, libs = get_modules(self.config)
        self.assertEqual(modules, {'devices/LedStrip.py', 'ir-remote/samsung-codes.json', 'ir-remote/whynter-codes.json', 'devices/Device.py', 'devices/Tplink.py', 'sensors/Sensor.py', 'sensors/Dummy.py', 'devices/Wled.py', 'devices/Mosfet.py', 'sensors/Thermostat.py', 'devices/IrBlaster.py', 'sensors/Switch.py', 'devices/Desktop_target.py', 'sensors/Desktop_trigger.py', 'devices/DumbRelay.py', 'sensors/MotionSensor.py', 'devices/Relay.py'})
        self.assertEqual(libs, ['lib/logging.py', 'lib/si7021.py', 'lib/ir_tx/__init__.py', 'lib/ir_tx/nec.py'])

    def test_get_modules_empty_config(self):
        modules, libs = get_modules({})
        self.assertEqual(modules, set())
        self.assertEqual(libs, ['lib/logging.py'])

    def test_get_modules_no_ir_blaster(self):
        config = self.config.copy()
        del config['ir_blaster']
        modules, libs = get_modules(config)
        self.assertEqual(modules, {'devices/LedStrip.py', 'devices/Device.py', 'devices/Tplink.py', 'sensors/Sensor.py', 'sensors/Dummy.py', 'devices/Wled.py', 'devices/Mosfet.py', 'sensors/Thermostat.py', 'sensors/Switch.py', 'devices/Desktop_target.py', 'sensors/Desktop_trigger.py', 'devices/DumbRelay.py', 'sensors/MotionSensor.py', 'devices/Relay.py'})
        self.assertEqual(libs, ['lib/logging.py', 'lib/si7021.py'])

    def test_get_modules_no_thermostat(self):
        config = self.config.copy()
        del config['sensor5']
        modules, libs = get_modules(config)
        self.assertEqual(modules, {'devices/LedStrip.py', 'ir-remote/samsung-codes.json', 'ir-remote/whynter-codes.json', 'devices/Device.py', 'devices/Tplink.py', 'sensors/Sensor.py', 'sensors/Dummy.py', 'devices/Wled.py', 'devices/Mosfet.py', 'devices/IrBlaster.py', 'sensors/Switch.py', 'devices/Desktop_target.py', 'sensors/Desktop_trigger.py', 'devices/DumbRelay.py', 'sensors/MotionSensor.py', 'devices/Relay.py'})
        self.assertEqual(libs, ['lib/logging.py', 'lib/ir_tx/__init__.py', 'lib/ir_tx/nec.py'])

    def test_get_modules_realistic(self):
        config = self.config.copy()
        del config['ir_blaster']
        del config['sensor3']
        del config['sensor4']
        del config['sensor5']
        del config['device4']
        del config['device5']
        del config['device7']
        modules, libs = get_modules(config)
        self.assertEqual(modules, {'devices/LedStrip.py', 'devices/Device.py', 'devices/Tplink.py', 'sensors/Sensor.py', 'devices/Wled.py', 'sensors/Switch.py', 'sensors/MotionSensor.py', 'devices/Relay.py'})
        self.assertEqual(libs, ['lib/logging.py'])



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
