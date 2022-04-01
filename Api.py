import json
import os
import uasyncio as asyncio
import logging
import gc

# Set name for module's log lines
log = logging.getLogger("API")



class Api:
    def __init__(self, config, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

        self.config = config



    def disable(self, instance):
        inst = self.config.find(instance)

        if not inst:
            return 'Error: Instance not found'

        print(f"API: Received command to disable {instance}, disabling...")
        log.info(f"API: Received command to disable {instance}, disabling...")
        inst.disable()
        return 'OK'



    def enable(self, instance):
        inst = self.config.find(instance)

        if not inst:
            return 'Error: Instance not found'

        print(f"API: Received command to enable {instance}, enabling...")
        log.info(f"API: Received command to enable {instance}, enabling...")
        inst.enable()
        return 'OK'



    def set_rule(self, target, rule, client):
        target = self.config.find(target)

        if not target:
            print(f"API: Received invalid command from {client}")
            return 'Error: 2nd param must be name of a sensor or device - use status to see options'

        if target.set_rule(rule):
            return 'OK'
        else:
            return 'Error: Bad rule parameter'



    def ir_key(self, target, key):
        try:
            blaster = self.config.ir_blaster
        except AttributeError:
            return 'Error: No IR blaster configured'

        if not target in blaster.codes:
            return 'Error: No codes found for target "{}"'.format(target)
        if not key in blaster.codes[target]:
            return 'Error: Target "{}" has no key {}'.format(target, key)
        else:
            blaster.send(target, key)
            return 'OK'



    def ir_backlight(self, state):
        if not (state == "on" or state == "off"):
            return 'Error: Backlight setting must be "on" or "off"'

        try:
            blaster = self.config.ir_blaster
        except AttributeError:
            return 'Error: No IR blaster configured'

        blaster.backlight(state)
        return 'OK'



    def get_temp(self):
        for sensor in self.config.sensors:
            if sensor.sensor_type == "si7021":
                return sensor.fahrenheit()
        else:
            return 'Error: No temp sensor connected'



    def get_humid(self):
        for sensor in self.config.sensors:
            if sensor.sensor_type == "si7021":
                return sensor.temp_sensor.relative_humidity
        else:
            return 'Error: No temp sensor connected'



    def clear_log(self):
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

            return 'OK'
        except OSError:
            return 'Error: no log file found'



    async def run(self):
        print('API: Awaiting client connection.\n')
        log.info("API ready")
        self.server = await asyncio.start_server(self.run_client, self.host, self.port, self.backlog)
        while True:
            await asyncio.sleep(100)



    async def run_client(self, sreader, swriter):
        try:
            while True:
                try:
                    res = await asyncio.wait_for(sreader.readline(), self.timeout)
                except asyncio.TimeoutError:
                    raise OSError

                # Receives null when client closes write stream - break and close read stream
                if not res: break

                data = json.loads(res.rstrip())

                # Will be overwritten if command is valid, checked after conditional before sending invalid syntax error
                reply = False

                if data[0] == "status":
                    print(f"\nAPI: Status request received from {sreader.get_extra_info('peername')[0]}, sending dict\n")
                    reply = self.config.get_status()

                elif data[0] == "reboot":
                    print(f"API: Reboot command received from {sreader.get_extra_info('peername')[0]}")

                    # Send response before rebooting (cannot rely on the send call after conditional)
                    reply = 'OK'
                    swriter.write(json.dumps(reply))
                    await swriter.drain()  # Echo back
                    from Config import reboot
                    reboot()

                elif data[0] == "temp":
                    reply = self.get_temp()

                elif data[0] == "humid":
                    reply = self.get_humid()

                elif data[0] == "clear_log":
                    reply = self.clear_log()

                elif data[0] == "disable" and (data[1].startswith("sensor") or data[1].startswith("device")):
                    reply = self.disable(data[1])

                elif data[0] == "enable" and (data[1].startswith("sensor") or data[1].startswith("device")):
                    reply = self.enable(data[1])

                elif data[0] == "set_rule" and (data[1].startswith("sensor") or data[1].startswith("device")):
                    reply = self.set_rule(data[1], data[2], sreader.get_extra_info('peername')[0])

                elif data[0] == "ir" and (data[1] == "tv" or data[1] == "ac"):
                    reply = self.ir_key(data[1], data[2])

                elif data[0] == "ir" and data[1] == "backlight":
                    reply = self.ir_backlight(data[2])

                else:
                    print(f"API: Received invalid command from {sreader.get_extra_info('peername')[0]}")
                    reply = 'Error: first arg must be one of: status, reboot, enable, disable, set_rule, clear_log, temp, humid, ir'

                # Send the reply
                swriter.write(json.dumps(reply))
                await swriter.drain()
                reply = False

                # Prevent running out of mem after repeated requests
                gc.collect()

        except OSError:
            pass
        # Client disconnected, close socket
        await sreader.wait_closed()
