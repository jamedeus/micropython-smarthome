import json
import os
import uasyncio as asyncio
import logging
import gc
import SoftwareTimer
import re

# Set name for module's log lines
log = logging.getLogger("API")



class Api:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        # Populated with decorators + self.route
        # Key = endpoint, value = function
        self.url_map = {}



    def route(self, url):
        def _route(func):
            self.url_map[url] = func
        return _route



    async def run(self):
        print('API: Awaiting client connection.\n')
        log.info("API ready")
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(25)



    async def run_client(self, sreader, swriter):
        try:
            # Read client request
            res = await asyncio.wait_for(sreader.readline(), self.timeout)

            # Receives null when client closes write stream - break and close read stream
            if not res: raise OSError

            res = res.decode()

            # Determine if request is HTTP (browser) or raw JSON (much faster, used by api_client.py and other nodes)
            if res.startswith("GET"):
                http = True
                path = res.split()[1]

                path = path.split("?", 1)
                qs = ""
                if len(path) > 1:
                    qs = path[1]
                    qs = qs.split("/")
                path = path[0][1:]

                # Skip headers
                while True:
                    l = await asyncio.wait_for(sreader.readline(), self.timeout)
                    if l == b"\r\n":
                        break

            else:
                http = False
                # Get dict of parameters
                data = json.loads(res.rstrip())
                path = data[0]
                qs = data[1:]

            # Find endpoint matching data[0], call handler function and pass remaining args (data[1:])
            try:
                # Call handler, receive reply for client
                reply = self.url_map[path](qs)
            except KeyError:
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



app = Api()



@app.route("reboot")
def index(params):
    from Config import reboot
    SoftwareTimer.timer.create(1000, reboot, "API")

    return {"Reboot_in": "1 second"}



@app.route("status")
def status(params):
    return app.config.get_status()



@app.route("enable")
def enable(params):
    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        target.enable()
        return {"Enabled": target.name}



@app.route("enable_in")
def enable_for(params):
    if not len(params) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])
    period = params[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        period = float(period) * 60000
        SoftwareTimer.timer.create(period, target.enable, "API")
        return {"Enabled": target.name, "Enable_in_seconds": period/1000}



@app.route("disable")
def disable(params):
    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        target.disable()
        return {"Disabled": target.name}



@app.route("disable_in")
def disable_for(params):
    if not len(params) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])
    period = params[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        period = float(period) * 60000
        SoftwareTimer.timer.create(period, target.disable, "API")
        return {"Disabled": target.name, "Disable_in_seconds": period/1000}



@app.route("set_rule")
def set_rule(params):
    if not len(params) >= 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])
    rule = params[1]

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    if target.set_rule(rule):
        return {target.name : rule}
    else:
        return {"ERROR": "Invalid rule"}



@app.route("reset_rule")
def reset_rule(params):
    if not len(params) == 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    target.current_rule = target.scheduled_rule

    return {target.name : "Reverted to scheduled rule", "current_rule" : target.current_rule}



@app.route("get_schedule_rules")
def get_schedule_rules(params):
    if not len(params) == 1:
        return {"ERROR": "Invalid syntax"}

    try:
        rules = app.config.schedule[params[0]]
    except KeyError:
        return {"ERROR": "Instance not found, use status to see options"}

    return rules



@app.route("add_schedule_rule")
def add_schedule_rule(params):
    if not len(params) == 3:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    rules = app.config.schedule[params[0]]

    if re.match("^[0-9][0-9]:[0-9][0-9]$", params[1]):
        timestamp = params[1]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    if target.rule_validator(params[2]):
        rules[timestamp] = params[2]
        app.config.schedule[params[0]] = rules
        app.config.build_queue()
        return {"Rule added" : params[2], "time" : timestamp}
    else:
        return {"ERROR": "Invalid rule"}



@app.route("remove_rule")
def remove_rule(params):
    if not len(params) == 2:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    rules = app.config.schedule[params[0]]

    if re.match("^[0-9][0-9]:[0-9][0-9]$", params[1]):
        timestamp = params[1]
    else:
        return {"ERROR": "Timestamp format must be HH:MM (no AM/PM)"}

    try:
        del rules[timestamp]
        app.config.schedule[params[0]] = rules
        app.config.build_queue()
    except KeyError:
        return {"ERROR": "No rule exists at that time"}

    return {"Deleted": timestamp}



@app.route("get_attributes")
def get_attributes(params):
    if not len(params) == 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

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

    return attributes



@app.route("condition_met")
def condition_met(params):
    if not len(params) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}
    else:
        return {"Condition": target.condition_met()}



@app.route("trigger_sensor")
def trigger_sensor(params):
    if not len(params) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    result = target.trigger()
    if result:
        return {"Triggered": target.name}
    else:
        return {"ERROR": "Cannot trigger {} sensor type".format(target.sensor_type)}



@app.route("turn_on")
def turn_on(params):
    if not len(params) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    result = target.send(1)
    if result:
        target.state = True
        return {"On": target.name}
    else:
        return {"ERROR": "Unable to turn on {}".format(target.name)}



@app.route("turn_off")
def turn_on(params):
    if not len(params) >= 1:
        return {"ERROR": "Invalid syntax"}

    target = app.config.find(params[0])

    if not target:
        return {"ERROR": "Instance not found, use status to see options"}

    result = target.send(0)
    if result:
        target.state = False
        return {"Off": target.name}
    else:
        return {"ERROR": "Unable to turn off {}".format(target.name)}



@app.route("get_temp")
def get_temp(params):
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            return {"Temp": sensor.fahrenheit()}
    else:
        return {"ERROR": "No temperature sensor configured"}



@app.route("get_humid")
def get_temp(params):
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            return {"Humidity": sensor.temp_sensor.relative_humidity}
    else:
        return {"ERROR": "No temperature sensor configured"}



@app.route("clear_log")
def clear_log(params):
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
def ir_key(params):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"ERROR": "No IR blaster configured"}

    target = params[0]
    key = params[1]

    if not target in blaster.codes:
        return {"ERROR": 'No codes found for target "{}"'.format(target)}

    if not key in blaster.codes[target]:
        return {"ERROR": 'Target "{}" has no key {}'.format(target, key)}

    else:
        blaster.send(target, key)
        return {target: key}



@app.route("backlight")
def backlight(params):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        return {"Error": "No IR blaster configured"}

    if not params[0] == "on" and not params[0] == "off":
        return {'ERROR': 'Backlight setting must be "on" or "off"'}
    else:
        blaster.backlight(params[0])
        return {"backlight": params[0]}
