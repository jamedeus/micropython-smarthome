from django.test import TestCase, Client
from django.conf import settings
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import json, os, socket
from .views import validateConfig, get_modules, get_api_target_menu_options, provision, get_api_target_menu_options
from .models import Config, Node, WifiCredentials
from unittest.mock import patch, MagicMock
from copy import deepcopy

# Large JSON objects, helper functions
from .unit_test_helpers import request_payload, create_test_nodes, clean_up_test_nodes, test_config_1, test_config_2, simulate_first_time_upload, simulate_reupload_all_partial_success, create_config_and_node_from_json, test_config_1_edit_context, test_config_2_edit_context, test_config_3_edit_context, simulate_corrupt_filesystem_upload, simulate_reupload_all_fail_for_different_reasons, binary_unit_test_config, simulate_read_file_over_webrepl, simulated_read_position
from .Webrepl import websocket, Webrepl, handshake_message



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
            node = Node.objects.create()

        # Should refuse to create with invalid IP
        with self.assertRaises(ValidationError):
            node = Node.objects.create(friendly_name='Unit Test Node', ip='123.456.789.10')

        # Should refuse to create negative floor
        with self.assertRaises(ValidationError):
            node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='-5')

        # Should refuse to create floor over 999
        with self.assertRaises(ValidationError):
            node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='9999')

        # Should refuse to create non-int floor
        with self.assertRaises(ValidationError):
            node = Node.objects.create(friendly_name='Unit Test Node', ip='123.45.67.89', floor='upstairs')

        # Should refuse to create with friendly name >50 characters
        with self.assertRaises(ValidationError):
            Config.objects.create(config=test_config_1, filename='Very Unrealistically Long Friendly Name That Nobody Needs')

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
            Config.objects.create(config=test_config_1, filename='very-unrealistically-long-config-name-that-nobody-needs.json')

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
            # Second call: return sz=15 (bytes to iterate in inner while sz loop, mock recv to return 5 bytes, evenly divisible with 15)
            # Third call: return sz=16, fl=0x82 (trigger break in second if statement)
            # Fourth call: return 16 characters to final recvexactly statement in function
            with patch.object(websocket, 'recvexactly', side_effect=[b'\x81\x7E', b'\x00\x0F', b'\x82\x10', b'abcdefghijklmnop']), \
                patch.object(mock_socket, 'recv', return_value=b'abcde'):

                # Read 16 bytes, confirm expected response
                data = ws.read(16)
                self.assertEqual(data, b'abcdefghijklmnop')

    def test_client_handshake_method(self):
        # Mock object to replace socket.makefile.write
        mock_cl = MagicMock()
        mock_cl.write = MagicMock()
        mock_cl.readline =  MagicMock(side_effect=[b'HTTP/1.1 101 Switching Protocols\r\n', b'Upgrade: websocket\r\n', b'Connection: Upgrade\r\n', b'\r\n'])

        # Mock socket to do nothing, mock makefile method to return object created above
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(mock_socket, 'makefile', return_value = mock_cl):

            # Instantiate, verify correct methods called
            ws = websocket(mock_socket)
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
             patch.object(node.ws, 'read', side_effect = simulate_failed_read) as mock_read, \
             patch.object(node, 'read_resp', side_effect=[0, 0]):

            # Both methods should raise OSError when empty buffer returned on second call
            with self.assertRaises(OSError):
                node.get_file("test.json", "/path/to/remote")
                self.assertEqual(mock_read.call_count, 2)
                os.remove("test.json")

            with self.assertRaises(OSError):
                node.get_file_mem("/path/to/remote")
                self.assertEqual(mock_read.call_count, 2)

    def test_put_file(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock websocket and read_resp to allow send to complete
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, 'read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Call method, confirm correct methods called
            node.put_file('node_configuration/unit-test-config.json', 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

    def test_login(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock methods to simulate successful login without making network connection
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(websocket, 'client_handshake', return_value=True) as mock_client_handshake, \
             patch.object(websocket, 'read', side_effect = [b":", b" "]):

            # Should login successfully due websocket.read simulating password prompt
            self.assertTrue(node.open_connection())

    def test_read_resp(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock open_connection to return True without doing anything
        # Mock websocket.read to simulate reading file (will only read signature bytes)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', MagicMock()), \
             patch.object(node.ws, 'read', side_effect = simulate_read_file_over_webrepl) as mock_read:

            # Call read_resp directly, confirm mock method called
            # Returning successfully indicates signature verified
            node.read_resp()
            self.assertEqual(mock_read.call_count, 1)




# Test all endpoints that require POST requests
class ConfirmRequiresPostTests(TestCase):
    def test_get_request(self):
        # All endpoints requiring POST requests
        endpoints = ['/setup', '/new_config/setup', '/edit_config/setup', '/upload', '/upload/reupload', '/edit_config/upload', '/edit_config/upload/reupload', '/delete_config', '/delete_node', '/check_duplicate', '/generateConfigFile', '/set_default_credentials', '/restore_config']

        # Confirm correct error and status code for each endpoint
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, 405)
            self.assertEqual(response.json(), {'Error': 'Must post data'})


# Test edit config view
class EditConfigTests(TestCase):
    def setUp(self):
        # Create 3 test nodes and configs to edit
        create_test_nodes()

    def test_edit_config_1(self):
        # Request page, confirm correct template used
        response = self.client.get('/edit_config/Test1')
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context + api target menu options
        self.assertEqual(response.context['config'], test_config_1_edit_context['config'])
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
        self.assertTemplateUsed(response, 'node_configuration/edit-config.html')

        # Confirm correct context + api target menu options
        self.assertEqual(response.context['config'], test_config_3_edit_context['config'])
        self.assertEqual(response.context['api_target_options'], test_config_3_edit_context['api_target_options'])

        # Confirm title, heading, and edit mode
        self.assertContains(response, '<title>Editing Test3</title>')
        self.assertContains(response, '<h1 class="text-center pt-3 pb-4">Editing Test3</h1>')
        self.assertContains(response, 'const edit_existing = true;')

        # Confirm all devices and sensors present
        self.assertContains(response, '<input type="text" class="form-control sensor1 nickname" id="sensor1-nickname" placeholder="" value="Motion Sensor (Bath)"')
        self.assertContains(response, '<input type="text" class="form-control sensor2 nickname" id="sensor2-nickname" placeholder="" value="Motion Sensor (Entry)"')
        self.assertContains(response, '<input type="text" class="form-control device1 pwm-limits" id="device1-max" placeholder="1023" value="1023" required>')
        self.assertContains(response, '<input type="text" class="form-control device2 ip-input" id="device2-ip" placeholder="" value="192.168.1.239"')
        self.assertContains(response, '<input type="text" class="form-control device3 nickname" id="device3-nickname" placeholder="" value="Entry Light" onchange="update_nickname(this)" oninput="prevent_duplicate_nickname(event)" required>')

    # Verify setup can be reached from suburl, used when upload fails due to missing /lib on target node
    def test_setup(self):
        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            response = self.client.post('/edit_config/setup', {'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Upload complete.')



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
        self.assertEqual(response.context['config'], {"TITLE": "Create New Config", 'wifi': {'password': 'hunter2', 'ssid': 'AzureDiamond'}})
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
        self.assertNotContains(response, '<div id="not_uploaded" class="row mx-3 mb-5">')
        self.assertNotContains(response, '<div id="existing" class="row mx-3">')

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
        self.assertNotContains(response, '<div id="not_uploaded" class="row mx-3 mb-5">')
        self.assertContains(response, '<div id="existing"')

        # Confirm table with all 3 nodes present
        self.assertContains(response, '<tr id="Test1">')
        self.assertContains(response, '<td class="align-middle">Test2</td>')
        self.assertContains(response, 'onclick="window.location.href = \'/edit_config/Test3\'"')
        self.assertContains(response, 'onclick="del_node(\'Test1\')"')

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
        self.assertContains(response, '<div id="not_uploaded" class="row mx-3 mb-5">')
        self.assertNotContains(response, '<div id="existing"')

        # Confirm IP field, upload button, delete button all present
        self.assertContains(response, '<td><input type="text" id="test1.json-ip"')
        self.assertContains(response, 'id="upload-test1.json"')
        self.assertContains(response, 'onclick="del_config(\'test1.json\');"')



# Test endpoint called by reupload all option in config overview
class ReuploadAllTests(TestCase):
    def setUp(self):
        create_test_nodes()

    def test_reupload_all(self):
        # Mock provision to return success message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = JsonResponse("Upload complete.", safe=False, status=200)

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
        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision') as mock_provision:
            mock_provision.return_value = JsonResponse("Error: Unable to connect to node, please make sure it is connected to wifi and try again.", safe=False, status=404)

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'success': [], 'failed': {'Test1': 'Offline', 'Test2': 'Offline', 'Test3': 'Offline'}})
            self.assertEqual(mock_provision.call_count, 3)

    def test_reupload_all_fail_different_reasons(self):
        # Mock provision to return failure message without doing anything
        with patch('node_configuration.views.provision', new=simulate_reupload_all_fail_for_different_reasons):

            # Send request, validate response, validate that provision is called exactly 3 times
            response = self.client.get('/reupload_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'success': [], 'failed': {'Test1': 'Connection timed out', 'Test2': 'Offline', 'Test3': 'Requires setup'}})



# Test endpoint that uploads first-time setup script
class SetupTests(TestCase):
    # Verify response in a normal scenario
    # Testing errors is redundant, it just returns the output of provision (already tested)
    def test_setup(self):
        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            response = self.client.post('/setup', {'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Upload complete.')

    # Verify the provision function is called with correct arguments
    def test_function_call(self):
        # Mock provision to return expected output without doing anything
        with patch('node_configuration.views.provision') as mock_provision:

            mock_provision.return_value = JsonResponse("Upload complete.", safe=False, status=200)
            response = self.client.post('/setup', {'ip': '123.45.67.89'}, content_type='application/json')
            mock_provision.assert_called_with("setup.json", '123.45.67.89', {}, {})

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/setup', {'ip': '123.456.678.90'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': f'Invalid IP 123.456.678.90'})



# Test endpoint called by frontend upload buttons (calls get_modules and provision)
class UploadTests(TestCase):
    def test_upload_new_node(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            # Upload config, verify response
            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'}, content_type='application/json')
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
             patch.object(Webrepl, 'put_file', return_value=True):

            # Reupload config (second URL parameter), verify response
            response = self.client.post('/upload/True', {'config': 'test1.json', 'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Upload complete.')

        # Should have same number of configs and nodes
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

    def test_upload_non_existing_config(self):
        # Confirm database empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            # Reupload config (second URL parameter), verify error
            response = self.client.post('/upload', {'config': 'fake-config.json', 'ip': '123.45.67.89'}, content_type='application/json')
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
            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.')

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
             patch.object(Webrepl, 'put_file', side_effect=TimeoutError):

            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 408)
            self.assertEqual(response.json(), 'Connection timed out - please press target node reset button, wait 30 seconds, and try again.')

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    def test_upload_first_time_setup(self):
        # Create test config, confirm database
        Config.objects.create(config=test_config_1, filename='test1.json')
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl.put_file to raise AssertionError (raised when uploading to non-existing path)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', new=simulate_first_time_upload):

            response = self.client.post('/upload', {'config': 'test1.json', 'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json(), 'ERROR: Unable to upload libraries, /lib/ does not exist. This is normal for new nodes - would you like to upload setup to fix?')

        # Should not create Node or Config
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 0)
        with self.assertRaises(Node.DoesNotExist):
            Node.objects.get(friendly_name='Test1')

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/upload', {'ip': '123.456.678.90'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': f'Invalid IP 123.456.678.90'})



# Test view that uploads completed configs and dependencies to esp32 nodes
class ProvisionTests(TestCase):
    def test_provision(self):
        modules, libs = get_modules(test_config_1)

        # Mock Webrepl to return True without doing anything
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', return_value=True):

            response = provision('test1.json', '123.45.67.89', modules, libs)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), '"Upload complete."')

    def test_provision_offline_node(self):
        modules, libs = get_modules(test_config_1)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            response = provision('test1.json', '123.45.67.89', modules, libs)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content.decode(), '"Error: Unable to connect to node, please make sure it is connected to wifi and try again."')

    def test_provision_connection_timeout(self):
        modules, libs = get_modules(test_config_1)

        # Mock Webrepl.put_file to raise TimeoutError
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', side_effect=TimeoutError):

            response = provision('test1.json', '123.45.67.89', modules, libs)
            self.assertEqual(response.status_code, 408)
            self.assertEqual(response.content.decode(), '"Connection timed out - please press target node reset button, wait 30 seconds, and try again."')

    def test_provision_first_time_setup(self):
        modules, libs = get_modules(test_config_1)

        # Mock Webrepl.put_file to raise AssertionError for files starting with "/lib/" (simulate uploading to non-existing path)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', new=simulate_first_time_upload):

            response = provision('test1.json', '123.45.67.89', modules, libs)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.content.decode(), '"ERROR: Unable to upload libraries, /lib/ does not exist. This is normal for new nodes - would you like to upload setup to fix?"')

    def test_provision_corrupt_filesystem(self):
        modules, libs = get_modules(test_config_1)

        # Mock Webrepl.put_file to raise AssertionError for non-library files (simulate failing to upload to root dir)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'put_file', new=simulate_corrupt_filesystem_upload):

            response = provision('test1.json', '123.45.67.89', modules, libs)
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.content.decode(), '"ERROR: Upload failed due to filesystem problem, please re-flash node."')



# Test view that connects to existing node, downloads config file, writes to database
class RestoreConfigViewTest(TestCase):
    def test_restore_config(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to return byte-encoded test_config_1 (see unit_test_helpers.py)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(Webrepl, 'get_file_mem', return_value=json.dumps(test_config_1).encode('utf-8')):

            # Post fake IP to endpoint, confirm output
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), 'Config restored')

        # Config and Node should now exist, should be able to find with test_config_1
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)
        self.assertTrue(Config.objects.get(config=test_config_1))
        self.assertTrue(Node.objects.get(friendly_name='Test1'))

    def test_target_offline(self):
        # Database should be empty
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Mock Webrepl to fail to connect
        with patch.object(Webrepl, 'open_connection', return_value=False):

            # Post fake IP to endpoint, confirm weeoe
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.json(), 'Error: Unable to connect to node, please make sure it is connected to wifi and try again.')

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
            response = self.client.post('/restore_config', {'ip': '123.45.67.89'}, content_type='application/json')
            self.assertEqual(response.status_code, 409)
            self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should still have 3
        self.assertEqual(len(Config.objects.all()), 3)
        self.assertEqual(len(Node.objects.all()), 3)

    # Verify correct error when passed an invalid IP
    def test_invalid_ip(self):
        response = self.client.post('/restore_config', {'ip': '123.456.678.90'}, content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': f'Invalid IP 123.456.678.90'})



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
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'Test1': '192.168.1.123', 'Test2': '192.168.1.124', 'Test3': '192.168.1.125'}, 'self-target': {}, 'Test1': {'device1-Cabinet Lights (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'device2-Overhead Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']}, 'Test2': {'device1-Air Conditioner (api-target)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'sensor1-Thermostat (si7021)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule'], 'ir_blaster-Ir Blaster': {'ac': ['start', 'stop', 'off']}}, 'Test3': {'device1-Bathroom LEDs (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'device2-Bathroom Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'device3-Entry Light (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (Bath) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor'], 'sensor2-Motion Sensor (Entry) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']}})

        # Remove test configs from disk
        clean_up_test_nodes()

    def test_from_edit_config(self):
        # Create nodes
        create_test_nodes()

        # Request options with friendly name as argument (used by edit_config)
        options = get_api_target_menu_options('Test1')

        # Should return valid options for each device and sensor of all existing nodes, except Test1
        # Should include Test1's options in self-target section, should not be in main section
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'Test2': '192.168.1.124', 'Test3': '192.168.1.125'}, 'self-target': {}, 'Test2': {'device1-Air Conditioner (api-target)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'sensor1-Thermostat (si7021)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule'], 'ir_blaster-Ir Blaster': {'ac': ['start', 'stop', 'off']}}, 'Test3': {'device1-Bathroom LEDs (pwm)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'device2-Bathroom Lights (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'device3-Entry Light (relay)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'turn_on', 'turn_off'], 'sensor1-Motion Sensor (Bath) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor'], 'sensor2-Motion Sensor (Entry) (pir)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule', 'trigger_sensor']}})

        # Remove test configs from disk
        clean_up_test_nodes()

    # Original bug: IR Blaster options always included both TV and AC, even if only one configured.
    # Fixed in 8ab9367b, now only includes available options.
    def test_regression_ir_blaster(self):
        # Configs with all possible combinations of ir blaster targets
        no_target_config = {'metadata': {'id': 'ir_test', 'location': 'Bedroom', 'floor': '2'}, 'wifi': {'ssid': 'wifi', 'password': '1234'}, 'ir_blaster': {'pin': '19', 'target': []}}
        ac_target_config = {'metadata': {'id': 'ir_test', 'location': 'Bedroom', 'floor': '2'}, 'wifi': {'ssid': 'wifi', 'password': '1234'}, 'ir_blaster': {'pin': '19', 'target': ['ac']}}
        tv_target_config = {'metadata': {'id': 'ir_test', 'location': 'Bedroom', 'floor': '2'}, 'wifi': {'ssid': 'wifi', 'password': '1234'}, 'ir_blaster': {'pin': '19', 'target': ['tv']}}
        both_target_config = {'metadata': {'id': 'ir_test', 'location': 'Bedroom', 'floor': '2'}, 'wifi': {'ssid': 'wifi', 'password': '1234'}, 'ir_blaster': {'pin': '19', 'target': ['ac', 'tv']}}

        # No targets: All options should be removed
        create_config_and_node_from_json(no_target_config)
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1'}, 'self-target': {}})
        Node.objects.all()[0].delete()

        # AC only: Should only include AC options
        create_config_and_node_from_json(ac_target_config)
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'ir_test': '192.168.1.123'}, 'self-target': {}, 'ir_test': {'ir_blaster-Ir Blaster': {'ac': ['start', 'stop', 'off']}}})
        Node.objects.all()[0].delete()

        # TV only: Should only include TV options
        create_config_and_node_from_json(tv_target_config)
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'ir_test': '192.168.1.123'}, 'self-target': {}, 'ir_test': {'ir_blaster-Ir Blaster': {'tv': ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source']}}})
        Node.objects.all()[0].delete()

        # Both: Should include all options, same as before bug fix
        create_config_and_node_from_json(both_target_config)
        options = get_api_target_menu_options()
        self.assertEqual(options, {'addresses': {'self-target': '127.0.0.1', 'ir_test': '192.168.1.123'}, 'self-target': {}, 'ir_test': {'ir_blaster-Ir Blaster': {'tv': ['power', 'vol_up', 'vol_down', 'mute', 'up', 'down', 'left', 'right', 'enter', 'settings', 'exit', 'source'], 'ac': ['start', 'stop', 'off']}}})
        Node.objects.all()[0].delete()

    # Original bug: It was possible to set ApiTarget to turn itself on/off, resulting in
    # an infinite loop. These commands are no longer included for api-target instances
    # while self-targeting. Fixed in b8b8b0bf.
    def test_regression_self_target_infinite_loop(self):
        # Create nodes
        create_test_nodes()

        # Request options for node with ApiTarget
        options = get_api_target_menu_options('Test2')

        # Should not include turn_on or turn_off in self-target section (infinite loop)
        self.assertEqual(options['self-target'], {'device1-Air Conditioner (api-target)': ['enable', 'disable', 'enable_in', 'disable_in', 'set_rule', 'reset_rule']})

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

    def test_print_method(self):
        credentials = WifiCredentials.objects.create(ssid='testnet', password='hunter2')
        self.assertEqual(credentials.__str__(), 'testnet')



# Test duplicate detection
class DuplicateDetectionTests(TestCase):
    def test_check_duplicate(self):
        # Should accept new name
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test Config'}), content_type='application/json')
        self.assertEqual(response.json(), 'Name OK.')

        # Create config with same name
        self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')

        # Should now reject (identical name)
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test Config'}), content_type='application/json')
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should reject regardless of capitalization
        response = self.client.post('/check_duplicate', json.dumps({'name': 'unit test config'}), content_type='application/json')
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')

        # Should accept different name
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test'}), content_type='application/json')
        self.assertEqual(response.json(), 'Name OK.')

    # Test second conditional in is_duplicate function (unreachable when used as
    # intended, prevents issues if advanced user creates Node from shell/admin)
    def test_duplicate_friendly_name_only(self):
        # Create Node with no matching Config (avoids matching first conditional)
        node = Node.objects.create(friendly_name="Unit Test Config", ip="123.45.67.89", floor="0")

        # Should reject, identical friendly name exists
        response = self.client.post('/check_duplicate', json.dumps({'name': 'Unit Test Config'}), content_type='application/json')
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')



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
        self.assertEqual(modules, {'../sensors/Sensor.py': 'Sensor.py', '../sensors/MotionSensor.py': 'MotionSensor.py', '../devices/LedStrip.py': 'LedStrip.py', '../sensors/Thermostat.py': 'Thermostat.py', '../devices/Mosfet.py': 'Mosfet.py', '../devices/Device.py': 'Device.py', '../devices/Desktop_target.py': 'Desktop_target.py', '../sensors/Dummy.py': 'Dummy.py', '../sensors/Desktop_trigger.py': 'Desktop_trigger.py', '../ir-remote/samsung-codes.json': 'samsung-codes.json', '../sensors/Switch.py': 'Switch.py', '../ir-remote/whynter-codes.json': 'whynter-codes.json', '../devices/Relay.py': 'Relay.py', '../devices/IrBlaster.py': 'IrBlaster.py', '../devices/DumbRelay.py': 'DumbRelay.py', '../devices/Wled.py': 'Wled.py', '../devices/Tplink.py': 'Tplink.py', '../devices/ApiTarget.py': 'ApiTarget.py'})
        self.assertEqual(libs, {'../lib/logging.py': 'lib/logging.py', '../lib/si7021.py': 'lib/si7021.py', '../lib/ir_tx/__init__.py': 'lib/ir_tx/__init__.py', '../lib/ir_tx/nec.py': 'lib/ir_tx/nec.py'})

    def test_get_modules_empty_config(self):
        modules, libs = get_modules({})
        self.assertEqual(modules, {})
        self.assertEqual(libs, {'../lib/logging.py': 'lib/logging.py'})

    def test_get_modules_no_ir_blaster(self):
        config = self.config.copy()
        del config['ir_blaster']
        modules, libs = get_modules(config)
        self.assertEqual(modules, {'../sensors/Sensor.py': 'Sensor.py', '../sensors/MotionSensor.py': 'MotionSensor.py', '../devices/LedStrip.py': 'LedStrip.py', '../sensors/Thermostat.py': 'Thermostat.py', '../devices/Mosfet.py': 'Mosfet.py', '../devices/Device.py': 'Device.py', '../devices/Desktop_target.py': 'Desktop_target.py', '../sensors/Dummy.py': 'Dummy.py', '../sensors/Desktop_trigger.py': 'Desktop_trigger.py', '../sensors/Switch.py': 'Switch.py', '../devices/Relay.py': 'Relay.py', '../devices/DumbRelay.py': 'DumbRelay.py', '../devices/Wled.py': 'Wled.py', '../devices/Tplink.py': 'Tplink.py', '../devices/ApiTarget.py': 'ApiTarget.py'})
        self.assertEqual(libs, {'../lib/logging.py': 'lib/logging.py', '../lib/si7021.py': 'lib/si7021.py'})

    def test_get_modules_no_thermostat(self):
        config = self.config.copy()
        del config['sensor5']
        modules, libs = get_modules(config)
        self.assertEqual(modules, {'../sensors/Sensor.py': 'Sensor.py', '../sensors/MotionSensor.py': 'MotionSensor.py', '../devices/LedStrip.py': 'LedStrip.py', '../devices/Mosfet.py': 'Mosfet.py', '../devices/Device.py': 'Device.py', '../devices/Desktop_target.py': 'Desktop_target.py', '../sensors/Dummy.py': 'Dummy.py', '../sensors/Desktop_trigger.py': 'Desktop_trigger.py', '../ir-remote/samsung-codes.json': 'samsung-codes.json', '../sensors/Switch.py': 'Switch.py', '../ir-remote/whynter-codes.json': 'whynter-codes.json', '../devices/Relay.py': 'Relay.py', '../devices/IrBlaster.py': 'IrBlaster.py', '../devices/DumbRelay.py': 'DumbRelay.py', '../devices/Wled.py': 'Wled.py', '../devices/Tplink.py': 'Tplink.py', '../devices/ApiTarget.py': 'ApiTarget.py'})
        self.assertEqual(libs, {'../lib/logging.py': 'lib/logging.py', '../lib/ir_tx/__init__.py': 'lib/ir_tx/__init__.py', '../lib/ir_tx/nec.py': 'lib/ir_tx/nec.py'})

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
        self.assertEqual(modules, {'../sensors/Sensor.py': 'Sensor.py', '../sensors/MotionSensor.py': 'MotionSensor.py', '../devices/LedStrip.py': 'LedStrip.py', '../devices/Device.py': 'Device.py', '../sensors/Switch.py': 'Switch.py', '../devices/Relay.py': 'Relay.py', '../devices/Wled.py': 'Wled.py', '../devices/Tplink.py': 'Tplink.py', '../devices/ApiTarget.py': 'ApiTarget.py'})
        self.assertEqual(libs, {'../lib/logging.py': 'lib/logging.py'})



# Test config generator backend function
class GenerateConfigFileTests(TestCase):
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

        # Confirm output file is same as known-value config
        with open('node_configuration/unit-test-config.json') as file:
            compare = json.load(file)
            self.assertEqual(config.config, compare)

    def test_edit_existing_config_file(self):
        # Create config, confirm 1 exists in database
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(len(Config.objects.all()), 1)

        # Copy request payload, change 1 default_rule
        modified_request_payload = deepcopy(request_payload)
        modified_request_payload['devices']['device6']['default_rule'] = 900

        # Send with edit argument (overwrite existing with same name instead of throwing duplicate error)
        response = self.client.post('/generateConfigFile/True', json.dumps(modified_request_payload), content_type='application/json')
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
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Config created.')
        self.assertEqual(len(Config.objects.all()), 1)

        # Post again, should throw error (duplicate name), should not create model
        response = self.client.post('/generateConfigFile', json.dumps(request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json(), 'ERROR: Config already exists with identical name.')
        self.assertEqual(len(Config.objects.all()), 1)

    def test_invalid_config_file(self):
        # Confirm starting condition
        self.assertEqual(len(Config.objects.all()), 0)

        # Add invalid default rule to request payload
        invalid_request_payload = deepcopy(request_payload)
        invalid_request_payload['devices']['device6']['default_rule'] = 9001

        # Post invalid payload, confirm rejected with correct error, confirm config not created
        response = self.client.post('/generateConfigFile', json.dumps(invalid_request_payload), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'Error': 'Cabinet Lights: Invalid default rule 9001'})
        self.assertEqual(len(Config.objects.all()), 0)



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
        self.assertEqual(result, 'Cabinet Lights: Invalid default rule 1100')

    def test_pwm_invalid_schedule_rule(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 500
        config['device6']['max'] = 1000
        config['device6']['schedule']['01:00'] = 1023
        result = validateConfig(config)
        self.assertEqual(result, 'Cabinet Lights: Invalid schedule rule 1023')

    def test_pwm_noninteger_limit(self):
        config = self.valid_config.copy()
        config['device6']['min'] = 'off'
        result = validateConfig(config)
        self.assertEqual(result, 'Invalid PWM limits, both must be int between 0 and 1023')
