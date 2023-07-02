import json
import os
import socket
from copy import deepcopy
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ValidationError
from .views import validate_full_config, get_modules, get_api_target_menu_options, provision
from .models import Config, Node, WifiCredentials, ScheduleKeyword, GpsCoordinates
from Webrepl import websocket, Webrepl, handshake_message
from .validators import (
    validate_rules,
    api_target_validator,
    led_strip_validator,
    tplink_validator,
    wled_validator,
    dummy_validator,
    motion_sensor_validator,
    thermostat_validator,
)

# Large JSON objects, helper functions
from .unit_test_helpers import (
    JSONClient,
    request_payload,
    create_test_nodes,
    clean_up_test_nodes,
    test_config_1,
    test_config_2,
    simulate_reupload_all_partial_success,
    create_config_and_node_from_json,
    test_config_1_edit_context,
    test_config_2_edit_context,
    test_config_3_edit_context,
    simulate_corrupt_filesystem_upload,
    simulate_reupload_all_fail_for_different_reasons,
    binary_unit_test_config,
    simulate_read_file_over_webrepl,
    simulated_read_position,
)


# Test the Node model
class NodeTests(TestCase):
    def test_create_node(self):
        self.assertEqual(len(Node.objects.all()), 0)

        # Create node, confirm exists in database
        node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertIsInstance(node, Node)

        # Confirm friendly name shown when instance printed
        self.assertEqual(node.__str__(), 'Unit Test Node')

        # Confirm attributes, should not have config reverse relation
        self.assertEqual(node.friendly_name, 'Unit Test Node')
        self.assertEqual(node.ip, '123.45.67.89')
        self.assertEqual(node.floor, 2)
        with self.assertRaises(Node.config.RelatedObjectDoesNotExist):
            print(node.config)

        # Create Config with reverse relation, confirm accessible both ways
        config = Config.objects.create(config=test_config_1, filename='test1.json', node=node)
        self.assertEqual(node.config, config)
        self.assertEqual(config.node, node)

    def test_create_node_invalid(self):
        # Confirm starting condition
        self.assertEqual(len(Node.objects.all()), 0)

        # Should refuse to create with no arguments, only floor has default
        with self.assertRaises(ValidationError):
            Node.objects.create()

        # Should refuse to create with invalid IP
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.456.789.10')

        # Should refuse to create negative floor
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='-5')

        # Should refuse to create floor over 999
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='9999')

        # Should refuse to create non-int floor
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='upstairs')

        # Should refuse to create with friendly name >50 characters
        with self.assertRaises(ValidationError):
            Config.objects.create(config=test_config_1, filename='Unrealistically Long Friendly Name That Nobody Needs')

        # Confirm no nodes were created
        self.assertEqual(len(Node.objects.all()), 0)

    def test_create_duplicate_node(self):
        # Create node, confirm number in database
        Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        self.assertEqual(len(Node.objects.all()), 1)

        # Should refuse to create another node with same name
        with self.assertRaises(ValidationError):
            Node.objects.create(friendly_name='Unit Test Node', ip='123.45.1.9', floor='3')

        # Confirm no nodes created in db
        self.assertEqual(len(Node.objects.all()), 1)


# Test the Config model
class ConfigTests(TestCase):
    def test_create_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Create node, confirm exists in database
        config = Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertIsInstance(config, Config)

        # Confirm filename shown when instance printed
        self.assertEqual(config.__str__(), 'test1.json')

        # Confirm attributes, confirm no node reverse relation
        self.assertEqual(config.config, test_config_1)
        self.assertEqual(config.filename, 'test1.json')
        self.assertIsNone(config.node)

        # Create Node, add reverse relation
        node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='2')
        config.node = node
        config.save()

        # Confirm accessible both ways
        self.assertEqual(config.node, node)
        self.assertEqual(node.config, config)

    def test_create_config_invalid(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Should refuse to create with no arguments
        with self.assertRaises(ValidationError):
            Config.objects.create()

        # Should refuse to create with filename >50 characters
        with self.assertRaises(ValidationError):
            Config.objects.create(
                config=test_config_1,
                filename='unrealistically-long-config-name-that-nobody-needs.json'
            )

        # Confirm no configs created in db
        self.assertEqual(len(Config.objects.all()), 0)

    def test_duplicate_filename(self):
        # Create config, confirm number in database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)

        # Should refuse to create another config with same name
        with self.assertRaises(ValidationError):
            Config.objects.create(config=test_config_1, filename='test1.json')

        # Confirm no configs created in db
        self.assertEqual(len(Config.objects.all()), 1)

    def test_write_to_disk(self):
        # Create config
        config = Config.objects.create(config=test_config_1, filename='write_to_disk.json')

        # Config should not exist on disk
        self.assertFalse(os.path.exists(os.path.join(settings.CONFIG_DIR + 'write_to_disk.json')))

        # Call method, should exist
        config.write_to_disk()
        self.assertTrue(os.path.exists(os.path.join(settings.CONFIG_DIR + 'write_to_disk.json')))

        # Contents should match config attribute
        with open(os.path.join(settings.CONFIG_DIR + 'write_to_disk.json'), 'r') as file:
            output = json.load(file)
            self.assertEqual(config.config, output)

        # Remove file, prevent test failing after first run
        os.remove(os.path.join(settings.CONFIG_DIR + 'write_to_disk.json'))

    def test_read_from_disk(self):
        # Create config
        config = Config.objects.create(config=test_config_1, filename='read_from_disk.json')

        # Write different config to expected config path
        with open(os.path.join(settings.CONFIG_DIR + 'read_from_disk.json'), 'w') as file:
            json.dump(test_config_2, file)

        # Confirm configs are different
        self.assertNotEqual(config.config, test_config_2)

        # Call method, configs should now be identical
        config.read_from_disk()
        self.assertEqual(config.config, test_config_2)

        # Remove file
        os.remove(os.path.join(settings.CONFIG_DIR + 'read_from_disk.json'))


# Test websocket class used by Webrepl
class WebsocketTests(TestCase):

    def test_write_method(self):
        # Mock socket and client_handshake to do nothing
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(websocket, 'client_handshake', return_value=True):

            # Instantiate, write long string to trigger else (rest covered by Webrepl tests)
            ws = websocket(mock_socket)
            ws.write('test string longer than the 126 characters, which is the required number of characters to trigger the else clause in websocket.write')

    def test_recvexactly_method(self):
        # Mock socket.recv to return arbitrary data, mock client_handshake to do nothing
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(mock_socket, 'recv', return_value=b"A bunch of binary data"), \
             patch.object(websocket, 'client_handshake', return_value=True):

            # Instantiate, request data, verify response
            ws = websocket(mock_socket)
            data = ws.recvexactly(22)
            self.assertEqual(data, b"A bunch of binary data")

            # Change return value to trigger conditional, verify response
            mock_socket.recv.return_value = None
            data = ws.recvexactly(22)
            self.assertEqual(data, b"")

    # Arbitrary mocks to traverse every line in read method
    def test_read_method(self):
        # Mock socket and client_handshake to do nothing
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(websocket, 'client_handshake', return_value=True):

            # Instantiate websocket
            ws = websocket(mock_socket)

            # First call: return sz=5, fl=0x82 (trigger break in second if statement)
            # Second call: Return Hello
            with patch.object(websocket, 'recvexactly', side_effect=[b'\x82\x05', b'Hello']):
                # Read 5 bytes, confirm expected response
                data = ws.read(5)
                self.assertEqual(data, b'Hello')

            # First call: return sz=5, fl=0x81 (trigger last if statement in loop)
            # Second call: return World
            with patch.object(websocket, 'recvexactly', side_effect=[b'\x81\x05', b'World']):
                # Read 5 bytes, confirm expected response
                data = ws.read(5, text_ok=True)
                self.assertEqual(data, b'World')

            # First call: return sz=126 (trigger first if statement in loop)
            # Second call: return sz=15 (bytes to iterate in inner loop, evenly divisible by 5 bytes returned by recv)
            # Third call: return sz=16, fl=0x82 (trigger break in second if statement)
            # Fourth call: return 16 characters to final recvexactly statement in function
            recvexactly_side_effect = [b'\x81\x7E', b'\x00\x0F', b'\x82\x10', b'abcdefghijklmnop']
            with patch.object(websocket, 'recvexactly', side_effect=recvexactly_side_effect), \
                 patch.object(mock_socket, 'recv', return_value=b'abcde'):

                # Read 16 bytes, confirm expected response
                data = ws.read(16)
                self.assertEqual(data, b'abcdefghijklmnop')

    def test_client_handshake_method(self):
        # Mock object to replace socket.makefile.write
        mock_cl = MagicMock()
        mock_cl.write = MagicMock()
        mock_cl.readline = MagicMock(
            side_effect=[
                b'HTTP/1.1 101 Switching Protocols\r\n',
                b'Upgrade: websocket\r\n',
                b'Connection: Upgrade\r\n',
                b'\r\n'
            ]
        )

        # Mock socket to do nothing, mock makefile method to return object created above
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(mock_socket, 'makefile', return_value=mock_cl):

            # Instantiate, verify correct methods called
            websocket(mock_socket)
            mock_cl.write.assert_called_once_with(handshake_message)
            self.assertEqual(mock_cl.readline.call_count, 4)


# Test the Webrepl class used to upload config + dependencies to nodes
class WebreplTests(TestCase):

    def test_open_and_close_connection(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock all methods called by open_connection + close_connection to return True
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(websocket, 'client_handshake', return_value=True) as mock_client_handshake, \
             patch.object(Webrepl, 'login', return_value=True) as mock_login:

            # Should connect successfully due to mocks
            self.assertTrue(node.open_connection())

            # Confirm correct methods called
            mock_socket.return_value.settimeout.assert_called()
            mock_socket.return_value.connect.assert_called()
            mock_client_handshake.assert_called()
            mock_login.assert_called()

            # Confirm has websocket attribute
            self.assertIsInstance(node.ws, websocket)

            # Close connection, confirm method called, confirm lost websocket attribute
            self.assertTrue(node.close_connection())
            self.assertEqual(node.ws, None)
            mock_socket.return_value.close.assert_called()

    def test_bad_connection(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock the socket connect method to raise OSError, simulates failed connection
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket:
            mock_socket.return_value.connect.side_effect = OSError

            # Confirm open_connect catches the error and returns False
            self.assertFalse(node.open_connection())

    # Confirm error raised if login/read_resp called before open_connection
    def test_premature_method_calls(self):
        node = Webrepl('123.45.67.89', 'password')
        self.assertRaises(OSError, node.login)
        self.assertRaises(OSError, node.read_resp)

    # Confirm error raised if get/put_file methods called before open_connection and open_connection fails
    def test_premature_file_io(self):
        node = Webrepl('123.45.67.89', 'password')

        with patch.object(Webrepl, 'open_connection', return_value=False) as mock_open_connection:

            # All methods should attempt to open connection, raise OSError when it fails
            self.assertRaises(OSError, node.get_file, 'app.log', 'app.log')
            self.assertTrue(mock_open_connection.called)
            mock_open_connection.reset_mock()

            self.assertRaises(OSError, node.get_file_mem, 'app.log')
            self.assertTrue(mock_open_connection.called)
            mock_open_connection.reset_mock()

            self.assertRaises(OSError, node.put_file, 'app.log', 'app.log')
            self.assertTrue(mock_open_connection.called)

            self.assertRaises(OSError, node.put_file_mem, 'app.log', 'app.log')
            self.assertTrue(mock_open_connection.called)

    def test_get_file(self):
        node = Webrepl('123.45.67.89', 'password')
        local_file = "test_get_file_output.json"

        # Mock websocket read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl

        # Set simulated read starting position to beginning of file
        simulated_read_position[0] = 0

        # Mock open_connection to return True without doing anything
        # Mock websocket with object created above
        # Mock read_resp to return bytes indicating valid signature
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', ws_mock), \
             patch.object(node, 'read_resp', side_effect=[0, 0]):

            # Call method, should receive simulated data stream and write to disk
            node.get_file(local_file, "/path/to/remote")

        # Confirm expected data written
        with open(local_file, 'rb') as f:
            get_file_output = f.read()
            self.assertEqual(binary_unit_test_config, get_file_output)

        # Delete test file
        os.remove(local_file)

    def test_get_file_mem(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock websocket read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl

        # Set simulated read starting position to beginning of file
        simulated_read_position[0] = 0

        # Mock open_connection to return True without doing anything
        # Mock websocket with object created above
        # Mock read_resp to return bytes indicating valid signature
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', ws_mock), \
             patch.object(node, 'read_resp', side_effect=[0, 0]):

            # Call method, confirm returns expected data stream
            result = node.get_file_mem("/path/to/remote")
            self.assertEqual(binary_unit_test_config, result)

    # Confirm OSError raised when either get_file or get_file_mem receive empty buffer during read
    def test_get_file_failed_read(self):
        node = Webrepl('123.45.67.89', 'password')

        # Return buffer that unpacks to 256 when remaining size queried (first call)
        # Return empty buffer to simulate failed read otherwise (second call)
        def simulate_failed_read(size):
            if size == 2:
                return b'\x00\x01'
            else:
                return b''

        # Mock open_connection to return True without doing anything
        # Mock websocket.read to simulate failed read
        # Mock read_resp to return bytes indicating valid signature
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', MagicMock()), \
             patch.object(node.ws, 'read', side_effect=simulate_failed_read) as mock_read, \
             patch.object(node, 'read_resp', side_effect=[0, 0]):

            # Both methods should raise OSError when empty buffer returned on second call
            with self.assertRaises(OSError):
                node.get_file("test.json", "/path/to/remote")
            self.assertEqual(mock_read.call_count, 2)
            os.remove("test.json")

            with self.assertRaises(OSError):
                node.get_file_mem("/path/to/remote")
            self.assertEqual(mock_read.call_count, 4)

    def test_put_file(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock websocket and read_resp to allow send to complete
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, 'read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Call method, confirm correct methods called
            node.put_file('node_configuration/unit-test-config.json', 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

    def test_put_file_mem(self):
        node = Webrepl('123.45.67.89', 'password')

        # Read file into variable
        with open('node_configuration/unit-test-config.json', 'r') as file:
            config = json.load(file)

        # Mock websocket and read_resp to allow send to complete
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, 'read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Send as dict, confirm correct methods called
            node.put_file_mem(config, 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

        # Should also accept string
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, 'read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Send as string
            node.put_file_mem(str(json.dumps(config)), 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

        # Should also accept bytes
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, 'read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Send as bytes
            node.put_file_mem(json.dumps(config).encode(), 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

        # Should raise error for other types
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             self.assertRaises(ValueError):

            node.put_file_mem(420, 'config.json')

    def test_login(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock methods to simulate successful login without making network connection
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(websocket, 'client_handshake', return_value=True) as mock_client_handshake, \
             patch.object(websocket, 'read', side_effect=[b":", b" "]):

            # Should login successfully due to websocket.read simulating password prompt
            self.assertTrue(node.open_connection())
            self.assertTrue(mock_client_handshake.called)

    def test_read_resp(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock open_connection to return True without doing anything
        # Mock websocket.read to simulate reading file (will only read signature bytes)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', MagicMock()), \
             patch.object(node.ws, 'read', side_effect=simulate_read_file_over_webrepl) as mock_read:

            # Call read_resp directly, confirm mock method called
            # Returning successfully indicates signature verified
            node.read_resp()
            self.assertEqual(mock_read.call_count, 1)


# Test all endpoints that require POST requests
class ConfirmRequiresPostTests(TestCase):
    def test_get_request(self):
        # All endpoints requiring POST requests
        endpoints = [
            '/upload',
            '/upload/reupload',
            '/edit_config/upload',
            '/edit_config/upload/reupload',
            '/delete_config',
            '/delete_node',
            '/check_duplicate',
            '/generate_config_file',
            '/set_default_credentials',
            '/set_default_location',
            '/restore_config'
        ]

        # Confirm correct error and status code for each endpoint
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json(), {'Error': 'Must post data'})


# Test edit config view
class EditConfigTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes and configs to edit
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_edit_config_1(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context, keys in correct order (alphabetical), correct api target menu options
        self.assertEqual(response.context['config'], test_config_1_edit_context['config'])
        self.assertEqual(list(response.context['config']['devices'].keys()), ['device1', 'device2'])
        self.assertEqual(response.context['api_target_options'], test_config_1_edit_context['api_target_options'])

        # Confirm title, heading, and edit mode
        self.assertContains(response, '<title>Editing Test1</title>')
        self.assertContains(response, '<h1 class="text-center pt-3 pb-4">Editing Test1</h1>')
        self.assertContains(response, 'const edit_existing = true;')

        # Confirm all devices and sensors present
        self.assertContains(response, '<input type="text" class="form-control sensor1 nickname" id="sensor1-nickname" placeholder="" value="Motion Sensor" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>')
        self.assertContains(response, '<input type="text" class="form-control device1 nickname" id="device1-nickname" placeholder="" value="Cabinet Lights" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>')

    def test_edit_config_2(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test2')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context + api target menu options
        self.assertEqual(response.context['config'], test_config_2_edit_context['config'])
        self.assertEqual(response.context['api_target_options'], test_config_2_edit_context['api_target_options'])

        # Confirm title, heading, and edit mode
        self.assertContains(response, '<title>Editing Test2</title>')
        self.assertContains(response, '<h1 class="text-center pt-3 pb-4">Editing Test2</h1>')
        self.assertContains(response, 'const edit_existing = true;')

        # Confirm all devices and sensors present
        self.assertContains(response, '<input type="text" class="form-control sensor1 thermostat" id="sensor1-tolerance" placeholder="" value="0.5" required>')
        self.assertContains(response, '<input class="form-check-input ir-target" type="checkbox" value="irblaster-ac" id="checkbox-ac" checked>')
        self.assertContains(response, '<option value="127.0.0.1" selected>self-target</option>')

    def test_edit_config_3(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test3')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context, keys in correct order (alphabetical), correct api target menu options
        self.assertEqual(response.context['config'], test_config_3_edit_context['config'])
        self.assertEqual(list(response.context['config']['devices'].keys()), ['device1', 'device2', 'device3'])
        self.assertEqual(list(response.context['config']['sensors'].keys()), ['sensor1', 'sensor2'])
        self.assertEqual(response.context['api_target_options'], test_config_3_edit_context['api_target_options'])

        # Confirm title, heading, and edit mode
        self.assertContains(response, '<title>Editing Test3</title>')
        self.assertContains(response, '<h1 class="text-center pt-3 pb-4">Editing Test3</h1>')
        self.assertContains(response, 'const edit_existing = true;')

        # Confirm all devices and sensors present
        self.assertContains(response, '<input type="text" class="form-control sensor1 nickname" id="sensor1-nickname" placeholder="" value="Motion Sensor (Bath)"')
        self.assertContains(response, '<input type="text" class="form-control sensor2 nickname" id="sensor2-nickname" placeholder="" value="Motion Sensor (Entry)"')
        self.assertContains(response, '<input type="text" class="form-control device1 pwm-limits" id="device1-max_bright" value="1023" required>')
        self.assertContains(response, '<input type="text" class="form-control device2 ip-input" id="device2-ip" placeholder="" value="192.168.1.239"')
        self.assertContains(response, '<input type="text" class="form-control device3 nickname" id="device3-nickname" placeholder="" value="Entry Light" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>')

    # Original bug: Did not catch DoesNotExist error, leading to traceback
    # if target config was deleted by another client before clicking edit
    def test_regression_edit_non_existing_config(self):
        # Attempt to edit non-existing node, verify error
        response = self.client.get('/edit_config/Fake')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'Error': 'Fake node not found'})


# Test config generation page
class ConfigGeneratorTests(TestCase):
    def test_new_config(self):
        # Request page, confirm correct template used
        response = self.client.get('/new_config')
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context (empty) + api target menu options + edit_existing set correctly
        self.assertEqual(response.context['config'], {"TITLE": "Create New Config"})
        self.assertEqual(response.context['api_target_options'], get_api_target_menu_options())
        self.assertContains(response, 'const edit_existing = false;')

        # Confirm wifi fields empty
        self.assertContains(response, '<h1 class="text-center pt-3 pb-4">Create New Config</h1>')
        self.assertContains(response, 'name="ssid" value="" onchange="open_toast()" required>')
        self.assertContains(response, 'name="password" value="" onchange="open_toast()" required>')

    def test_with_default_wifi(self):
        # Set default wifi credentials
        WifiCredentials.objects.create(ssid='AzureDiamond', password='hunter2')

        # Request page, confirm correct template used
        response = self.client.get('/new_config')
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm context contains credentials + edit_existing set correctly
        expected_response = {"TITLE": "Create New Config", 'wifi': {'password': 'hunter2', 'ssid': 'AzureDiamond'}}
        self.assertEqual(response.context['config'], expected_response)
        self.assertContains(response, 'const edit_existing = false;')

        # Confirm wifi fields pre-filled
        self.assertContains(response, 'name="ssid" value="AzureDiamond" onchange="open_toast()" required>')
        self.assertContains(response, 'name="password" value="hunter2" onchange="open_toast()" required>')


# Test main overview page
class OverviewPageTests(TestCase):
    def test_overview_page_no_nodes(self):
        # Request page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (empty)
        self.assertEqual(response.context['not_uploaded'], [])
        self.assertEqual(response.context['uploaded'], [])

        # Confirm neither section present
        self.assertNotContains(response, '<div id="not_uploaded" class="row section px-0 pt-2 mb-5">')
        self.assertNotContains(response, '<div id="existing" class="row section px-0 pt-2">')

    def test_overview_page_with_nodes(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (empty configs, 3 nodes)
        self.assertEqual(response.context['not_uploaded'], [])
        self.assertEqual(len(response.context['uploaded']), 3)

        # Confirm existing node section present, new config section not present
        self.assertNotContains(response, '<div id="not_uploaded" class="row section px-0 pt-2 mb-5">')
        self.assertContains(response, '<div id="existing" class="row section px-0 pt-2">')

        # Confirm table with all 3 nodes present
        self.assertContains(response, '<tr id="Test1">')
        self.assertContains(
            response,
            '<td class="align-middle"><span class="form-control keyword text-center">Test2</span></td>'
        )
        self.assertContains(response, 'onclick="window.location.href = \'/edit_config/Test3\'"')
        self.assertContains(response, 'onclick="del_node(\'Test1\')"')

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_overview_page_with_configs(self):
        # Create test config that hasn't been uploaded
        Config.objects.create(config=test_config_1, filename='test1.json')

        # Rquest page, confirm correct template used
        response = self.client.get('/config_overview')
        self.assertTemplateUsed(response, 'node_configuration/overview.html')

        # Confirm correct context (1 config, empty nodes)
        self.assertEqual(len(response.context['not_uploaded']), 1)
        self.assertEqual(response.context['uploaded'], [])

        # Confirm new config section present, existing node section section not present
        self.assertContains(response, '<div id="not_uploaded" class="row section px-0 pt-2 mb-5">')
        self.assertNotContains(response, '<div id="existing" class="row section px-0 pt-2">')

        # Confirm IP field, upload button, delete button all present
        self.assertContains(response, '<td><input type="text" id="test1.json-ip"')
        self.assertContains(response, 'id="upload-test1.json"')
        self.assertContains(response, 'onclick="del_config(\'test1.json\');"')


# Test endpoint called by reupload all option in config overview
class ReuploadAllTests(TestCase):
    def setUp(self):
        create_test_nodes()

        self.failed_to_connect = {
            'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
            'status': 404
        }

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_reupload_all(self):
        # Mock provision to return success message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {'message': 'Upload complete.', 'status': 200}

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'success': ['Test1', 'Test2', 'Test3'], 'failed': {}})
            self.assertEqual(mock_provision.call_count, 3)

    def test_reupload_all_partial_success(self):
        # Mock provision to return failure message for Test2, success for everything else
        with patch('node_configuration.views.provision', new=simulate_reupload_all_partial_success):

            # Send request, validate response, validate that test1 and test3 succeeded while test2 failed
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'success': ['Test1', 'Test3'], 'failed': {'Test2': 'Offline'}})

    def test_reupload_all_fail(self):
        # Expected response object
        all_failed = {
            "success": [],
            "failed": {
                "Test1": "Offline",
                "Test2": "Offline",
                "Test3": "Offline"
            }
        }

        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision', return_value=self.failed_to_connect) as mock_provision:

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), all_failed)
            self.assertEqual(mock_provision.call_count, 3)

    def test_reupload_all_fail_different_reasons(self):
        # Expected response object
        all_failed_different_reasons = {
            "success": [],
            "failed": {
                "Test1": "Connection timed out",
                "Test2": "Offline",
                "Test3": "Filesystem error"
            }
        }

        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision', new=simulate_reupload_all_fail_for_different_reasons):

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), all_failed_different_reasons)


# Test endpoint called by frontend upload buttons (calls get_modules and provision)
class UploadTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_upload_new_node(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            # Upload config, verify response
            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Upload complete.')

        # Should create 1 Node, no configs
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Node.objects.get(friendly_name='Test1'))

    def test_reupload_existing(self):
        # Create test config, confirm database
        create_test_nodes()
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            # Reupload config (second URL parameter), verify response
            response = self.client.post('/upload/True', {'config': 'test1.json', 'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Upload complete.')

        # Should have same number of configs and nodes
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_upload_non_existing_config(self):
        # Confirm database empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            # Reupload config (second URL parameter), verify error
            response = self.client.post('/upload', {'config': 'fake-config.json', 'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), "ERROR: Config file doesn't exist - did you delete it manually?")

        # Database should still be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_upload_to_offline_node(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Upload config, verify error
            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(),
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    def test_upload_connection_timeout(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=TimeoutError):

            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 408)
            self.assertEqual(
                response.json(),
                'Connection timed out - please press target node reset button, wait 30 seconds, and try again.'
            )

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/upload', {'ip': '123.456.678.90'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'Invalid IP 123.456.678.90'})


# Test view that uploads completed configs and dependencies to esp32 nodes
class ProvisionTests(TestCase):
    def test_provision(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', return_value=True):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 200)
            self.assertEqual(response['message'], "Upload complete.")

    def test_provision_offline_node(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 404)
            self.assertEqual(
                response['message'],
                "Error: Unable to connect to node, please make sure it is connected to wifi and try again."
            )

    def test_provision_connection_timeout(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', side_effect=TimeoutError):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 408)
            self.assertEqual(
                response['message'],
                "Connection timed out - please press target node reset button, wait 30 seconds, and try again."
            )

    def test_provision_corrupt_filesystem(self):
        modules = get_modules(test_config_1, settings.REPO_DIR)

        # Mock Webrepl.put_file to raise AssertionError for non-library files (simulate failing to upload to root dir)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file_mem', new=simulate_corrupt_filesystem_upload):

            response = provision('123.45.67.89', 'password', 'test1.json', modules)
            self.assertEqual(response['status'], 409)
            self.assertEqual(response['message'], "Failed due to filesystem error, please re-flash firmware.")


# Test view that connects to existing node, downloads config file, writes to database
class RestoreConfigViewTest(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_restore_config(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return byte-encoded test_config_1 (see unit_test_helpers.py)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(test_config_1).encode('utf-8')):

            # Post fake IP to endpoint, confirm output
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Config restored')

        # Config and Node should now exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Config.objects.get(filename='test1.json'))
        self.assertTrue(Node.objects.get(friendly_name='Test1'))

        # Config should be identical to input object
        config = Config.objects.get(filename='test1.json').config
        self.assertEqual(config, test_config_1)
        self.assertEqual(len(config['metadata']['schedule_keywords']), 2)
        self.assertIn('sunrise', config['metadata']['schedule_keywords'].keys())
        self.assertIn('sunset', config['metadata']['schedule_keywords'].keys())

    def test_target_offline(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Post fake IP to endpoint, confirm weeoe
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(),
                'Error: Unable to connect to node, please make sure it is connected to wifi and try again.'
            )

        # Database should still be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

    def test_duplicate_config_name(self):
        # Create 3 test nodes
        create_test_nodes()
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Mock Webrepl to return byte-encoded test_config_1 (duplicate, already used by create_test_nodes)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(test_config_1).encode('utf-8')):

            # Post fake IP to endpoint, confirm error
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should still have 3
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

        # Remove test configs from disk
        clean_up_test_nodes()

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/restore_config', {'ip': '123.456.678.90'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'Invalid IP 123.456.678.90'})

    # Should refuse to create in database if invalid config received
    def test_invalid_config_format(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Delete required key from config
        invalid_config = deepcopy(test_config_1)
        del invalid_config['metadata']['floor']

        # Mock Webrepl to return byte-encoded invalid config
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(invalid_config).encode('utf-8')):

            # Post fake IP to endpoint, confirm error, confirm no models created
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'})
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), 'ERROR: Config format invalid, possibly outdated version.')
            self.assertEqual(len(Config.objects.all()), 0)
            self.assertEqual(len(Node.objects.all()), 0)


# Test function that generates JSON used to populate API target set_rule menu
class ApiTargetMenuOptionsTest(TestCase):
    def test_empty_database(self):
        # Should return empty template when no Nodes exist
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}})

    def test_from_api_frontend(self):
        # Create nodes
        create_test_nodes()

        # Options that should be returned for these test nodes
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "Test1": "192.168.1.123",
                "Test2": "192.168.1.124",
                "Test3": "192.168.1.125"
            },
            "self-target": {},
            "Test1": {
                "device1-Cabinet Lights (pwm)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "device2-Overhead Lights (relay)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "sensor1-Motion Sensor (pir)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "trigger_sensor"
                ],
                "ignore": {}
            },
            "Test2": {
                "device1-Air Conditioner (api-target)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "sensor1-Thermostat (si7021)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule"
                ],
                "ir_blaster-Ir Blaster": {
                    "ac": [
                        "start",
                        "stop",
                        "off"
                    ]
                },
                "ignore": {}
            },
            "Test3": {
                "device1-Bathroom LEDs (pwm)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "device2-Bathroom Lights (relay)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "device3-Entry Light (relay)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "sensor1-Motion Sensor (Bath) (pir)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "trigger_sensor"
                ],
                "sensor2-Motion Sensor (Entry) (pir)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "trigger_sensor"
                ],
                "ignore": {}
            }
        }

        # Request options with no argument (used by Api frontend)
        options = get_api_target_menu_options()

        # Should return valid options for each device and sensor of all existing nodes
        self.assertEqual(options, expected_options)

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_from_edit_config(self):
        # Create nodes
        create_test_nodes()

        # Options that should be returned for these test nodes
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "Test2": "192.168.1.124",
                "Test3": "192.168.1.125"
            },
            "self-target": {
                "ignore": {}
            },
            "Test2": {
                "device1-Air Conditioner (api-target)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "sensor1-Thermostat (si7021)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule"
                ],
                "ir_blaster-Ir Blaster": {
                    "ac": [
                        "start",
                        "stop",
                        "off"
                    ]
                },
                "ignore": {}
            },
            "Test3": {
                "device1-Bathroom LEDs (pwm)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "device2-Bathroom Lights (relay)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "device3-Entry Light (relay)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "turn_on",
                    "turn_off"
                ],
                "sensor1-Motion Sensor (Bath) (pir)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "trigger_sensor"
                ],
                "sensor2-Motion Sensor (Entry) (pir)": [
                    "enable",
                    "disable",
                    "enable_in",
                    "disable_in",
                    "set_rule",
                    "reset_rule",
                    "trigger_sensor"
                ],
                "ignore": {}
            }
        }

        # Request options with friendly name as argument (used by edit_config)
        options = get_api_target_menu_options('Test1')

        # Should return valid options for each device and sensor of all existing nodes, except Test1
        # Should include Test1's options in self-target section, should not be in main section
        self.assertEqual(options, expected_options)

        # Remove test configs from disk
        clean_up_test_nodes()

    # Original bug: IR Blaster options always included both TV and AC, even if only one configured.
    # Fixed in 8ab9367b, now only includes available options.
    def test_regression_ir_blaster(self):
        # Base config with no IR Blaster options
        config = {
            'metadata': {
                'id': 'ir_test',
                'location': 'Bedroom',
                'floor': '2'
            },
            'wifi': {
                'ssid': 'wifi',
                'password': '1234'
            }
        }

        # IR Blaster configs with all possible combinations of targets
        no_target_config = {
            'pin': '19',
            'target': []
        }
        ac_target_config = {
            'pin': '19',
            'target': ['ac']
        }
        tv_target_config = {
            'pin': '19',
            'target': ['tv']
        }
        both_target_config = {
            'pin': '19',
            'target': ['ac', 'tv']
        }

        # No targets: All options should be removed
        config['ir_blaster'] = no_target_config
        expected_options = {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}}

        # Create, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for AC-only config
        config['ir_blaster'] = ac_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ignore": {},
                "ir_blaster-Ir Blaster": {
                    "ac": [
                        "start",
                        "stop",
                        "off"
                    ]
                }
            }
        }

        # Create AC-only config, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for TV-only config
        config['ir_blaster'] = tv_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ignore": {},
                "ir_blaster-Ir Blaster": {
                    "tv": [
                        "power",
                        "vol_up",
                        "vol_down",
                        "mute",
                        "up",
                        "down",
                        "left",
                        "right",
                        "enter",
                        "settings",
                        "exit",
                        "source"
                    ]
                }
            }
        }

        # Create TV-only config, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Correct options for config with both TV and AC, same as before bug fix
        config['ir_blaster'] = both_target_config
        expected_options = {
            "addresses": {
                "self-target": "127.0.0.1",
                "ir_test": "192.168.1.123"
            },
            "self-target": {},
            "ir_test": {
                "ignore": {},
                "ir_blaster-Ir Blaster": {
                    "tv": [
                        "power",
                        "vol_up",
                        "vol_down",
                        "mute",
                        "up",
                        "down",
                        "left",
                        "right",
                        "enter",
                        "settings",
                        "exit",
                        "source"
                    ],
                    "ac": [
                        "start",
                        "stop",
                        "off"
                    ]
                }
            }
        }

        # Create config with both TV and AC, verify options
        create_config_and_node_from_json(config)
        options = get_api_target_menu_options()
        self.assertEqual(options, expected_options)
        Node.objects.all()[0].delete()

        # Clean up
        os.remove(f"{settings.CONFIG_DIR}/ir_test.json")

    # Original bug: It was possible to set ApiTarget to turn itself on/off, resulting in
    # an infinite loop. These commands are no longer included for api-target instances
    # while self-targeting. Fixed in b8b8b0bf.
    def test_regression_self_target_infinite_loop(self):
        # Create nodes
        create_test_nodes()

        # ApiTarget options do not include turn_on or turn_off in self-target section (infinite loop)
        expected_options = {
            "device1-Air Conditioner (api-target)": [
                "enable",
                "disable",
                "enable_in",
                "disable_in",
                "set_rule",
                "reset_rule"
            ],
            "ignore": {}
        }

        # Request options for node with ApiTarget, confirm no turn_on/turn_off
        options = get_api_target_menu_options('Test2')
        self.assertEqual(options['self-target'], expected_options)

        # Remove test configs from disk
        clean_up_test_nodes()


# Test setting default wifi credentials
class WifiCredentialsTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_setting_credentials(self):
        # Database should be empty
        self.assertEqual(len(WifiCredentials.objects.all()), 0)

        # Set default credentials, verify response + database
        response = self.client.post('/set_default_credentials', {'ssid': 'AzureDiamond', 'password': 'hunter2'})
        self.assertEqual(response.json(), 'Default credentials set')
        self.assertEqual(len(WifiCredentials.objects.all()), 1)

        # Overwrite credentials, verify model only contains 1 entry
        response = self.client.post('/set_default_credentials', {'ssid': 'NewWifi', 'password': 'hunter2'})
        self.assertEqual(response.json(), 'Default credentials set')
        self.assertEqual(len(WifiCredentials.objects.all()), 1)

    def test_print_method(self):
        credentials = WifiCredentials.objects.create(ssid='testnet', password='hunter2')
        self.assertEqual(credentials.__str__(), 'testnet')


class GpsCoordinatesTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_setting_coordinates(self):
        # Database should be empty
        self.assertEqual(len(GpsCoordinates.objects.all()), 0)

        # Set default credentials, verify response + database
        response = self.client.post(
            '/set_default_location',
            {'name': 'Portland', 'lat': '45.689122409097', 'lon': '-122.63675124859863'}
        )
        self.assertEqual(response.json(), 'Location set')
        self.assertEqual(len(GpsCoordinates.objects.all()), 1)

        # Overwrite credentials, verify model only contains 1 entry
        response = self.client.post(
            '/set_default_location',
            {'name': 'Dallas', 'lat': '32.99171902655', 'lon': '-96.77213361367663'}
        )
        self.assertEqual(response.json(), 'Location set')
        self.assertEqual(len(GpsCoordinates.objects.all()), 1)

    def test_print_method(self):
        gps = GpsCoordinates.objects.create(display='Portland', lat='45.689122409097', lon='-122.63675124859863')
        self.assertEqual(gps.__str__(), 'Portland')


# Test duplicate detection
class DuplicateDetectionTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

    def test_check_duplicate(self):
        # Should accept new name
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json(), 'Name OK.')

        # Create config with same name
        self.client.post('/generate_config_file', request_payload)

        # Should now reject (identical name)
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should reject regardless of capitalization
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should accept different name
        response = self.client.post('/check_duplicate', {'name': 'Unit Test'})
        self.assertEqual(response.json(), 'Name OK.')

    # Test second conditional in is_duplicate function (unreachable when used as
    # intended, prevents issues if advanced user creates Node from shell/admin)
    def test_duplicate_friendly_name_only(self):
        # Create Node with no matching Config (avoids matching first conditional)
        Node.objects.create(friendly_name="Unit Test Config", ip="123.45.67.89", floor="0")

        # Should reject, identical friendly name exists
        response = self.client.post('/check_duplicate', {'name': 'Unit Test Config'})
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')


# Test delete config
class DeleteConfigTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config, will be deleted below
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Delete the Config created in setUp, confirm response message, confirm removed from database + disk
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Deleted unit-test-config.json')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertFalse(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

    def test_delete_non_existing_config(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 1)

        # Attempt to delete non-existing Config, confirm fails with correct message
        response = self.client.post('/delete_config', json.dumps('does-not-exist.json'))
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
        response = self.client.post('/delete_config', json.dumps('unit-test-config.json'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            'Failed to delete, permission denied. This will break other features, check your filesystem permissions.'
        )

        # Confirm Config still exists
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

        # Undo permissions
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o664)
        os.chmod(settings.CONFIG_DIR, 0o775)


class DeleteNodeTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Generate Config for test Node
        response = self.client.post('/generate_config_file', request_payload)
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
        response = self.client.post('/delete_node', json.dumps('Test Node'))
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
        response = self.client.post('/delete_node', json.dumps('Wrong Node'))
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
        response = self.client.post('/delete_node', json.dumps('Test Node'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(),
            'Failed to delete, permission denied. This will break other features, check your filesystem permissions.'
        )

        # Confirm Node and Config still exist
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))

        # Undo permissions
        os.chmod(f'{settings.CONFIG_DIR}/unit-test-config.json', 0o664)
        os.chmod(settings.CONFIG_DIR, 0o775)

    # Original bug: Impossible to delete node if config file deleted
    # from disk, traceback when file not found. Fixed in 1af01a00.
    def test_regression_delete_node_config_not_on_disk(self):
        # Delete config from disk but not database, confirm removed
        os.remove(f'{settings.CONFIG_DIR}/unit-test-config.json')
        self.assertFalse(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Delete Node, should ignore missing file on disk
        response = self.client.post('/delete_node', json.dumps('Test Node'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Deleted Test Node')
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)
        self.assertFalse(os.path.exists(f'{settings.CONFIG_DIR}/unit-test-config.json'))


# Test endpoint used to change an existing node's IP
class ChangeNodeIpTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

    def tearDown(self):
        # Remove test configs from disk
        clean_up_test_nodes()

    def test_change_node_ip(self):
        # Confirm starting IP
        self.assertEqual(Node.objects.all()[0].ip, '192.168.1.123')

        # Mock provision to return success message
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {'message': 'Upload complete.', 'status': 200}

            # Make request, confirm response
            request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.255'}
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Successfully uploaded to new IP')

            # Confirm node model IP changed, upload was called
            self.assertEqual(Node.objects.all()[0].ip, '192.168.1.255')
            self.assertEqual(mock_provision.call_count, 1)

    def test_target_ip_offline(self):
        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = {
                'message': 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.',
                'status': 404
            }

            # Make request, confirm error
            request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.255'}
            response = self.client.post('/change_node_ip', request_payload)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(
                response.json(),
                "Error: Unable to connect to node, please make sure it is connected to wifi and try again."
            )

    def test_invalid_get_request(self):
        # Requires post, confirm errors
        response = self.client.get('/change_node_ip')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

    def test_invalid_parameters(self):
        # Make request with invalid IP, confirm error
        request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.555'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'Invalid IP 192.168.1.555'})

        # Make request targeting non-existing node, confirm error
        request_payload = {'friendly_name': 'Test9', 'new_ip': '192.168.1.255'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), "Unable to change IP, node does not exist")

        # Make request with current IP, confirm error
        request_payload = {'friendly_name': 'Test1', 'new_ip': '192.168.1.123'}
        response = self.client.post('/change_node_ip', request_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'New IP must be different than old'})


# Test function that takes config file, returns list of dependencies for upload
class GetModulesTests(TestCase):
    def setUp(self):
        with open('node_configuration/unit-test-config.json') as file:
            self.config = json.load(file)

    def test_get_modules_full_config(self):

        expected_modules = {
            '../devices/ApiTarget.py': 'ApiTarget.py',
            '../devices/Wled.py': 'Wled.py',
            '../devices/Mosfet.py': 'Mosfet.py',
            '../devices/Relay.py': 'Relay.py',
            '../sensors/MotionSensor.py': 'MotionSensor.py',
            '../sensors/Dummy.py': 'Dummy.py',
            '../devices/Device.py': 'Device.py',
            '../sensors/Switch.py': 'Switch.py',
            '../sensors/Desktop_trigger.py': 'Desktop_trigger.py',
            '../devices/DumbRelay.py': 'DumbRelay.py',
            '../devices/Tplink.py': 'Tplink.py',
            '../devices/Desktop_target.py': 'Desktop_target.py',
            '../sensors/Thermostat.py': 'Thermostat.py',
            '../sensors/Sensor.py': 'Sensor.py',
            '../devices/LedStrip.py': 'LedStrip.py',
            '../devices/DimmableLight.py': 'DimmableLight.py',
            '../core/Config.py': 'Config.py',
            '../core/Group.py': 'Group.py',
            '../core/SoftwareTimer.py': 'SoftwareTimer.py',
            '../core/Api.py': 'Api.py',
            '../core/util.py': 'util.py',
            '../core/main.py': 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_empty_config(self):
        expected_modules = {
            '../core/Config.py': 'Config.py',
            '../core/Group.py': 'Group.py',
            '../core/SoftwareTimer.py': 'SoftwareTimer.py',
            '../core/Api.py': 'Api.py',
            '../core/util.py': 'util.py',
            '../core/main.py': 'main.py'
        }

        # Should only return core modules, no devices or sensors
        modules = get_modules({}, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_ir_blaster(self):
        del self.config['ir_blaster']

        expected_modules = {
            '../devices/ApiTarget.py': 'ApiTarget.py',
            '../devices/Wled.py': 'Wled.py',
            '../devices/Mosfet.py': 'Mosfet.py',
            '../devices/Relay.py': 'Relay.py',
            '../sensors/MotionSensor.py': 'MotionSensor.py',
            '../sensors/Dummy.py': 'Dummy.py',
            '../devices/Device.py': 'Device.py',
            '../sensors/Switch.py': 'Switch.py',
            '../sensors/Desktop_trigger.py': 'Desktop_trigger.py',
            '../devices/DumbRelay.py': 'DumbRelay.py',
            '../devices/Tplink.py': 'Tplink.py',
            '../devices/Desktop_target.py': 'Desktop_target.py',
            '../sensors/Thermostat.py': 'Thermostat.py',
            '../sensors/Sensor.py': 'Sensor.py',
            '../devices/LedStrip.py': 'LedStrip.py',
            '../devices/DimmableLight.py': 'DimmableLight.py',
            '../core/Config.py': 'Config.py',
            '../core/Group.py': 'Group.py',
            '../core/SoftwareTimer.py': 'SoftwareTimer.py',
            '../core/Api.py': 'Api.py',
            '../core/util.py': 'util.py',
            '../core/main.py': 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_no_thermostat(self):
        del self.config['sensor5']

        expected_modules = {
            '../devices/ApiTarget.py': 'ApiTarget.py',
            '../devices/Wled.py': 'Wled.py',
            '../devices/Mosfet.py': 'Mosfet.py',
            '../devices/Relay.py': 'Relay.py',
            '../sensors/MotionSensor.py': 'MotionSensor.py',
            '../sensors/Dummy.py': 'Dummy.py',
            '../devices/Device.py': 'Device.py',
            '../sensors/Switch.py': 'Switch.py',
            '../sensors/Desktop_trigger.py': 'Desktop_trigger.py',
            '../devices/DumbRelay.py': 'DumbRelay.py',
            '../devices/Tplink.py': 'Tplink.py',
            '../devices/Desktop_target.py': 'Desktop_target.py',
            '../sensors/Sensor.py': 'Sensor.py',
            '../devices/LedStrip.py': 'LedStrip.py',
            '../devices/DimmableLight.py': 'DimmableLight.py',
            '../core/Config.py': 'Config.py',
            '../core/Group.py': 'Group.py',
            '../core/SoftwareTimer.py': 'SoftwareTimer.py',
            '../core/Api.py': 'Api.py',
            '../core/util.py': 'util.py',
            '../core/main.py': 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)

    def test_get_modules_realistic(self):
        del self.config['ir_blaster']
        del self.config['sensor3']
        del self.config['sensor4']
        del self.config['sensor5']
        del self.config['device4']
        del self.config['device5']
        del self.config['device7']

        expected_modules = {
            '../devices/ApiTarget.py': 'ApiTarget.py',
            '../devices/Relay.py': 'Relay.py',
            '../sensors/MotionSensor.py': 'MotionSensor.py',
            '../devices/Device.py': 'Device.py',
            '../sensors/Switch.py': 'Switch.py',
            '../devices/Tplink.py': 'Tplink.py',
            '../devices/Wled.py': 'Wled.py',
            '../sensors/Sensor.py': 'Sensor.py',
            '../devices/LedStrip.py': 'LedStrip.py',
            '../devices/DimmableLight.py': 'DimmableLight.py',
            '../core/Config.py': 'Config.py',
            '../core/Group.py': 'Group.py',
            '../core/SoftwareTimer.py': 'SoftwareTimer.py',
            '../core/Api.py': 'Api.py',
            '../core/util.py': 'util.py',
            '../core/main.py': 'main.py'
        }

        modules = get_modules(self.config, settings.REPO_DIR)
        self.assertEqual(modules, expected_modules)


# Test config generator backend function
class GenerateConfigFileTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Set default GPS coordinates
        GpsCoordinates.objects.create(display='Portland', lat='45.689122409097', lon='-122.63675124859863')

    def tearDown(self):
        try:
            os.remove(f"{settings.CONFIG_DIR}/unit-test-config.json")
        except FileNotFoundError:
            pass

    def test_generate_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')

        # Confirm model was created
        self.assertEqual(len(Config.objects.all()), 1)
        config = Config.objects.all()[0]

        # Confirm output file is same as known-value config
        with open('node_configuration/unit-test-config.json') as file:
            compare = json.load(file)
            self.assertEqual(config.config, compare)

    def test_edit_existing_config_file(self):
        # Create config, confirm 1 exists in database
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(len(Config.objects.all()), 1)

        # Copy request payload, change 1 default_rule
        modified_request_payload = deepcopy(request_payload)
        modified_request_payload['device6']['default_rule'] = 900

        # Send with edit argument (overwrite existing with same name instead of throwing duplicate error)
        response = self.client.post('/generate_config_file/True', json.dumps(modified_request_payload))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')

        # Confirm same number of configs, no new config created
        self.assertEqual(len(Config.objects.all()), 1)
        config = Config.objects.all()[0]

        # Confirm new output is NOT identical to known-value config
        with open('node_configuration/unit-test-config.json') as file:
            compare = json.load(file)
            self.assertNotEqual(config.config, compare)

            # Change same default_rule, confirm was only change made
            compare['device6']['default_rule'] = 900
            self.assertEqual(config.config, compare)

    def test_duplicate_config_name(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Post frontend config generator payload to view, confirm response + model created
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')
        self.assertEqual(len(Config.objects.all()), 1)

        # Post again, should throw error (duplicate name), should not create model
        response = self.client.post('/generate_config_file', request_payload)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')
        self.assertEqual(len(Config.objects.all()), 1)

    def test_invalid_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Add invalid default rule to request payload
        invalid_request_payload = deepcopy(request_payload)
        invalid_request_payload['device6']['default_rule'] = 9001

        # Post invalid payload, confirm rejected with correct error, confirm config not created
        response = self.client.post('/generate_config_file', json.dumps(invalid_request_payload))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'Cabinet Lights: Invalid default rule 9001'})
        self.assertEqual(len(Config.objects.all()), 0)

    # Original bug: Did not catch DoesNotExist error, leading to traceback
    # if target config was deleted by another client while editing
    def test_regression_edit_non_existing_config(self):
        # Attempt to edit non-existing config file, verify error, confirm not created
        response = self.client.post('/generate_config_file/True', request_payload)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'Error': 'Config not found'})
        self.assertEqual(len(Config.objects.all()), 0)


# Test the validate_full_config function called when user submits config generator form
class ValidateConfigTests(TestCase):
    def setUp(self):
        with open('node_configuration/unit-test-config.json') as file:
            self.valid_config = json.load(file)

    def test_valid_config(self):
        result = validate_full_config(self.valid_config)
        self.assertTrue(result)

    def test_missing_keys(self):
        del self.valid_config['wifi']['ssid']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in wifi section')

        del self.valid_config['metadata']['id']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required key in metadata section')

        del self.valid_config['metadata']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Missing required top-level metadata key')

    def test_invalid_floor(self):
        self.valid_config['metadata']['floor'] = 'top'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid floor, must be integer')

    def test_duplicate_nicknames(self):
        self.valid_config['device4']['nickname'] = self.valid_config['device1']['nickname']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate nicknames')

    def test_duplicate_pins(self):
        self.valid_config['sensor2']['pin'] = self.valid_config['sensor1']['pin']
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Contains duplicate pins')

    def test_invalid_device_pin(self):
        self.valid_config['device1']['pin'] = '14'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid device pin {self.valid_config["device1"]["pin"]} used')

    def test_invalid_sensor_pin(self):
        self.valid_config['sensor1']['pin'] = '3'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid sensor pin {self.valid_config["sensor1"]["pin"]} used')

    def test_noninteger_pin(self):
        self.valid_config['sensor1']['pin'] = 'three'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid pin (non-integer)')

    def test_invalid_device_type(self):
        self.valid_config['device1']['_type'] = 'nuclear'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid device type {self.valid_config["device1"]["_type"]} used')

    def test_invalid_sensor_type(self):
        self.valid_config['sensor1']['_type'] = 'ozone-sensor'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid sensor type {self.valid_config["sensor1"]["_type"]} used')

    def test_invalid_ip(self):
        self.valid_config['device1']['ip'] = '192.168.1.500'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, f'Invalid IP {self.valid_config["device1"]["ip"]}')

    def test_thermostat_tolerance_out_of_range(self):
        self.valid_config['sensor5']['tolerance'] = 12.5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance out of range (0.1 - 10.0)')

    def test_invalid_thermostat_tolerance(self):
        self.valid_config['sensor5']['tolerance'] = 'low'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Thermostat tolerance must be int or float')

    def test_pwm_min_greater_than_max(self):
        self.valid_config['device6']['min_bright'] = 1023
        self.valid_config['device6']['max_bright'] = 500
        self.valid_config['device6']['default_rule'] = 700
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'PWM min cannot be greater than max')

    def test_pwm_limits_negative(self):
        self.valid_config['device6']['min_bright'] = -50
        self.valid_config['device6']['max_bright'] = -5
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'PWM limits cannot be less than 0')

    def test_pwm_limits_over_max(self):
        self.valid_config['device6']['min_bright'] = 1023
        self.valid_config['device6']['max_bright'] = 4096
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'PWM limits cannot be greater than 1023')

    def test_pwm_invalid_default_rule(self):
        self.valid_config['device6']['min_bright'] = 500
        self.valid_config['device6']['max_bright'] = 1000
        self.valid_config['device6']['default_rule'] = 1100
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid default rule 1100')

    def test_pwm_invalid_schedule_rule(self):
        self.valid_config['device6']['min_bright'] = 500
        self.valid_config['device6']['max_bright'] = 1000
        self.valid_config['device6']['schedule']['01:00'] = 1023
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Cabinet Lights: Invalid schedule rule 1023')

    def test_pwm_noninteger_limit(self):
        self.valid_config['device6']['min_bright'] = 'off'
        result = validate_full_config(self.valid_config)
        self.assertEqual(result, 'Invalid PWM limits, both must be int between 0 and 1023')


# Test functions in validators.py not already covered by config generation tests
class ValidatorTests(TestCase):
    def setUp(self):
        # Load valid config
        with open('node_configuration/unit-test-config.json', 'r') as file:
            self.config = json.load(file)

    def test_api_target_single_param(self):
        # Should accept all 3 single-parameter commands
        valid = self.config['device10']['default_rule']
        valid['on'] = ['ignore']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['reboot']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['clear_log']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_enable_disable(self):
        # Should accept accept enable and disable if arg is sensor or device
        valid = self.config['device10']['default_rule']
        valid['on'] = ['enable', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['disable', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_sensor_commands(self):
        # Should accept sensor-only commands if arg is sensor
        valid = self.config['device10']['default_rule']
        valid['on'] = ['trigger_sensor', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['condition_met', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        # Should reject device
        valid['on'] = ['condition_met', 'device1']
        self.assertFalse(api_target_validator(valid))

    def test_api_target_enable_in_disable_in(self):
        # Should accept accept enable and disable if args ar sensor/device and int/float
        valid = self.config['device10']['default_rule']
        valid['on'] = ['enable_in', 'sensor1', '5']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['disable_in', 'device1', '2.5']
        self.assertTrue(api_target_validator(valid))
        # Should fail with non-numeric delay
        valid['on'] = ['disable_in', 'device1', 'five minutes']
        self.assertFalse(api_target_validator(valid))

    def test_api_target_turn_on_turn_off(self):
        # Should accept turn_on/off if arg is device
        valid = self.config['device10']['default_rule']
        valid['on'] = ['turn_on', 'device1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['turn_off', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_set_rule(self):
        # Should accept set_rule if args are sensor/device and rule
        valid = self.config['device10']['default_rule']
        valid['on'] = ['set_rule', 'sensor1', '50']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['set_rule', 'device1', '50']
        self.assertTrue(api_target_validator(valid))

        # Should accept reset_rule if arg is sensor or device
        valid['on'] = ['reset_rule', 'sensor1']
        self.assertTrue(api_target_validator(valid))
        valid['on'] = ['reset_rule', 'device1']
        self.assertTrue(api_target_validator(valid))

    def test_api_target_ir_key(self):
        # Should accept valid command
        valid = self.config['device10']['default_rule']
        self.assertTrue(api_target_validator(valid))
        # Should reject unknown args
        valid['on'] = ['ir_key', 'invalid', 'invalid', 'invalid']
        self.assertFalse(api_target_validator(valid))

    def test_fade_rules(self):
        # LedStrip and Tplink should accept fade rules
        self.assertTrue(led_strip_validator('fade/50/3600', '0', '1023'))
        self.assertTrue(tplink_validator('fade/50/3600'))

        # LedStrip should reject if target out of range
        self.assertFalse(led_strip_validator('fade/50/3600', '500', '1023'))

        # Both should reject if target negative
        self.assertFalse(tplink_validator('fade/-5/3600'))
        self.assertEqual(led_strip_validator('fade/-5/3600', '-500', '1023'), 'PWM limits cannot be less than 0')

        # Both should reject if period negative
        self.assertFalse(led_strip_validator('fade/50/-500', '0', '1023'))
        self.assertFalse(tplink_validator('fade/50/-500'))

        # Both should reject if target is non-integer
        self.assertFalse(led_strip_validator('fade/max/3600', '0', '1023'))
        self.assertFalse(tplink_validator('fade/max/3600'))

    def test_motion_sensor_rules(self):
        # Should accept None (converts to 0)
        self.assertTrue(motion_sensor_validator(None))


# Confirm functions in validators.py correctly reject invalid rules
class ValidatorErrorTests(TestCase):
    def setUp(self):
        # Load valid config
        with open('node_configuration/unit-test-config.json', 'r') as file:
            self.config = json.load(file)

    def test_invalid_type(self):
        # Verify error when type is unsupported
        invalid = self.config['device1']
        invalid['_type'] = 'foobar'
        self.assertEqual(validate_rules(invalid), 'Invalid type foobar')

    def test_invalid_rule_no_special_validator(self):
        # Verify error when failed to verify default-only rule
        invalid = self.config['device5']
        invalid['default_rule'] = '50'
        self.assertEqual(validate_rules(invalid), 'Screen: Invalid default rule 50')

    def test_api_target_non_dict_rule_string(self):
        # Should reject unless rule is dict with 2 keys
        self.assertFalse(api_target_validator("string that can't convert to dict"))
        self.assertFalse(api_target_validator(50))

    def test_api_target_dict_too_long(self):
        # Should reject after adding 3rd key
        invalid = self.config['device10']
        invalid['default_rule']['value'] = '50'
        self.assertFalse(api_target_validator(invalid))

    def test_api_target_invalid_key(self):
        # Should reject keys other than on and off
        invalid = self.config['device10']['default_rule']
        invalid['new'] = invalid['on'].copy()
        del invalid['on']
        self.assertFalse(api_target_validator(invalid))

    def test_api_target_invalid_non_list_subrule(self):
        # Keys (on and off) must contain list of parameters
        invalid = self.config['device10']['default_rule']
        invalid['on'] = 42
        self.assertFalse(api_target_validator(invalid))

    def test_invalid_bool_rule(self):
        # Confirm bool is rejected for correct types
        self.assertFalse(led_strip_validator(True, '0', '1023'))
        self.assertFalse(tplink_validator(True))
        self.assertFalse(wled_validator(True))
        self.assertFalse(motion_sensor_validator(True))

    def test_invalid_out_of_range_rules(self):
        # Confirm range is enforced for correct types
        self.assertFalse(tplink_validator('-50'))
        self.assertFalse(wled_validator('-50'))
        self.assertFalse(thermostat_validator('50', 1))

    def test_invalid_noninteger_rules(self):
        # Confirm string is rejected for correct types
        self.assertFalse(wled_validator('max'))
        self.assertFalse(motion_sensor_validator('max'))
        self.assertFalse(thermostat_validator('max', 1))

    def test_invalid_keyword_rules(self):
        # Confirm wrong keywords are rejected for correct types
        self.assertFalse(dummy_validator('max'))
        self.assertFalse(dummy_validator(50))


# Test views used to manage schedule keywords from config overview
class ScheduleKeywordTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create existing keyword
        self.keyword = ScheduleKeyword.objects.create(keyword='first', timestamp='00:00')

        # Config template, new keywords should be added/removed in tests
        test_config = {
            'metadata': {
                'id': 'Test1',
                'floor': '2',
                'schedule_keywords': {
                    "sunrise": "06:00",
                    "sunset": "18:00",
                    "first": "00:00"
                }
            }
        }

        # Create nodes to upload keyword to
        self.config1, self.node1 = create_config_and_node_from_json(test_config, '123.45.67.89')
        test_config['metadata']['id'] = 'Test2'
        self.config2, self.node2 = create_config_and_node_from_json(test_config, '123.45.67.98')

        # Create mock objects to replace keyword api endpoints
        self.mock_add = MagicMock()
        self.mock_add.return_value = {"Keyword added": "morning", "time": "08:00"}
        self.mock_remove = MagicMock()
        self.mock_remove.return_value = {"Keyword added": "morning", "time": "08:00"}
        self.mock_save = MagicMock()
        self.mock_save.return_value = {"Success": "Keywords written to disk"}

    def test_str_method(self):
        # Should print keyword
        self.assertEqual(self.keyword.__str__(), 'first')

    def test_add_schedule_keyword(self):
        # Confirm starting conditions
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request, confirm response, confirm model created
            data = {'keyword': 'morning', 'timestamp': '08:00'}
            response = self.client.post('/add_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Keyword created')
            self.assertEqual(len(ScheduleKeyword.objects.all()), 4)

            # Should call add and save once for each node
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 0)
            self.assertEqual(self.mock_save.call_count, 2)

        # All configs should contain new keyword
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertEqual(self.node1.config.config['metadata']['schedule_keywords']['morning'], '08:00')
        self.assertEqual(self.config2.config['metadata']['schedule_keywords']['morning'], '08:00')

    def test_edit_schedule_keyword_timestamp(self):
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        self.assertEqual(
            self.node1.config.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )
        self.assertEqual(
            self.config2.config['metadata']['schedule_keywords'],
            {'sunrise': '06:00', 'sunset': '18:00', 'first': '00:00'}
        )

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to change timestamp only, should overwrite existing keyword
            data = {'keyword_old': 'first', 'keyword_new': 'first', 'timestamp_new': '01:00'}
            response = self.client.post('/edit_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Keyword updated')

            # Should call add and save once for each node, should not call remove
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 0)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm no model entry created, existing has new timestamp same keyword
            self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
            self.keyword.refresh_from_db()
            self.assertEqual(self.keyword.keyword, 'first')
            self.assertEqual(self.keyword.timestamp, '01:00')

        # All configs should contain new keyword
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertEqual(self.node1.config.config['metadata']['schedule_keywords']['first'], '01:00')
        self.assertEqual(self.config2.config['metadata']['schedule_keywords']['first'], '01:00')

    def test_edit_schedule_keyword_keyword(self):
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to change keyword, should remove and replace existing keyword
            data = {'keyword_old': 'first', 'keyword_new': 'second', 'timestamp_new': '08:00'}
            response = self.client.post('/edit_schedule_keyword', data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Keyword updated')

            # Should call add, remove, and save once for each node
            self.assertEqual(self.mock_add.call_count, 2)
            self.assertEqual(self.mock_remove.call_count, 2)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm same number of model entries, existing has new timestamp same keyword
            self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
            self.keyword.refresh_from_db()
            self.assertEqual(self.keyword.keyword, 'second')
            self.assertEqual(self.keyword.timestamp, '08:00')

        # Keyword should update on all existing configs
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertNotIn('first', self.node1.config.config['metadata']['schedule_keywords'].keys())
        self.assertNotIn('first', self.config2.config['metadata']['schedule_keywords'].keys())
        self.assertEqual(self.node1.config.config['metadata']['schedule_keywords']['second'], '08:00')
        self.assertEqual(self.config2.config['metadata']['schedule_keywords']['second'], '08:00')

    def test_delete_schedule_keyword(self):
        # Confirm starting condition
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

        # Mock all keyword endpoints, prevent failed network requests
        with patch('node_configuration.views.add_schedule_keyword', side_effect=self.mock_add), \
             patch('node_configuration.views.remove_schedule_keyword', side_effect=self.mock_remove), \
             patch('node_configuration.views.save_schedule_keywords', side_effect=self.mock_save):

            # Send request to delete keyword, verify response
            response = self.client.post('/delete_schedule_keyword', {'keyword': 'first'})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Keyword deleted')

            # Should call remove and save once for each node, should not call add
            self.assertEqual(self.mock_add.call_count, 0)
            self.assertEqual(self.mock_remove.call_count, 2)
            self.assertEqual(self.mock_save.call_count, 2)

            # Confirm model deleted
            self.assertEqual(len(ScheduleKeyword.objects.all()), 2)

        # Should be removed from all existing configs
        self.node1.refresh_from_db()
        self.config2.refresh_from_db()
        self.assertNotIn('first', self.node1.config.config['metadata']['schedule_keywords'].keys())
        self.assertNotIn('first', self.config2.config['metadata']['schedule_keywords'].keys())


# Confirm schedule keyword management endpoints raise correct errors
class ScheduleKeywordErrorTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create existing keyword
        self.keyword = ScheduleKeyword.objects.create(keyword='first', timestamp='00:00')

    def test_add_invalid_timestamp(self):
        # Send request, confirm error, confirm no model created
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        data = {'keyword': 'morning', 'timestamp': '8:00'}
        response = self.client.post('/add_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "{'timestamp': ['Timestamp format must be HH:MM (no AM/PM).']}")
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

    def test_add_duplicate_keyword(self):
        # Send request, confirm error, confirm no model created
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)
        data = {'keyword': 'sunrise', 'timestamp': '08:00'}
        response = self.client.post('/add_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "{'keyword': ['Schedule keyword with this Keyword already exists.']}")
        self.assertEqual(len(ScheduleKeyword.objects.all()), 3)

    def test_edit_invalid_timestamp(self):
        # Send request, confirm error
        data = {'keyword_old': 'first', 'keyword_new': 'second', 'timestamp_new': '8:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "{'timestamp': ['Timestamp format must be HH:MM (no AM/PM).']}")

    def test_edit_duplicate_keyword(self):
        # Send request, confirm error
        data = {'keyword_old': 'first', 'keyword_new': 'sunrise', 'timestamp_new': '08:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "{'keyword': ['Schedule keyword with this Keyword already exists.']}")

    def test_edit_non_existing_keyword(self):
        # Send request to edit keyword, verify error
        data = {'keyword_old': 'fake', 'keyword_new': 'second', 'timestamp_new': '8:00'}
        response = self.client.post('/edit_schedule_keyword', data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'Error': 'Keyword not found'})

    def test_delete_non_existing_keyword(self):
        # Send request to delete keyword, verify error
        response = self.client.post('/delete_schedule_keyword', {'keyword': 'fake'})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {'Error': 'Keyword not found'})

    # Should not be able to delete sunrise or sunset
    def test_delete_required_keyword(self):
        # Send request to delete keyword, verify error
        response = self.client.post('/delete_schedule_keyword', {'keyword': 'sunrise'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "sunrise is required and cannot be deleted")

        response = self.client.post('/delete_schedule_keyword', {'keyword': 'sunset'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "sunset is required and cannot be deleted")

    def test_invalid_get_request(self):
        # All keyword endpoints require post, confirm errors
        response = self.client.get('/add_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

        response = self.client.get('/edit_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})

        response = self.client.get('/delete_schedule_keyword')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json(), {'Error': 'Must post data'})
