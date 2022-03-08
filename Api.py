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

    async def run(self):
        print('\nRemote control: Awaiting client connection.\n')
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
                    for i in Config.config.sensors:
                        if i.name == data[1]:
                            print(f"API: Received command to disable {data[1]}, disabling...")
                            log.info(f"API: Received command to disable {data[1]}, enabling...")
                            i.disable()
                            reply = 'OK'

                    if not reply: # Detect if loop failed to find a match
                        reply = 'Error: Sensor not found'



                elif data[0] == "enable" and data[1].startswith("sensor"):
                    for i in Config.config.sensors:
                        if i.name == data[1]:
                            print(f"API: Received command to enable {data[1]}, enabling...")
                            log.info(f"API: Received command to enable {data[1]}, enabling...")
                            i.enable()
                            reply = 'OK'

                    if not reply: # Detect if loop failed to find a match
                        reply = 'Error: Sensor not found'



                elif data[0] == "set_rule" and data[1].startswith("sensor") or data[1].startswith("device"):
                    target = data[1]

                    if target.startswith("sensor"):
                        for i in Config.config.sensors:
                            if i.name == target:
                                print(f"API: Received command to set {target} delay to {data[2]} minutes, setting...")
                                try:
                                    i.current_rule = data[2]
                                    reply = 'OK'
                                except:
                                    reply = 'Error: Bad rule parameter, int required'

                    elif target.startswith("device"):
                        for i in Config.config.devices:
                            if i.name == target:
                                print(f"API: Received command to set {target} brightness to {data[2]}, setting...")
                                try:
                                    i.current_rule = data[2]
                                    reply = 'OK'
                                except:
                                    reply = 'Error: Bad rule parameter. Relay requires "on" or "off", all others require int'

                    else:
                        print(f"API: Received invalid command from {sreader.get_extra_info('peername')[0]}")
                        reply = 'Error: 2nd param must be name of a sensor or device - use status to see options'



                elif data[0] == "ir" and (data[1] == "tv" or data[1] == "ac"):
                    for i in Config.config.devices:
                        if i.device == "ir_blaster":
                            if not data[1] in i.codes:
                                reply = 'Error: No codes found for target "{}"'.format(data[1])
                            else:
                                if not data[2]:
                                    reply = 'Error: Please specify which key to simulate'
                                else:
                                    i.send(data[1], data[2])
                                    reply = 'OK'

                    if not reply:
                        reply = 'Error: No IR blaster configured'



                elif data[0] == "ir" and data[1] == "backlight":
                    if not (data[2] == "on" or data[2] == "off"):
                        reply = 'Error: Backlight setting must be "on" or "off"'
                    else:
                        for i in Config.config.devices:
                            if i.device == "ir_blaster":
                                i.backlight(data[2])
                                reply = 'OK'

                        if not reply:
                            reply = 'Error: No IR blaster configured'



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
