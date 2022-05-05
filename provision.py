#!/usr/bin/env python3

# Upload config file + boot.py + all required modules in a single step

# Usage: ./provision.py -c path/to/config.json -ip <target>

# Everything above line 167 copied from webrepl_cli.py with minimal modifications
# https://github.com/micropython/webrepl

import sys
import os
import struct
import json
import socket
from colorama import Fore, Style

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
def get_modules(config, basepath):

    # Used for initial setup, uploads code that automatically installs dependencies with upip
    if config == "setup.json":
        return [], []

    with open(basepath + "/" + config, 'r') as file:
        conf = json.load(file)

    modules = []

    libs = []
    libs.append('lib/logging.py')


    for i in conf:
        if i == "ir_blaster":
            print(Fore.YELLOW + "WARNING"  + Fore.RESET + ": If this is a new ESP32, upload config/setup.json first to install dependencies\n")

            modules.append("devices/IrBlaster.py")
            modules.append("ir-remote/samsung-codes.json")
            modules.append("ir-remote/whynter-codes.json")
            libs.append("lib/ir_tx/__init__.py")
            libs.append("lib/ir_tx/nec.py")
            continue

        if not i.startswith("device") and not i.startswith("sensor"): continue

        if conf[i]["type"] == "dimmer" or conf[i]["type"] == "bulb":
            modules.append("devices/Tplink.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "relay":
            modules.append("devices/Relay.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "dumb-relay":
            modules.append("devices/DumbRelay.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "desktop":
            if i.startswith("device"):
                modules.append("devices/Desktop_target.py")
                modules.append("devices/Device.py")
            elif i.startswith("sensor"):
                modules.append("sensors/Desktop_trigger.py")
                modules.append("sensors/Sensor.py")

        elif conf[i]["type"] == "pwm":
            modules.append("devices/LedStrip.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "mosfet":
            modules.append("devices/Mosfet.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "api-target":
            modules.append("devices/ApiTarget.py")
            modules.append("devices/Device.py")

        elif conf[i]["type"] == "pir":
            modules.append("sensors/MotionSensor.py")
            modules.append("sensors/Sensor.py")

        elif conf[i]["type"] == "si7021":
            print(Fore.YELLOW + "WARNING"  + Fore.RESET + ": If this is a new ESP32, upload config/setup.json first to install dependencies\n")

            modules.append("sensors/Thermostat.py")
            modules.append("sensors/Sensor.py")
            libs.append("lib/si7021.py")

        elif conf[i]["type"] == "dummy":
            modules.append("sensors/Dummy.py")

    # Remove duplicates
    modules = set(modules)

    return modules, libs



# Modified from webrepl_cli.py main() function
def upload(host, port, src_file, dst_file, basepath):
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

    try:
        put_file(ws, basepath + "/" + src_file, dst_file)
    except AssertionError:

        if src_file.startswith("lib/"):
            print(Fore.RED + "\nERROR: Unable to upload libraries, /lib/ does not exist" + Fore.RESET)
            print("This is normal for new nodes - would you like to upload setup to fix? " + Fore.CYAN + "[Y/n]" + Fore.RESET)
            x = input()
            if x == "n":
                print(Fore.YELLOW + "\nWARNING" + Fore.RESET + ": Skipping " + src_file + " library, node may fail to boot after upload.\n")
                pass
            else:
                upload(host, port, 'config/setup.json', 'config.json')
                upload(host, port, 'setup.py', 'boot.py')
                print(Fore.CYAN + "Please reboot target node and wait 30 seconds, then press enter to resume upload." + Fore.RESET)
                x = input()
                upload(host, port, src_file, dst_file)

        else:
            print(Fore.RED + "ERROR"  + Fore.RESET + ": Unable to upload " + str(dst_file) + ". Node will likely crash after reboot.")
            pass

    s.close()



def provision(config, basepath):
    # Read config file, determine which device/sensor modules need to be uploaded
    modules, libs = get_modules(config, basepath)

    port = 8266

    # Upload all device/sensor modules
    for i in modules:
        src_file = i
        dst_file = i.rsplit("/", 1)[-1] # Remove path from filename

        upload(host, port, src_file, dst_file, basepath)

    # Upload all libraries
    for i in libs:
        src_file = i
        dst_file = i

        upload(host, port, src_file, dst_file, basepath)

    # Upload config file
    upload(host, port, config, "config.json", basepath)

    # Upload Config module
    upload(host, port, "Config.py", "Config.py", basepath)

    # Upload SoftwareTimer module
    upload(host, port, "SoftwareTimer.py", "SoftwareTimer.py", basepath)

    # Upload API module
    upload(host, port, "Api.py", "Api.py", basepath)

    if not "setup.json" in config:
        # Upload main code last (triggers automatic reboot)
        upload(host, port, "boot.py", "boot.py", basepath)
    else:
        # Upload code to install dependencies
        upload(host, port, "setup.py", "boot.py", basepath)



basepath = os.path.dirname(os.path.realpath(__file__))

# Load config file
try:
    with open(basepath + "/" + '/nodes.json', 'r') as file:
        nodes = json.load(file)
except FileNotFoundError:
    print("Warning: Unable to find nodes.json, friendly names will not work")
    nodes = {}



# If user selected node by name
if sys.argv[1] in nodes:
    passwd = "password"
    config = nodes[sys.argv[1]]["config"]
    host = nodes[sys.argv[1]]["ip"]
    provision(config)

# If user selected all nodes
elif sys.argv[1] == "--all":
    passwd = "password"
    for i in nodes:
        config = nodes[i]["config"]
        host = nodes[i]["ip"]
        provision(config)

# If user used keyword args
else:
    # Get config file and target IP from cli arguments
    passwd, config, host = arg_parse()

    provision(config, basepath)
