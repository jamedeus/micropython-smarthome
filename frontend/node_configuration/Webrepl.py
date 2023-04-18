from __future__ import print_function
import sys
import os
import struct
import socket
import binascii
import hashlib
import io

# TODO Attribute? Arg?
SANDBOX = ""

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
        l = len(data)
        if l < 126:
            hdr = struct.pack(">BB", 0x82, l)
        else:
            hdr = struct.pack(">BBH", 0x82, 126, l)
        self.s.send(hdr)
        self.s.send(data)

    def recvexactly(self, sz):
        res = b""
        while sz:
            data = self.s.recv(sz)
            if not data:
                break
            res += data
            sz -= len(data)
        return res

    def read(self, size, text_ok=False):
        if not self.buf:
            while True:
                hdr = self.recvexactly(2)
                assert len(hdr) == 2
                fl, sz = struct.unpack(">BB", hdr)
                if sz == 126:
                    hdr = self.recvexactly(2)
                    assert len(hdr) == 2
                    (sz,) = struct.unpack(">H", hdr)
                if fl == 0x82:
                    break
                if text_ok and fl == 0x81:
                    break
                while sz:
                    skip = self.s.recv(sz)
                    sz -= len(skip)
            data = self.recvexactly(sz)
            assert len(data) == sz
            self.buf = data

        d = self.buf[:size]
        self.buf = self.buf[size:]
        assert len(d) == size, len(d)
        return d

    # Minimal client handshake for MicroPython, may not comply with standards
    def client_handshake(self):
        cl = self.s.makefile("rwb", 0)
        cl.write(handshake_message)
        l = cl.readline()
        while 1:
            l = cl.readline()
            if l == b"\r\n":
                break


# Helper class to simplify connections
class Webrepl():
    def __init__(self, ip, password="password"):
        self.ip = ip
        self.password = password
        self.ws = None


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

        src_fname = (SANDBOX + remote_file).encode("utf-8")
        rec = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(src_fname), src_fname)
        self.ws.write(rec)
        assert self.read_resp() == 0
        with open(local_file, "wb") as f:
            cnt = 0
            while True:
                self.ws.write(b"\0")
                (sz,) = struct.unpack("<H", self.ws.read(2))
                if sz == 0:
                    break
                while sz:
                    buf = self.ws.read(sz)
                    if not buf:
                        raise OSError()
                    cnt += len(buf)
                    f.write(buf)
                    sz -= len(buf)
                    sys.stdout.write("Received %d bytes\r" % cnt)
                    sys.stdout.flush()
        print()
        assert self.read_resp() == 0


    def get_file_mem(self, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        src_fname = (SANDBOX + remote_file).encode("utf-8")
        rec = struct.pack("<2sBBQLH64s", b"WA", 2, 0, 0, 0, len(src_fname), src_fname)
        self.ws.write(rec)
        assert self.read_resp() == 0

        output = io.BytesIO()

        cnt = 0
        while True:
            self.ws.write(b"\0")
            (sz,) = struct.unpack("<H", self.ws.read(2))
            if sz == 0:
                break
            while sz:
                buf = self.ws.read(sz)
                if not buf:
                    raise OSError()
                cnt += len(buf)
                output.write(buf)
                sz -= len(buf)
                sys.stdout.write("Received %d bytes\r" % cnt)
                sys.stdout.flush()

        print()
        assert self.read_resp() == 0

        return output.getvalue()

    def put_file(self, local_file, remote_file):
        if self.ws is None:
            if not self.open_connection():
                raise OSError

        sz = os.stat(local_file)[6]
        dest_fname = (SANDBOX + remote_file).encode("utf-8")
        rec = struct.pack("<2sBBQLH64s", b"WA", 1, 0, 0, sz, len(dest_fname), dest_fname)
        self.ws.write(rec[:10])
        self.ws.write(rec[10:])
        assert self.read_resp() == 0
        cnt = 0
        with open(local_file, "rb") as f:
            while True:
                sys.stdout.write("Sent %d of %d bytes\r" % (cnt, sz))
                sys.stdout.flush()
                buf = f.read(1024)
                if not buf:
                    break
                self.ws.write(buf)
                cnt += len(buf)
        print()
        assert self.read_resp() == 0
