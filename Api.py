import json
import os
import uasyncio as asyncio
import logging
import Config
import gc

# Set log file and syntax
logging.basicConfig(level=logging.INFO, filename='app.log', format='%(asctime)s - %(levelname)s - %(name)s - %(message)s', style='%')
log = logging.getLogger("API")



class Api:
    def __init__(self, host='0.0.0.0', port=8123, backlog=5, timeout=20):
        self.host = host
        self.port = port
        self.backlog = backlog
        self.timeout = timeout

    def disable(self, sensor):
        sensor = Config.config.find(sensor)

        if not sensor:
            return 'Error: Sensor not found'

        print(f"API: Received command to disable {sensor}, disabling...")
        log.info(f"API: Received command to disable {sensor}, disabling...")
        sensor.disable()
        return 'OK'



    def enable(self, sensor):
        sensor = Config.config.find(sensor)

        if not sensor:
            return 'Error: Sensor not found'

        print(f"API: Received command to enable {sensor}, enabling...")
        log.info(f"API: Received command to enable {sensor}, enabling...")
        sensor.enable()
        return 'OK'



    def set_rule(self, target, rule, client):
        target = Config.config.find(target)

        if not target:
            print(f"API: Received invalid command from {client}")
            return 'Error: 2nd param must be name of a sensor or device - use status to see options'

        try:
            target.current_rule = rule
            return 'OK'
        except:
            return 'Error: Bad rule parameter'



    def ir_key(self, target, key):
        for i in Config.config.devices:
            if i.device == "ir_blaster":
                blaster = i
                break
        else:
            return 'Error: No IR blaster configured'

        if not target in i.codes:
            return 'Error: No codes found for target "{}"'.format(target)
        if not key in i.codes[target]:
            return 'Error: Target "{}" has no key {}'.format(target, key)
        else:
            i.send(target, key)
            return 'OK'



    def ir_backlight(self, state):
        if not (state == "on" or state == "off"):
            return 'Error: Backlight setting must be "on" or "off"'
        else:
            for i in Config.config.devices:
                if i.device == "ir_blaster":
                    i.backlight(state)
                    return 'OK'

        return 'Error: No IR blaster configured'



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
                    reply = Config.config.get_status()
                    type(reply)

                elif data[0] == "reboot":
                    print(f"API: Reboot command received from {sreader.get_extra_info('peername')[0]}")

                    # Send response before rebooting (cannot rely on the send call after conditional)
                    reply = 'OK'
                    swriter.write(json.dumps(reply))
                    await swriter.drain()  # Echo back
                    Config.reboot()

                elif data[0] == "disable" and data[1].startswith("sensor"):
                    reply = self.disable(data[1])

                elif data[0] == "enable" and data[1].startswith("sensor"):
                    reply = self.enable(data[1])

                elif data[0] == "set_rule" and data[1].startswith("sensor") or data[1].startswith("device"):
                    reply = self.set_rule(data[1], data[2], sreader.get_extra_info('peername')[0])

                elif data[0] == "ir" and (data[1] == "tv" or data[1] == "ac"):
                    reply = self.ir_key(data[1], data[2])

                elif data[0] == "ir" and data[1] == "backlight":
                    reply = self.ir_backlight(data[2])

                else:
                    print(f"API: Received invalid command from {sreader.get_extra_info('peername')[0]}")
                    reply = 'Error: first arg must be one of: status, reboot, enable, disable, set_rule'

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



server = Api()
