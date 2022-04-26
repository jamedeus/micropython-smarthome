import json
import os
import uasyncio as asyncio
import logging
import gc
import SoftwareTimer

# Set name for module's log lines
log = logging.getLogger("API")



class Api:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        self.url_map = []



    def route(self, url, **kwargs):
        def _route(func):
            self.url_map.append((url, func, kwargs))
            return func
        return _route



    async def run(self):
        print('API: Awaiting client connection.\n')
        log.info("API ready")
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)



    async def run_client(self, sreader, swriter):
        try:
            # Read client request
            res = await asyncio.wait_for(sreader.readline(), self.timeout)

            # Receives null when client closes write stream - break and close read stream
            if not res: raise OSError

            # Get dict of parameters
            data = json.loads(res.rstrip())

            # Find correct endpoint + handler function
            for endpoint in self.url_map:
                if data[0] == endpoint[0]:
                    # Call handler, receive reply for client
                    reply = endpoint[1](data[1:])
                    break
            else:
                # Exit with error if no match found
                swriter.write(json.dumps({"ERROR": "Invalid command"}))
                await swriter.drain()
                raise OSError

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
