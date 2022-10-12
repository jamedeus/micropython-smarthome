import json
import os
import uasyncio as asyncio
import logging
import gc
import SoftwareTimer
import re
from uasyncio import Lock

# Set name for module's log lines
log = logging.getLogger("API")

lock = Lock()

async def reboot():
    # Lock released when API finishes sending reply
    await lock.acquire()
    from Config import reboot
    reboot()



class Api:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        # Populated by decorators + self.route
        # Key = endpoint, value = function
        self.url_map = {}



    def route(self, url):
        def _route(func):
            self.url_map[url] = func
        return _route



    async def run(self):
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        print('API: Awaiting client connection.\n')
        log.info("API ready")
        while True:
            await asyncio.sleep(25)



    async def run_client(self, sreader, swriter):
        try:
            # Read client request
            req = await asyncio.wait_for(sreader.readline(), self.timeout)

            # Receives null when client closes write stream - break and close read stream
            if not req: raise OSError

            # Determine if request is HTTP (browser) or raw JSON (much faster, used by api_client.py and other nodes)
            if req.startswith("GET"):
                # Received something like "GET /status HTTP/1.1"
                http = True

                req = req.decode()

                # Drop all except "/status"
                path = req.split()[1]

                # Convert to list, path ("/status") as first index, query string (if present) as second
                path = path.split("?", 1)

                if len(path) > 1:
                    # If query string present, split all parameters into args list
                    args = path[1]
                    args = args.split("/")
                else:
                    # No query string
                    args = ""

                # Drop all except path ("/status"), remove leading "/"
                path = path[0][1:]

                # Skip headers
                while True:
                    l = await asyncio.wait_for(sreader.readline(), self.timeout)
                    # Sequence indicates end of headers
                    if l == b"\r\n":
                        break

            else:
                # Received serialized json, no headers etc
                http = False

                # Convert to dict, get path and args
                data = json.loads(req)
                path = data[0]
                args = data[1:]

            # Acquire lock, prevents reboot until finished sending reply
            await lock.acquire()

            # Find endpoint matching path, call handler function and pass args
            try:
                # Call handler, receive reply for client
                reply = self.url_map[path](args)
            except KeyError:
                if http:
                    # Send headers before reply
                    swriter.write("HTTP/1.0 404 NA\r\nContent-Type: application/json\r\n\r\n")
                    swriter.write(json.dumps({"ERROR": "Invalid command"}).encode())
                else:
                    # Exit with error if no match found
                    swriter.write(json.dumps({"ERROR": "Invalid command"}))

                await swriter.drain()
                raise OSError

            if http:
                # Send headers before reply
                swriter.write("HTTP/1.0 200 NA\r\nContent-Type: application/json\r\n\r\n")
                swriter.write(json.dumps(reply).encode())
            else:
                # Send reply to client
                swriter.write(json.dumps(reply))

            await swriter.drain()

            # Prevent running out of mem after repeated requests
            gc.collect()

        except OSError:
            pass
        except asyncio.TimeoutError:
            pass
        # Client disconnected, close socket
        await sreader.wait_closed()

        # Allow reboot (if reboot endpoint was called)
        try:
            lock.release()
        except RuntimeError:
            # Prevent crash if connection timed out before lock acquired
            pass



app = Api()



@app.route("reboot")
def index(args):
    asyncio.create_task(reboot())
    return "Rebooting"



@app.route("status")
def status(args):
    return app.config.get_status()



@app.route("enable")
def enable(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        target.enable()
        return {"Enabled": target.name}



@app.route("enable_in")
def enable_for(args):
    if not len(args) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])
    period = args[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        period = float(period) * 60000
        SoftwareTimer.timer.create(period, target.enable, "API")
        return {"Enabled": target.name, "Enable_in_seconds": period/1000}



@app.route("disable")
def disable(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        target.disable()
        return {"Disabled": target.name}



@app.route("disable_in")
def disable_for(args):
    if not len(args) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])
    period = args[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        period = float(period) * 60000
        SoftwareTimer.timer.create(period, target.disable, "API")
        return {"Disabled": target.name, "Disable_in_seconds": period/1000}



@app.route("set_rule")
def set_rule(args):
    if not len(args) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])
    rule = args[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    if target.set_rule(rule):
        return {target.name : rule}
    else:
        return {"ERROR": "Invalid rule"}



@app.route("reset_rule")
def reset_rule(args):
    if not len(args) == 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    target.set_rule(target.scheduled_rule)

    return {target.name : "Reverted to scheduled rule", "current_rule" : target.current_rule}



@app.route("reset_all_rules")
def reset_all_rules(args):
    response = {}
    response["New rules"] = {}

    for device in app.config.devices:
        device.set_rule(device.scheduled_rule)
        response["New rules"][device.name] = device.current_rule

    for sensor in app.config.sensors:
        sensor.set_rule(sensor.scheduled_rule)
        response["New rules"][sensor.name] = sensor.current_rule

    return response



@app.route("get_schedule_rules")
def get_schedule_rules(args):
    if not len(args) == 1:
        return {"ERROR": "Invalid syntax"}

    try:
        rules = app.config.schedule[args[0]]
    except KeyError:
        return {"ERROR": "Instance not found, use status to see options"}

    return rules



@app.route("add_schedule_rule")
def add_schedule_rule(args):
    if not len(args) >= 3:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    rules = app.config.schedule[args[0]]

    if re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", args[1]):
        timestamp = args[1]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    valid = target.rule_validator(args[2])

    if str(valid) == "False":
        return {"ERROR": "Invalid rule"}

    if timestamp in rules and (not len(args) >=4 or not args[3] == "overwrite"):
        return {"ERROR": "Rule already exists at {}, add 'overwrite' arg to replace".format(timestamp)}
    else:
        rules[timestamp] = valid
        app.config.schedule[args[0]] = rules
        app.config.build_queue()
        return {"Rule added" : valid, "time" : timestamp}



@app.route("remove_rule")
def remove_rule(args):
    if not len(args) == 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    rules = app.config.schedule[args[0]]

    if re.match("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$", args[1]):
        timestamp = args[1]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    try:
        del rules[timestamp]
        app.config.schedule[args[0]] = rules
        app.config.build_queue()
    except KeyError:
        return {"ERROR": "No rule exists at that time"}

    return {"Deleted": timestamp}



@app.route("save_rules")
def save_rules(args):
    with open('config.json', 'r') as file:
        config = json.load(file)

    for i in config:
        if i.startswith("sensor") or i.startswith("device"):
            config[i]["schedule"] = app.config.schedule[i]

    with open('config.json', 'w') as file:
        json.dump(config, file)

    return {"Success": "Rules written to disk"}



@app.route("get_attributes")
def get_attributes(args):
    if not len(args) == 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    attributes = target.__dict__.copy()

    # Make dict json-compatible
    for i in attributes.keys():
        # Remove module references
        if i == "pwm":
            del attributes["pwm"]
        if i == "i2c":
            del attributes["i2c"]
        if i == "temp_sensor":
            del attributes["temp_sensor"]
        if i == "mosfet":
            del attributes["mosfet"]
        if i == "relay":
            del attributes["relay"]
        if i == "sensor":
            del attributes["sensor"]

        # Replace instances with instance.name attribute
        elif i == "triggered_by":
            attributes["triggered_by"] = []
            for i in target.triggered_by:
                attributes["triggered_by"].append(i.name)
        elif i == "targets":
            attributes["targets"] = []
            for i in target.targets:
                attributes["targets"].append(i.name)

    # Replace group object with group name (JSON compatibility)
    if "group" in attributes.keys():
        attributes["group"] = target.group.name

    return attributes



@app.route("condition_met")
def condition_met(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    if not str(args[0]).startswith("sensor"):
        return {"ERROR": "Must specify sensor"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        return {"Condition": target.condition_met()}



@app.route("trigger_sensor")
def trigger_sensor(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    if not str(args[0]).startswith("sensor"):
        return {"ERROR": "Must specify sensor"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    result = target.trigger()
    if result:
        return {"Triggered": target.name}
    else:
        return {"ERROR": "Cannot trigger {} sensor type".format(target.sensor_type)}



@app.route("turn_on")
def turn_on(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    if not str(args[0]).startswith("device"):
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    if not target.enabled:
        return {"ERROR": f"{target.name} is disabled, please enable before turning on"}

    result = target.send(1)
    if result:
        target.state = True
        return {"On": target.name}
    else:
        return {"ERROR": "Unable to turn on {}".format(target.name)}



@app.route("turn_off")
def turn_on(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    if not str(args[0]).startswith("device"):
        return {"ERROR": "Can only turn on/off devices, use enable/disable for sensors"}

    target = app.config.find(args[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    result = target.send(0)
    if result:
        target.state = False
        return {"Off": target.name}
    else:
        return {"ERROR": "Unable to turn off {}".format(target.name)}



@app.route("get_temp")
def get_temp(args):
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            return {"Temp": sensor.fahrenheit()}
    else:
        return {"ERROR": "No temperature sensor configured"}



@app.route("get_humid")
def get_temp(args):
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            return {"Humidity": sensor.temp_sensor.relative_humidity}
    else:
        return {"ERROR": "No temperature sensor configured"}



@app.route("get_climate_data")
def get_climate_data(args):
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            data = {}
            data["temp"] = sensor.fahrenheit()
            data["humid"] = sensor.temp_sensor.relative_humidity
            return data
    else:
        return {"ERROR": "No temperature sensor configured"}



@app.route("clear_log")
def clear_log(args):
    try:
        # Close file, remove
        logging.root.handlers[0].close()
        os.remove('app.log')

        # Create new handler, set format
        h = logging.FileHandler('app.log')
        h.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))

        # Replace old handler with new
        logging.root.handlers.clear()
        logging.root.addHandler(h)

        log.info("Deleted old log (API request)")

        return {"clear_log": "success"}
    except OSError:
        return {"ERROR": "no log file found"}



@app.route("ir_key")
def ir_key(args):
    if not len(args) >= 2:
        return {"ERROR": "Invalid syntax"}

    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    target = args[0]
    key = args[1]

    if not target in blaster.codes:
        return {"ERROR": 'No codes found for target "{}"'.format(target)}

    if not key.lower() in blaster.codes[target]:
        return {"ERROR": 'Target "{}" has no key {}'.format(target, key)}

    else:
        blaster.send(target, key.lower())
        return {target: key}



@app.route("backlight")
def backlight(args):
    if not len(args) >= 1:
        return {"ERROR": "Invalid syntax"}

    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"Error": "No IR blaster configured"}

    if not args[0] == "on" and not args[0] == "off":
        return {'ERROR': 'Backlight setting must be "on" or "off"'}
    else:
        blaster.backlight(args[0])
        return {"backlight": args[0]}
