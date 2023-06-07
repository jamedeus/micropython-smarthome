from __future__ import print_function
import sys
import os
import struct
import socket
import io
import json

handshake_message = b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
"""


# Modified from official webrepl release
class websocket:
    def __init__(self, s):
        self.s = s
        self.client_handshake()
        self.buf = b""

    def write(self, data):
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

    # Minimal client handshake for MicroPython, may not comply with standards
    def client_handshake(self):
        # Make unbuffered file-like obect
        cl = self.s.makefile("rwb", 0)
        # Send websocket upgrade request to node
        cl.write(handshake_message)

        # Read node response until end of message
        while 1:
            line = cl.readline()
            if line == b"\r\n":
                break


# Helper class to simplify connections
class Webrepl():
    def __init__(self, ip, password="password"):
        self.ip = ip
        self.password = password
        self.ws = None

    # Open socket, upgrade to websocket, login with self.password
    def open_connection(self):
        try:
            s = socket.socket()
            s.settimeout(10)
            ai = socket.getaddrinfo(self.ip, 8266)
            addr = ai[0][4]
            s.connect(addr)
            self.ws = websocket(s)
            self.login()
            return True

        except OSError:
            self.close_connection()
            print(f"Error: Unable to open connection to {self.ip}")
            return False

    def close_connection(self):
        if self.ws:
            # Close socket, remove websocket attribute
            self.ws.s.close()
            self.ws = None
        return True

    def login(self):
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

    def read_resp(self):
        if self.ws is None:
            print("ERROR: Should not be invoked directly, use open_connection()")
            raise OSError

        data = self.ws.read(4)
        sig, code = struct.unpack("<2sH", data)
        assert sig == b"WB"
        return code

    def get_file(self, local_file, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 2 (read), request size, encoded filename
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(remote_file), remote_file)

        # Send request (no response = success)
        self.ws.write(request)
        assert self.read_resp() == 0

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
                    sys.stdout.write("Received %d bytes\r" % count)
                    sys.stdout.flush()
        print()
        assert self.read_resp() == 0

    def get_file_mem(self, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 2 (read), request size, encoded filename
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(remote_file), remote_file)

        # Send request (no response = success)
        self.ws.write(request)
        assert self.read_resp() == 0

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
                sys.stdout.write("Received %d bytes\r" % count)
                sys.stdout.flush()

        print()
        assert self.read_resp() == 0

        return output.getvalue()

    def put_file(self, local_file, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Create request: webrepl protocol, operation code 1 (write), payload size, encoded filename
        sz = os.stat(local_file)[6]
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 1, 0, 0, sz, len(remote_file), remote_file)

        # Send first 10 bytes of request, then all remaining bytes (no response = success)
        self.ws.write(request[:10])
        self.ws.write(request[10:])
        assert self.read_resp() == 0

        count = 0
        with open(local_file, "rb") as source_file:
            while True:
                # Overwrite previous progress report
                sys.stdout.write("Sent %d of %d bytes\r" % (count, sz))
                sys.stdout.flush()

                # Read next chunk
                buf = source_file.read(1024)

                # End of file reached
                if not buf:
                    break

                # Send chunk
                self.ws.write(buf)
                count += len(buf)
        print()
        assert self.read_resp() == 0

    # Takes string instead of
    def put_file_mem(self, file_contents, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        # Convert input to bytes
        if type(file_contents) is str:
            file_contents = file_contents.encode()
        elif type(file_contents) is dict or type(file_contents) is list:
            file_contents = json.dumps(file_contents).encode()
        elif type(file_contents) is bytes:
            pass
        else:
            raise ValueError

        # Create request: webrepl protocol, operation code 1 (write), payload size, encoded filename
        sz = len(file_contents)
        remote_file = (remote_file).encode("utf-8")
        request = struct.pack("<2sBBQLH64s", b"WA", 1, 0, 0, sz, len(remote_file), remote_file)

        # Send first 10 bytes of request, then all remaining bytes (no response = success)
        self.ws.write(request[:10])
        self.ws.write(request[10:])
        assert self.read_resp() == 0

        count = 0
        with io.BytesIO(file_contents) as source_file:
            while True:
                # Overwrite previous progress report
                sys.stdout.write("Sent %d of %d bytes\r" % (count, sz))
                sys.stdout.flush()

                # Read next chunk
                buf = source_file.read(1024)

                # End of file reached
                if not buf:
                    break

                # Send chunk
                self.ws.write(buf)
                count += len(buf)
        print()
        assert self.read_resp() == 0
