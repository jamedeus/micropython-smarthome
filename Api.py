import picoweb
import json
import os
import uasyncio as asyncio
import logging
import gc



# Subclass for compatibility with boot.py
class Api(picoweb.WebApp):
    def __init__(self, pkg, routes=None, serve_static=True):
        super().__init__(pkg, routes=None, serve_static=True)



    # Removed own event loop, boot.py adds to main event loop
    def run(self, host="127.0.0.1", port=8081, debug=False, lazy_init=False, log=None):
        self.log = logging.getLogger("API")
        gc.collect()
        self.debug = int(debug)
        self.init()
        if not lazy_init:
            for app in self.mounts:
                app.init()

        if debug > 0:
            print("* Running on http://%s:%s/" % (host, port))



app = Api(__name__)



@app.route("/reboot")
def index(req, resp):
    yield from picoweb.start_response(resp)
    yield from resp.awrite("Rebooting...")
    from Config import reboot
    reboot()



@app.route("/status")
def status(req, resp):
    status = app.config.get_status()
    yield from picoweb.start_response(resp)
    yield from resp.awrite(json.dumps(status))



@app.route("/enable")
def enable(req, resp):
    target = app.config.find(req.qs)

    if not target:
        yield from picoweb.start_response(resp)
        yield from resp.awrite("ERROR: Instance not found")
    else:
        target.enable()
        data = {"Enabled": target.name}
        yield from picoweb.start_response(resp)
        yield from resp.awrite(json.dumps(data))



@app.route("/disable")
def disable(req, resp):
    target = app.config.find(req.qs)

    if not target:
        yield from picoweb.start_response(resp)
        yield from resp.awrite("ERROR: Instance not found")
    else:
        target.disable()
        data = {"Disabled": target.name}
        yield from picoweb.start_response(resp)
        yield from resp.awrite(json.dumps(data))



@app.route("/set_rule")
def set_rule(req, resp):
    target = req.qs.split("=")[0]
    rule = req.qs.split("=")[1]

    if not target.startswith("sensor") and not target.startswith("device"):
        yield from picoweb.start_response(resp)
        yield from resp.awrite(f"No device/sensor named {target}, use status to see options")
        return
    else:
        target = app.config.find(target)

    if target.set_rule(rule):
        data = {target.name: rule}
        yield from picoweb.start_response(resp)
        yield from resp.awrite(json.dumps(data))

    else:
        yield from picoweb.start_response(resp)
        yield from resp.awrite(f"ERROR: Invalid rule {rule}")



@app.route("/get_temp")
def get_temp(req, resp):
    yield from picoweb.start_response(resp)
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            data = {"Temp": sensor.fahrenheit()}
            yield from resp.awrite(json.dumps(data))
            return True
    else:
        yield from resp.awrite("No temperature sensor configured")



@app.route("/get_humid")
def get_temp(req, resp):
    yield from picoweb.start_response(resp)
    for sensor in app.config.sensors:
        if sensor.sensor_type == "si7021":
            data = {"Humidity": sensor.temp_sensor.relative_humidity}
            yield from resp.awrite(json.dumps(data))
            return True
    else:
        yield from resp.awrite("No temperature sensor configured")



@app.route("/clear_log")
def clear_log(req, resp):
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

        app.log.info("Deleted old log (API request)")

        yield from picoweb.start_response(resp)
        yield from resp.awrite("OK")
    except OSError:
        yield from picoweb.start_response(resp)
        yield from resp.awrite("Error: no log file found")



@app.route("/ir_key")
def ir_key(req, resp):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        yield from picoweb.start_response(resp)
        yield from resp.awrite("Error: No IR blaster configured")

    target = req.qs.split("=")[0]
    key = req.qs.split("=")[1]

    if not target in blaster.codes:
        yield from picoweb.start_response(resp)
        yield from resp.awrite('Error: No codes found for target "{}"'.format(target))
        return
    if not key in blaster.codes[target]:
        yield from picoweb.start_response(resp)
        yield from resp.awrite('Error: Target "{}" has no key {}'.format(target, key))
        return
    else:
        blaster.send(target, key)
        data = {target: key}
        yield from picoweb.start_response(resp)
        yield from resp.awrite(json.dumps(data))



@app.route("/backlight")
def backlight(req, resp):
    try:
        blaster = app.config.ir_blaster
    except AttributeError:
        yield from picoweb.start_response(resp)
        yield from resp.awrite("Error: No IR blaster configured")

    if not req.qs == "on" and not req.qs == "off":
        yield from picoweb.start_response(resp)
        yield from resp.awrite('Error: Backlight setting must be "on" or "off"')
    else:
        blaster.backlight(req.qs)
        data = {"backlight": req.qs}
        yield from picoweb.start_response(resp)
        yield from resp.awrite(json.dumps(data))
