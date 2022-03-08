#!/usr/bin/env python

# Upload config file + boot.py + all required modules in a single step

# Usage: ./provision.py -c path/to/config.json -ip <target>

# Everything above line 167 copied from webrepl_cli.py with minimal modifications
# https://github.com/micropython/webrepl

import sys
import os
import struct
import json
import socket

DEBUG = 0

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER  = 3



def debugmsg(msg):
    if DEBUG:
        print(msg)



class websocket:

    def __init__(self, s):
        self.s = s
        self.buf = b""

    def write(self, data):
        l = len(data)
        if l < 126:
            # TODO: hardcoded "binary" type
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
                debugmsg("Got unexpected websocket record of type %x, skipping it" % fl)
                while sz:
                    skip = self.s.recv(sz)
                    debugmsg("Skip data: %s" % skip)
                    sz -= len(skip)
            data = self.recvexactly(sz)
            assert len(data) == sz
            self.buf = data

        d = self.buf[:size]
        self.buf = self.buf[size:]
        assert len(d) == size, len(d)
        return d

    def ioctl(self, req, val):
        assert req == 9 and val == 2



def login(ws, passwd):
    while True:
        c = ws.read(1, text_ok=True)
        if c == b":":
            assert ws.read(1, text_ok=True) == b" "
            break
    ws.write(passwd.encode("utf-8") + b"\r")



def read_resp(ws):
    data = ws.read(4)
    sig, code = struct.unpack("<2sH", data)
    assert sig == b"WB"
    return code



def send_req(ws, op, sz=0, fname=b""):
    rec = struct.pack(WEBREPL_REQ_S, b"WA", op, 0, 0, sz, len(fname), fname)
    debugmsg("%r %d" % (rec, len(rec)))
    ws.write(rec)



def get_ver(ws):
    send_req(ws, WEBREPL_GET_VER)
    d = ws.read(3)
    d = struct.unpack("<BBB", d)
    return d



def put_file(ws, local_file, remote_file):
    sz = os.stat(local_file)[6]
    dest_fname = remote_file.encode("utf-8")
    rec = struct.pack(WEBREPL_REQ_S, b"WA", WEBREPL_PUT_FILE, 0, 0, sz, len(dest_fname), dest_fname)
    debugmsg("%r %d" % (rec, len(rec)))
    ws.write(rec[:10])
    ws.write(rec[10:])
    assert read_resp(ws) == 0
    cnt = 0
    with open(local_file, "rb") as f:
        while True:
            sys.stdout.write("Sent %d of %d bytes\r" % (cnt, sz))
            sys.stdout.flush()
            buf = f.read(1024)
            if not buf:
                break
            ws.write(buf)
            cnt += len(buf)
    print("\n")
    assert read_resp(ws) == 0



# Very simplified client handshake, works for MicroPython's
# websocket server implementation, but probably not for other
# servers.
def client_handshake(sock):
    cl = sock.makefile("rwb", 0)
    cl.write(b"""\
GET / HTTP/1.1\r
Host: echo.websocket.org\r
Connection: Upgrade\r
Upgrade: websocket\r
Sec-WebSocket-Key: foo\r
\r
""")
    l = cl.readline()
    while 1:
        l = cl.readline()
        if l == b"\r\n":
            break



#####################################################################################################



def arg_parse():
    if len(sys.argv) < 5:
        print("Example usage: ./provision.py -c path/to/config.json -ip <target>")
        exit()

    for i in range(len(sys.argv)):
        if sys.argv[i] == '-p' or sys.argv[i] == '--password':
            sys.argv.pop(i)
            passwd = sys.argv.pop(i)
            break
    else:
        print("Using default password (password)\n")
        passwd = "password"

    for i in range(len(sys.argv)):
        if sys.argv[i] == '-c' or sys.argv[i] == '--config':
            sys.argv.pop(i)
            config = sys.argv.pop(i)
            break
    else:
        print("ERROR: Must specify config file.")
        exit()

    for i in range(len(sys.argv)):
        if sys.argv[i] == '-ip' or sys.argv[i] == '-t' or sys.argv[i] == '--node':
            sys.argv.pop(i)
            ip = sys.argv.pop(i)
            break
    else:
        print("ERROR: Must specify target IP.")
        exit()

    return passwd, config, ip



# Read config file and return list of required device/sensor modules
def get_modules(config):
    with open(config, 'r') as file:
        conf = json.load(file)

    modules = []

    for i in conf:
        if not i.startswith("device") and not i.startswith("sensor"): continue

        if conf[i]["type"] == "dimmer" or conf[i]["type"] == "bulb":
            modules.append("devices/Tplink.py")

        elif conf[i]["type"] == "relay" or conf[i]["type"] == "desktop":
            modules.append("devices/Relay.py")

        elif conf[i]["type"] == "pwm":
            modules.append("devices/LedStrip.py")

        elif conf[i]["type"] == "ir_blaster":
            modules.append("devices/IrBlaster.py")

        elif conf[i]["type"] == "pir":
            modules.append("sensors/MotionSensor.py")

    # Remove duplicates
    modules = set(modules)

    return modules



# Modified from webrepl_cli.py main() function
def upload(host, port, src_file, dst_file):
    print(f"{src_file} -> {host}:/{dst_file}")

    s = socket.socket()

    ai = socket.getaddrinfo(host, port)
    addr = ai[0][4]

    s.connect(addr)
    client_handshake(s)

    ws = websocket(s)

    login(ws, passwd)

    # Set websocket to send data marked as "binary"
    ws.ioctl(9, 2)

    put_file(ws, src_file, dst_file)

    s.close()



# Relative paths break if run from other dir
if not os.getcwd().split('/')[-1] == 'micropython-smarthome':
    print("ERROR: Must be run from 'micropython-smarthome' directory")
    exit()

# Get config file and target IP from cli arguments
passwd, config, host = arg_parse()

# Read config file, determine which device/sensor modules need to be uploaded
modules = get_modules(config)

port = 8266

# Upload all device/sensor modules
for i in modules:
    src_file = i
    dst_file = i.rsplit("/", 1)[-1] # Remove path from filename

    # TODO - Also get dependencies (ir-tx for ir_blaster) and upload them

    upload(host, port, src_file, dst_file)

# Upload config file
upload(host, port, config, "config.json")

# Upload Config module
upload(host, port, "Config.py", "Config.py")

# Upload main code last (triggers automatic reboot)
upload(host, port, "boot.py", "boot.py")
