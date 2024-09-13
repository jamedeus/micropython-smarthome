# pylint: disable=line-too-long, missing-function-docstring, missing-module-docstring, missing-class-docstring

import os
import json
import struct
import socket
from unittest import TestCase
from unittest.mock import patch, MagicMock
from Webrepl import Webrepl, Websocket, HANDSHAKE_MESSAGE

# Get full paths to repository root directory, CLI tools directory
cli = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
repo = os.path.split(cli)[0]

# Get absolute path to test config
test_config_path = os.path.join(repo, "util", "unit-test-config.json")

# Binary contents of test config file, used as payload in simulated Webrepl connections
with open(test_config_path, 'r', encoding='utf-8') as file:
    binary_unit_test_config = json.dumps(json.load(file)).encode()

# Used to track current position in binary_unit_test_config (read function called multiple times)
# A mutable object must be used for scope reasons, can't use int (would reset each call)
simulated_read_position = [0]


# Replaces websocket.read method in mock
# Feeds bytes from binary_unit_test_config to Webrepl.get_file and Webrepl.get_file_mem
def simulate_read_file_over_webrepl(size):
    # Client verifying signature, return expected bytes (WB00)
    if size == 4:
        return b'WB\x00\x00'

    # Client requested remaining filesize
    if size == 2:
        # Return 00 if no data left
        if simulated_read_position[0] >= len(binary_unit_test_config):
            return b'\x00\x00'

        # Otherwise return length of unread data
        remaining_size = len(binary_unit_test_config) - simulated_read_position[0]
        return struct.pack("<H", remaining_size)

    # Slice requested size starting from first un-read byte, increment counter to index of last byte in slice
    data = binary_unit_test_config[simulated_read_position[0]:simulated_read_position[0] + size]
    simulated_read_position[0] += size
    return data


# Test websocket class used by Webrepl
class WebsocketTests(TestCase):

    def test_write_method(self):
        # Mock socket and client_handshake to do nothing
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(Websocket, 'client_handshake', return_value=True):

            # Instantiate, write long string to trigger else (rest covered by Webrepl tests)
            ws = Websocket(mock_socket)
            ws.write('test string longer than the 126 characters, which is the required number of characters to trigger the else clause in websocket.write')

    def test_recvexactly_method(self):
        # Mock socket.recv to return arbitrary data, mock client_handshake to do nothing
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(mock_socket, 'recv', return_value=b"A bunch of binary data"), \
             patch.object(Websocket, 'client_handshake', return_value=True):

            # Instantiate, request data, verify response
            ws = Websocket(mock_socket)
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
             patch.object(Websocket, 'client_handshake', return_value=True):

            # Instantiate Websocket
            ws = Websocket(mock_socket)

            # First call: return sz=5, fl=0x82 (trigger break in second if statement)
            # Second call: Return Hello
            with patch.object(Websocket, 'recvexactly', side_effect=[b'\x82\x05', b'Hello']):
                # Read 5 bytes, confirm expected response
                data = ws.read(5)
                self.assertEqual(data, b'Hello')

            # First call: return sz=5, fl=0x81 (trigger last if statement in loop)
            # Second call: return World
            with patch.object(Websocket, 'recvexactly', side_effect=[b'\x81\x05', b'World']):
                # Read 5 bytes, confirm expected response
                data = ws.read(5, text_ok=True)
                self.assertEqual(data, b'World')

            # First call: return sz=126 (trigger first if statement in loop)
            # Second call: return sz=15 (bytes to iterate in inner loop, evenly divisible by 5 bytes returned by recv)
            # Third call: return sz=16, fl=0x82 (trigger break in second if statement)
            # Fourth call: return 16 characters to final recvexactly statement in function
            recvexactly_side_effect = [b'\x81\x7E', b'\x00\x0F', b'\x82\x10', b'abcdefghijklmnop']
            with patch.object(Websocket, 'recvexactly', side_effect=recvexactly_side_effect), \
                 patch.object(mock_socket, 'recv', return_value=b'abcde'):

                # Read 16 bytes, confirm expected response
                data = ws.read(16)
                self.assertEqual(data, b'abcdefghijklmnop')

            # Simulate buffer already contains data (read should return
            # existing buffer contents without reading from websocket)
            ws.buf = b'abcde'
            with patch.object(Websocket, 'recvexactly') as mock_recvexactly:
                # Read 5 bytes, confirm expected response
                data = ws.read(5)
                self.assertEqual(data, b'abcde')
                # Confirm did NOT read from websocket
                mock_recvexactly.assert_not_called()

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
            Websocket(mock_socket)
            mock_cl.write.assert_called_once_with(HANDSHAKE_MESSAGE)
            self.assertEqual(mock_cl.readline.call_count, 4)


# Test the Webrepl class used to upload config + dependencies to nodes
class WebreplTests(TestCase):

    # Path to file created by get_file method
    local_file = "test_get_file_output.json"

    # Delete files written to disk by tests
    def tearDown(self):
        try:
            os.remove(self.local_file)
        except FileNotFoundError:
            pass

    def test_open_and_close_connection(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock all methods called by open_connection + close_connection to return True
        with patch.object(socket, 'socket', return_value=MagicMock()) as mock_socket, \
             patch.object(Websocket, 'client_handshake', return_value=True) as mock_client_handshake, \
             patch.object(Webrepl, '_login', return_value=True) as mock_login:

            # Should connect successfully due to mocks
            self.assertTrue(node.open_connection())

            # Confirm correct methods called
            mock_socket.return_value.settimeout.assert_called()
            mock_socket.return_value.connect.assert_called()
            mock_client_handshake.assert_called()
            mock_login.assert_called()

            # Confirm has websocket attribute
            self.assertIsInstance(node.ws, Websocket)

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
        self.assertRaises(OSError, node._login)
        self.assertRaises(OSError, node._read_resp)

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

        # Mock Websocket.read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl

        # Set simulated read starting position to beginning of file
        simulated_read_position[0] = 0

        # Mock all methods called by open_connection
        # Mock Websocket to return the object created above
        # Mock _read_resp to return bytes indicating valid signature
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Webrepl, '_login', return_value=True), \
             patch('Webrepl.Websocket', return_value=ws_mock), \
             patch.object(node, '_read_resp', side_effect=[0, 0]):

            # Call method, should receive simulated data stream and write to disk
            node.get_file(self.local_file, "/path/to/remote")

        # Confirm expected data written
        with open(self.local_file, 'rb') as f:
            get_file_output = f.read()
            self.assertEqual(binary_unit_test_config, get_file_output)

    def test_get_file_mem(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock Websocket.read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl

        # Set simulated read starting position to beginning of file
        simulated_read_position[0] = 0

        # Mock all methods called by open_connection
        # Mock Websocket to return the object created above
        # Mock _read_resp to return bytes indicating valid signature
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Webrepl, '_login', return_value=True), \
             patch('Webrepl.Websocket', return_value=ws_mock), \
             patch.object(node, '_read_resp', side_effect=[0, 0]):

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
            return b''

        # Mock open_connection to return True without doing anything
        # Mock Websocket.read to simulate failed read
        # Mock _read_resp to return bytes indicating valid signature
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', MagicMock()), \
             patch.object(node.ws, 'read', side_effect=simulate_failed_read) as mock_read, \
             patch.object(node, '_read_resp', side_effect=[0, 0]):

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

        # Create mock Websocket object
        mock_websocket = MagicMock()

        # Mock all methods called by open_connection
        # Mock Websocket to return the object created above
        # Mock _read_resp to allow send to complete
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Webrepl, '_login', return_value=True) as mock_login, \
             patch('Webrepl.Websocket', return_value=mock_websocket), \
             patch.object(node, '_read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Call method, confirm correct methods called
            node.put_file(test_config_path, 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

            # Confirm logged in (open_connection called)
            self.assertTrue(mock_login.called)

        # Simulate connection already open when method called
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(Webrepl, '_login', return_value=True) as mock_login, \
             patch.object(node, '_read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Call method, confirm correct methods called
            node.put_file(test_config_path, 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

            # Confirm did NOT log in (connection already open)
            self.assertFalse(mock_login.called)

    def test_put_file_mem(self):
        node = Webrepl('123.45.67.89', 'password')

        # Read file into variable
        with open(test_config_path, 'r', encoding='utf-8') as file:
            config = json.load(file)

        # Create mock Websocket object
        mock_websocket = MagicMock()

        # Mock all methods called by open_connection
        # Mock Websocket to return the object created above
        # Mock _read_resp to allow send to complete
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Webrepl, '_login', return_value=True), \
             patch('Webrepl.Websocket', return_value=mock_websocket), \
             patch.object(node, '_read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Send as dict, confirm correct methods called
            node.put_file_mem(config, 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

        # Should also accept string
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, '_read_resp', side_effect=[0, 0]) as mock_read_resp:

            # Send as string
            node.put_file_mem(str(json.dumps(config)), 'config.json')
            self.assertTrue(mock_websocket.write.called)
            self.assertTrue(mock_read_resp.called)

        # Should also accept bytes
        with patch.object(node, 'ws', MagicMock()) as mock_websocket, \
             patch.object(node, '_read_resp', side_effect=[0, 0]) as mock_read_resp:

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
             patch.object(Websocket, 'client_handshake', return_value=True) as mock_client_handshake, \
             patch.object(Websocket, 'read', side_effect=[b"entry 0x400805cc", b":", b" "]):

            # Should login successfully due to Websocket.read simulating password prompt
            self.assertTrue(node.open_connection())
            self.assertTrue(mock_client_handshake.called)

    def test_read_resp(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock open_connection to return True without doing anything
        # Mock Websocket.read to simulate reading file (will only read signature bytes)
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', MagicMock()), \
             patch.object(node.ws, 'read', side_effect=simulate_read_file_over_webrepl) as mock_read:

            # Call read_resp directly, confirm mock method called
            # Returning successfully indicates signature verified
            node._read_resp()
            self.assertEqual(mock_read.call_count, 1)

    def test_connection_reset_error(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock methods to simulate successfully opening connection
        # Mock Websocket.read to simulate node closing connection early
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Websocket, 'read', side_effect=ConnectionResetError), \
             patch.object(Webrepl, '_login', return_value=True):

            # Confirm all methods print error message and raise OSError when
            # node closes connection
            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.get_file("test.json", "/path/to/remote")
                mock_print.assert_called_with("Error: Connection closed by 123.45.67.89")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.get_file_mem("/path/to/remote")
                mock_print.assert_called_with("Error: Connection closed by 123.45.67.89")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.put_file(test_config_path, 'config.json')
                mock_print.assert_called_with("Error: Connection closed by 123.45.67.89")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.put_file_mem({'mock': 'config'}, 'config.json')
                mock_print.assert_called_with("Error: Connection closed by 123.45.67.89")

    def test_connection_timed_out_error(self):
        node = Webrepl('123.45.67.89', 'password')

        # Mock methods to simulate successfully opening connection
        # Mock Websocket.read to simulate connection timing out
        with patch.object(socket, 'socket', return_value=MagicMock()), \
             patch.object(Websocket, 'client_handshake', return_value=True), \
             patch.object(Websocket, 'read', side_effect=TimeoutError), \
             patch.object(Webrepl, '_login', return_value=True):

            # Confirm all methods print error message and raise OSError when
            # connection times out
            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.get_file("test.json", "/path/to/remote")
                mock_print.assert_called_with("Connection timed out")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.get_file_mem("/path/to/remote")
                mock_print.assert_called_with("Connection timed out")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.put_file(test_config_path, 'config.json')
                mock_print.assert_called_with("Connection timed out")

            with self.assertRaises(OSError), \
                 patch('builtins.print') as mock_print:
                node.put_file_mem({'mock': 'config'}, 'config.json')
                mock_print.assert_called_with("Connection timed out")

    def test_quiet_arg_false(self):
        # Instantiate with quiet arg set to False
        node = Webrepl('123.45.67.89', 'password', False)

        # Mock Websocket.read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl
        simulated_read_position[0] = 0

        # Replace node.ws with the mock websocket created above
        # Mock methods used by get_* and put_* to do nothing
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', ws_mock), \
             patch.object(node, '_read_resp', return_value=0):

            # Mock print and sys.stdout.write to confirm called
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call get_file, confirm print and sys.stdout.write were called
                node.get_file(self.local_file, "/path/to/remote")
                mock_print.assert_called()
                mock_write_stdout.assert_called()

            # Repeat with get_file_mem
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Reset simulated read position, call method
                simulated_read_position[0] = 0
                node.get_file_mem("/path/to/remote")

                # Confirm print and sys.stdout.write were called
                mock_print.assert_called()
                mock_write_stdout.assert_called()

            # Repeat with put_file method
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call method, confirm print and sys.stdout.write were called
                node.put_file(test_config_path, 'config.json')
                mock_print.assert_called()
                mock_write_stdout.assert_called()

            # Repeat with put_file_mem method
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call method, confirm print and sys.stdout.write were called
                node.put_file_mem('mock_file', 'config.json')
                mock_print.assert_called()
                mock_write_stdout.assert_called()

    def test_quiet_arg_true(self):
        # Instantiate with quiet arg set to True
        node = Webrepl('123.45.67.89', 'password', True)

        # Mock Websocket.read method to return contents of unit-test-config.json
        ws_mock = MagicMock()
        ws_mock.read.side_effect = simulate_read_file_over_webrepl
        simulated_read_position[0] = 0

        # Replace node.ws with the mock websocket created above
        # Mock methods used by get_* and put_* to do nothing
        with patch.object(Webrepl, 'open_connection', return_value=True), \
             patch.object(node, 'ws', ws_mock), \
             patch.object(node, '_read_resp', return_value=0):

            # Mock print and sys.stdout.write to confirm NOT called
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call get_file, confirm print and sys.stdout.write were NOT called
                node.get_file(self.local_file, "/path/to/remote")
                mock_print.assert_not_called()
                mock_write_stdout.assert_not_called()

            # Repeat with get_file_mem
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Reset simulated read position, call method
                simulated_read_position[0] = 0
                node.get_file_mem("/path/to/remote")

                # Confirm print and sys.stdout.write were NOT called
                mock_print.assert_not_called()
                mock_write_stdout.assert_not_called()

            # Repeat with put_file method
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call method, confirm print and sys.stdout.write were NOT called
                node.put_file(test_config_path, 'config.json')
                mock_print.assert_not_called()
                mock_write_stdout.assert_not_called()

            # Repeat with put_file_mem method
            with patch('builtins.print') as mock_print, \
                 patch('Webrepl.sys.stdout.write') as mock_write_stdout:

                # Call method, confirm print and sys.stdout.write were NOT called
                node.put_file_mem('mock_file', 'config.json')
                mock_print.assert_not_called()
                mock_write_stdout.assert_not_called()
