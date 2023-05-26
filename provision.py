#!/usr/bin/env python3

# Upload config file + boot.py + all required modules and libraries in a single step

# Usage: ./provision.py -c path/to/config.json -ip <target>
# Usage: ./provision.py <friendly-name-from-nodes.json>
# Usage: ./provision.py --all

# Everything above line 156 copied from webrepl_cli.py with minimal modifications
# https://github.com/micropython/webrepl

import sys
import os
import struct
import json
import socket
import re
from colorama import Fore

DEBUG = 0

WEBREPL_REQ_S = "<2sBBQLH64s"
WEBREPL_PUT_FILE = 1
WEBREPL_GET_FILE = 2
WEBREPL_GET_VER  = 3

ip_regex = "^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"


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


class Provisioner():
    def __init__(self, args):
        # Show example usage and exit if no args given
        if len(args) < 2:
            print("Example usage: ./provision.py -c path/to/config.json -ip <target>")

        # Location of provision.py, used to get relative path to other modules if run from outside dir
        self.basepath = os.path.dirname(os.path.realpath(__file__))

        # Load config file
        try:
            with open(self.basepath + "/" + '/nodes.json', 'r') as file:
                self.nodes = json.load(file)
        except FileNotFoundError:
            print("Warning: Unable to find nodes.json, friendly names will not work")
            self.nodes = {}

        # If user selected node by name
        if args[1] in self.nodes:
            self.passwd = "password"
            self.config = self.nodes[args[1]]["config"]
            self.host = self.nodes[args[1]]["ip"]

        # If user selected all nodes
        elif args[1] == "--all":
            self.passwd = "password"
            for i in self.nodes:
                print(f"\n{i}\n")
                self.config = self.nodes[i]["config"]
                self.host = self.nodes[i]["ip"]
                self.provision()
            raise SystemExit

        # If user selected unit tests
        # TODO this fails with unhelpful errors when target dirs (/tests/) don't exist, should offer to upload setup
        # This also doesn't upload libs (si7021)
        elif args[1] == "--test":
            # Get config file and target IP from cli arguments
            self.passwd = "password"
            for i in args:
                if re.match(ip_regex, i):
                    self.host = i
                    break
            else:
                print("Example usage: ./provision.py --test <ip>")
                raise SystemExit

            if not self.open_connection():
                print("Error: Test node not connected to network or not accepting webrepl connections.\n")
                raise SystemExit

            # Upload all tests
            for i in os.listdir('/home/jamedeus/git/micropython-smarthome/tests'):
                if i.startswith("test_"):
                    self.upload("tests/" + i, "tests/" + i)

            # Upload all device classes
            for i in os.listdir('/home/jamedeus/git/micropython-smarthome/devices'):
                self.upload("devices/" + i, i)

            # Upload all sensor classes
            for i in os.listdir('/home/jamedeus/git/micropython-smarthome/sensors'):
                self.upload("sensors/" + i, i)

            # Upload Config module
            self.upload("Config.py", "Config.py")

            # Upload Group module
            self.upload("Group.py", "Group.py")

            # Upload SoftwareTimer module
            self.upload("SoftwareTimer.py", "SoftwareTimer.py")

            # Upload API module
            self.upload("Api.py", "Api.py")

            # Upload boot.py (unit test version automatically runs all tests on boot)
            self.upload("tests/unit_test_boot.py", "boot.py")

            self.close_connection()

            # Exit to prevent provision from running (already provisioned)
            raise SystemExit

        # If user used keyword args
        else:
            # Get config file and target IP from cli arguments
            self.passwd, self.config, self.host = self.arg_parse(args)

    def arg_parse(self, args):
        if len(args) < 5:
            print("Example usage: ./provision.py -c path/to/config.json -ip <target>")
            raise SystemExit

        for i in range(len(args)):
            if args[i] == '-p' or args[i] == '--password':
                args.pop(i)
                passwd = args.pop(i)
                break
        else:
            print("Using default password (password)\n")
            passwd = "password"

        for i in range(len(args)):
            if args[i] == '-c' or args[i] == '--config':
                args.pop(i)
                config = args.pop(i)
                if not config.endswith('.json'):
                    print("ERROR: Config file must be json.")
                    raise SystemExit
                break
        else:
            print("ERROR: Must specify config file.")
            raise SystemExit

        for i in range(len(args)):
            if args[i] == '-ip' or args[i] == '-t' or args[i] == '--node':
                args.pop(i)
                ip = args.pop(i)
                if not re.match(ip_regex, ip):
                    print("ERROR: Invalid IP address.")
                    raise SystemExit
                break
        else:
            print("ERROR: Must specify target IP.")
            raise SystemExit

        return passwd, config, ip

    def provision(self):
        # Read config file, determine which device/sensor modules need to be uploaded
        with open(self.basepath + "/" + self.config, 'r') as file:
            modules, libs = self.get_modules(json.load(file))

        if not self.open_connection():
            print(f"Error: {self.host} not connected to network or not accepting webrepl connections.\n")
            return

        # Upload all device/sensor modules
        for i in modules:
            src_file = i
            dst_file = i.rsplit("/", 1)[-1]  # Remove path from filename

            self.upload(src_file, dst_file)

        # Upload all libraries
        for i in libs:
            src_file = i
            dst_file = i

            self.upload(src_file, dst_file)

        # Upload config file
        self.upload(self.config, "config.json")

        # Upload Config module
        self.upload("Config.py", "Config.py")

        # Upload Group module
        self.upload("Group.py", "Group.py")

        # Upload SoftwareTimer module
        self.upload("SoftwareTimer.py", "SoftwareTimer.py")

        # Upload API module
        self.upload("Api.py", "Api.py")

        if "setup.json" not in self.config:
            # Upload main code last (triggers automatic reboot)
            self.upload("boot.py", "boot.py")
        else:
            # Upload code to install dependencies
            self.upload("setup.py", "boot.py")

        self.close_connection()

    # Takes loaded config file as arg, returns list of required device/sensor/library modules
    def get_modules(self, conf):
        # Used for initial setup, uploads code that automatically creates required subdirs
        if self.config == "setup.json":
            return [], []

        modules = []

        libs = []
        libs.append('lib/logging.py')

        for i in conf:
            if i == "ir_blaster":
                print(Fore.YELLOW + "WARNING" + Fore.RESET, end="")
                print(": If this is a new ESP32, upload config/setup.json first to install dependencies\n")

                modules.append("devices/IrBlaster.py")
                modules.append("ir-remote/samsung-codes.json")
                modules.append("ir-remote/whynter-codes.json")
                libs.append("lib/ir_tx/__init__.py")
                libs.append("lib/ir_tx/nec.py")
                continue

            if i.startswith("device"):
                if conf[i]["device_type"] == "dimmer" or conf[i]["device_type"] == "bulb":
                    modules.append("devices/Tplink.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "relay":
                    modules.append("devices/Relay.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "dumb-relay":
                    modules.append("devices/DumbRelay.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "desktop":
                    modules.append("devices/Desktop_target.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "pwm":
                    modules.append("devices/LedStrip.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "mosfet":
                    modules.append("devices/Mosfet.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "api-target":
                    modules.append("devices/ApiTarget.py")
                    modules.append("devices/Device.py")

                elif conf[i]["device_type"] == "wled":
                    modules.append("devices/Wled.py")
                    modules.append("devices/Device.py")

            elif i.startswith("sensor"):
                if conf[i]["sensor_type"] == "desktop":
                    modules.append("sensors/Desktop_trigger.py")
                    modules.append("sensors/Sensor.py")

                elif conf[i]["sensor_type"] == "pir":
                    modules.append("sensors/MotionSensor.py")
                    modules.append("sensors/Sensor.py")

                elif conf[i]["sensor_type"] == "si7021":
                    print(Fore.YELLOW + "WARNING" + Fore.RESET, end="")
                    print(": If this is a new ESP32, upload config/setup.json first to install dependencies\n")

                    modules.append("sensors/Thermostat.py")
                    modules.append("sensors/Sensor.py")
                    libs.append("lib/si7021.py")

                elif conf[i]["sensor_type"] == "dummy":
                    modules.append("sensors/Dummy.py")
                    modules.append("sensors/Sensor.py")

                elif conf[i]["sensor_type"] == "switch":
                    modules.append("sensors/Switch.py")
                    modules.append("sensors/Sensor.py")

            else: continue

        # Remove duplicates
        modules = set(modules)

        return modules, libs

    def open_connection(self):
        try:
            self.s = socket.socket()
            self.s.settimeout(5)

            ai = socket.getaddrinfo(self.host, 8266)
            addr = ai[0][4]

            self.s.connect(addr)
            client_handshake(self.s)

            self.ws = websocket(self.s)

            login(self.ws, self.passwd)

            # Set websocket to send data marked as "binary"
            self.ws.ioctl(9, 2)

            return True

        except OSError:
            # Target disconnected from network
            self.s.close()
            return False

    # Modified from webrepl_cli.py main() function
    def upload(self, src_file, dst_file):
        print(f"{src_file} -> {self.host}:/{dst_file}")

        try:
            put_file(self.ws, self.basepath + "/" + src_file, dst_file)
        except AssertionError:

            if src_file.startswith("lib/"):
                print(Fore.RED + "\nERROR: Unable to upload libraries, /lib/ does not exist" + Fore.RESET)
                print("This is normal for new nodes - would you like to upload setup to fix? ", end="")
                print(Fore.CYAN + "[Y/n]" + Fore.RESET)

                x = input()
                if x == "n":
                    print(Fore.YELLOW + "\nWARNING" + Fore.RESET, end="")
                    print(": Skipping " + src_file + " library, node may fail to boot after upload.\n")
                    pass
                else:
                    # Connection was broken by error, close and re-open
                    self.close_connection()
                    self.open_connection()

                    # Upload setup config and boot file (creates required directory structure then waits for upload_
                    self.upload('config/setup.json', 'config.json')
                    self.upload('setup.py', 'boot.py')

                    # Close connection (node rebooted)
                    self.close_connection()

                    # Resume upload once user restarts node
                    print(Fore.CYAN + "Please reboot target node and wait 30 seconds, then press enter to resume upload." + Fore.RESET)
                    x = input()
                    self.open_connection()
                    self.upload(src_file, dst_file)

            else:
                print(Fore.RED + "ERROR" + Fore.RESET, end="")
                print(": Unable to upload " + str(dst_file) + ". Node will likely crash after reboot.")
                pass

    def close_connection(self):
        self.s.close()


if __name__ == "__main__":
    # Create instance, pass CLI arguments to init
    app = Provisioner(sys.argv)
    app.provision()
