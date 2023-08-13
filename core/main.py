import gc
import webrepl
import logging
import uasyncio as asyncio
from Api import app
from Config import Config
from SoftwareTimer import timer
from util import read_config_from_disk, check_log_size

print("--------Booted--------")

# Set log file and syntax
logging.basicConfig(
    level=logging.DEBUG,
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    style='%'
)
log = logging.getLogger("Main")
log.info("Booted")


def start_loop():
    # Instantiate config object (connects to wifi, sets up hardware, etc)
    config = Config(read_config_from_disk())
    gc.collect()

    # Start webrepl (OTA updates)
    webrepl.start()

    # Pass config object to API instance
    app.config = config

    # Check if log exceeded 100 KB every 60 seconds
    timer.create(60000, check_log_size, "check_log_size")

    # Get event loop, add tasks, run forever
    loop = asyncio.get_event_loop()

    # SoftwareTimer loop runs callbacks when timers expire (schedule rules, API, etc)
    loop.create_task(timer.loop())

    # Start API server, await requests
    loop.create_task(app.run())
    loop.run_forever()
