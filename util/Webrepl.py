'''Modified from official webrepl release:
https://github.com/micropython/webrepl/blob/master/webrepl_cli.py

Webrepl class used to provision ESP32 nodes (upload config files and
dependencies to ESP32 filesystem) and to download logs from ESP32 filesystem.
'''

import io
import os
import sys
import json
import struct
import socket

HANDSHAKE_MESSAGE = b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
"""


class Websocket:
    '''Basic websocket implementation modified from official Webrepl release:
    https://github.com/micropython/webrepl/blob/master/webrepl_cli.py

    Automatically opens connection and completes handshake when instantiated.
    '''

    def __init__(self, s):
        self.s = s
        self.client_handshake()
        self.buf = b""

    def write(self, data):
        '''Sends data payload with appropriate header.'''

        # Get correct header for payload size
        size = len(data)
        if size < 126:
            hdr = struct.pack(">BB", 0x82, size)
        else:
            hdr = struct.pack(">BBH", 0x82, 126, size)

        # Send header followed by data
        self.s.send(hdr)
        self.s.send(data)

    def recvexactly(self, size):
        '''Reads the requested number of bytes directly from socket.'''

        response = b""
        while size:
            # Read requested number of bytes
            data = self.s.recv(size)

            # Reached end of data
            if not data:
                break

            # Add bytes to response, subtract from remaining length
            response += data
            size -= len(data)
        return response

    def read(self, size, text_ok=False):
        '''Reads the requested number of bytes from first websocket frame.
        Reads from binary frame by default, text frame if text_ok arg True.
        '''

        # Read until valid websocket frame found
        if not self.buf:
            while True:
                # Get frame header
                hdr = self.recvexactly(2)
                assert len(hdr) == 2

                # Get frame type, size
                fl, sz = struct.unpack(">BB", hdr)

                # Frame larger than 126 bytes: read second header, get actual size
                if sz == 126:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    (sz,) = struct.unpack(">H", hdr)

                # Binary frame found
                if fl == 0x82:
                    break

                # Text frame found
                if text_ok and fl == 0x81:
                    break

                # Invalid frame, skip
                while sz:
                    skip = self.s.recv(sz)
                    sz -= len(skip)

            # Read valid frame contents into self.buf
            data = self.recvexactly(sz)
            assert len(data) == sz
            self.buf = data

        # Parse requested number of bytes, truncate self.buf
        d = self.buf[:size]
        self.buf = self.buf[size:]
        assert len(d) == size, len(d)
        return d

    def client_handshake(self):
        '''Performs client handshake to upgrade connection to websocket.
        Minimal implementation for MicroPython, may not comply with standards.
        '''

        # Make unbuffered file-like object
        cl = self.s.makefile("rwb", 0)
        # Send websocket upgrade request to node
        cl.write(HANDSHAKE_MESSAGE)

        # Read node response until end of message
        while 1:
            line = cl.readline()
            if line == b"\r\n":
                break


class Webrepl():
    '''Webrepl helper class used to simplify connections to ESP32 nodes.

    Takes ESP32 IP, webrepl password (default=password), and optional quiet arg
    (silences all console output except errors if True, defaults to False).

    Contains methods to open and close connections, read and write files, etc.
    '''

    def __init__(self, ip, password="password", quiet=False):
        self.ip = ip
        self.password = password
        self.ws = None
        self.quiet = quiet

    def open_connection(self):
        '''Open socket, upgrade to websocket, login with self.password'''
        try:
            s = socket.socket()
            s.settimeout(10)
            ai = socket.getaddrinfo(self.ip, 8266)
            addr = ai[0][4]
            s.connect(addr)
            self.ws = Websocket(s)
            self._login()
            return True

        except OSError:
            self.close_connection()
            print(f"Error: Unable to open connection to {self.ip}")
            return False

    def close_connection(self):
        '''Closes underlying socket and deletes Websocket instance reference'''
        if self.ws:
            # Close socket, remove websocket attribute
            self.ws.s.close()
            self.ws = None
        return True

    def _login(self):
        '''Reads until password prompt detected, enters password'''
        if self.ws is None:
            print("ERROR: Should not be invoked directly, use open_connection()")
            raise OSError

        # Read until the password prompt (semicolon followed by space), send password
        while True:
            c = self.ws.read(1, text_ok=True)
            if c == b":":
                assert self.ws.read(1, text_ok=True) == b" "
                break
        self.ws.write(self.password.encode("utf-8") + b"\r")

    def _read_resp(self):
        '''Reads response code (called after writing to websocket)'''
        if self.ws is None:
            print("ERROR: Should not be invoked directly, use get_file or put_file methods")
            raise OSError

        data = self.ws.read(4)
        sig, code = struct.unpack("<2sH", data)
        assert sig == b"WB"
        return code

    def get_file(self, local_file, remote_file):
        '''Downloads a file from ESP32 filesystem, writes to local filesystem.
        Takes local filesystem output path, ESP32 filesystem path to download.
        '''
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 2 (read), request
        # size, encoded filename
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(remote_file), remote_file)

        # Send request (no response = success)
        self.ws.write(request)
        assert self._read_resp() == 0

        with open(local_file, "wb") as output_file:
            count = 0
            while True:
                # Request chunk, parse size
                self.ws.write(b"\0")
                (sz,) = struct.unpack("<H", self.ws.read(2))

                # End of file reached
                if sz == 0:
                    break

                # Read bytes into buffer, write to output file
                while sz:
                    buf = self.ws.read(sz)
                    if not buf:
                        raise OSError()
                    count += len(buf)
                    output_file.write(buf)
                    sz -= len(buf)

                    # Overwrite previous progress report
                    if not self.quiet:
                        sys.stdout.write(f"Received {count} bytes\r")
                        sys.stdout.flush()

        if not self.quiet:
            print()
        assert self._read_resp() == 0

    def get_file_mem(self, remote_file):
        '''Downloads a file from ESP32 filesystem, returns as string.'''

        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 2 (read), request size, encoded filename
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(remote_file), remote_file)

        # Send request (no response = success)
        self.ws.write(request)
        assert self._read_resp() == 0

        # Create buffer for received file
        output = io.BytesIO()

        count = 0
        while True:
            # Request chunk, parse size
            self.ws.write(b"\0")
            (sz,) = struct.unpack("<H", self.ws.read(2))

            # End of file reached
            if sz == 0:
                break

            # Read bytes into buffer, write to output buffer
            while sz:
                buf = self.ws.read(sz)
                if not buf:
                    raise OSError()
                count += len(buf)
                output.write(buf)
                sz -= len(buf)

                # Overwrite previous progress report
                if not self.quiet:
                    sys.stdout.write(f"Received {count} bytes\r")
                    sys.stdout.flush()

        if not self.quiet:
            print()
        assert self._read_resp() == 0

        return output.getvalue()

    def put_file(self, local_file, remote_file):
        '''Uploads file from local filesystem to ESP32 filesystem.
        Takes local filepath, ESP32 filesystem destination path.
        '''
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 1 (write), payload size, encoded filename
        sz = os.stat(local_file)[6]
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 1, 0, 0, sz, len(remote_file), remote_file)

        # Print status message before sending request
        if not self.quiet:
            print(f"{local_file} -> {self.ip}:/{remote_file}")

        # Send first 10 bytes of request, then all remaining bytes (no response = success)
        self.ws.write(request[:10])
        self.ws.write(request[10:])
        assert self._read_resp() == 0

        count = 0
        with open(local_file, "rb") as source_file:
            while True:
                # Overwrite previous progress report
                if not self.quiet:
                    sys.stdout.write(f"Sent {count} of {sz} bytes\r")
                    sys.stdout.flush()

                # Read next chunk
                buf = source_file.read(1024)

                # End of file reached
                if not buf:
                    break

                # Send chunk
                self.ws.write(buf)
                count += len(buf)

        if not self.quiet:
            print('\n')
        assert self._read_resp() == 0

    # Takes string instead of
    def put_file_mem(self, file_contents, remote_file):
        '''Writes contents of variable to file on ESP32 filesystem.
        Takes variable (str, list, dict, or bytes), ESP32 filesystem path.
        '''
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Convert input to bytes
        if isinstance(file_contents, str):
            file_contents = file_contents.encode()
        elif isinstance(file_contents, (dict, list)):
            file_contents = json.dumps(file_contents).encode()
        elif isinstance(file_contents, bytes):
            pass
        else:
            raise ValueError

        # Create request: webrepl protocol, operation code 1 (write), payload size, encoded filename
        sz = len(file_contents)
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 1, 0, 0, sz, len(remote_file), remote_file)

        # Print status message before sending request
        if not self.quiet:
            print(f"{sz} bytes -> {self.ip}:/{remote_file}")

        # Send first 10 bytes of request, then all remaining bytes (no response = success)
        self.ws.write(request[:10])
        self.ws.write(request[10:])
        assert self._read_resp() == 0

        count = 0
        with io.BytesIO(file_contents) as source_file:
            while True:
                # Overwrite previous progress report
                if not self.quiet:
                    sys.stdout.write(f"Sent {count} of {sz} bytes\r")
                    sys.stdout.flush()

                # Read next chunk
                buf = source_file.read(1024)

                # End of file reached
                if not buf:
                    break

                # Send chunk
                self.ws.write(buf)
                count += len(buf)

        if not self.quiet:
            print('\n')
        assert self._read_resp() == 0
