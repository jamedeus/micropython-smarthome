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


# Main loop - monitor sensors, apply actions if conditions met
async def main(config):
    while True:
        for group in config.groups:

            conditions = group.check_sensor_conditions()
            await asyncio.sleep(0)

            action = group.determine_correct_action(conditions)
            await asyncio.sleep(0)

            if action is None:
                # Skip to next group if no action required
                continue
            else:
                # Otherwise apply actions
                group.apply_action(action)

        # Must be >0 to avoid blocking webrepl.
        # Low values bottleneck webrepl speed, but this is acceptable since only used in maintenance
        await asyncio.sleep_ms(1)


def start_loop():
    # Instantiate config object (connects to wifi, sets up hardware, etc)
    config = Config(read_config_from_disk())
    gc.collect()

    # Start webrepl (OTA updates)
    webrepl.start()

    # Pass config object to API instance
    app.config = config

    # SoftwareTimer loop runs callbacks when timers expire (schedule rules, API, etc)
    asyncio.create_task(timer.loop())

    # Check if log exceeded 100 KB every 60 seconds
    timer.create(60000, check_log_size, "check_log_size")

    # Start API server, await requests
    asyncio.create_task(app.run())

    # Run main loop, controls device/sensor instances in config object
    asyncio.run(main(config))
