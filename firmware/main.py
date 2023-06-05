import gc
import webrepl
import logging
import uasyncio as asyncio
from Config import Config
from SoftwareTimer import timer
from Api import app
from util import disk_monitor, read_config_from_disk

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

    # Disk_monitor deletes log when size limit exceeded, reboots when new code uploaded
    asyncio.create_task(disk_monitor())

    # Config loop rebuilds schedule rules when config_timer expires around 3am every day
    asyncio.create_task(config.loop())

    # Start API server, await requests
    asyncio.create_task(app.run())

    # Run main loop, controls device/sensor instances in config object
    asyncio.run(main(config))
