import gc
import asyncio
import logging
import webrepl
import app_context
from Api import Api
from Config import Config
from SoftwareTimer import SoftwareTimer
from util import read_config_from_disk, check_log_size

log = logging.getLogger("Main")


def async_exception_handler(loop, context):
    '''Log uncaught exceptions to disk before calling default handler'''
    log.error("UNCAUGHT ASYNC EXCEPTION: %s", context)
    loop.default_exception_handler(loop, context)


def start():
    '''Reads config.json from disk, instantiates Config class (connect to wifi,
    instantiate device/sensors, etc), starts webrepl, SoftwareTimer and Api.
    '''

    # Instantiate SoftwareTimer, add to shared context
    app_context.timer_instance = SoftwareTimer()

    # Instantiate config object (connects to wifi, sets up hardware, etc)
    try:
        app_context.config_instance = Config(read_config_from_disk())
    # Load blank config template if config.json does not exist (initial setup)
    except OSError:
        log.critical("config.json not found, loading blank template")
        from default_config import default_config  # pylint: disable=C0415
        app_context.config_instance = Config(default_config)
    gc.collect()

    # Start webrepl (OTA updates)
    webrepl.start()

    # Check if log exceeded 100 KB every 60 seconds
    app_context.timer_instance.create(60000, check_log_size, "check_log_size")

    # Get event loop, add custom exception handler that logs all uncaught
    # exceptions to disk before calling default exception handler
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(async_exception_handler)

    # Add SoftwareTimer loop (runs callbacks when timers expire)
    loop.create_task(app_context.timer_instance.loop())

    # Instantiate API backend
    app_context.api_instance = Api()
    gc.collect()
    # Start server and await requests
    loop.create_task(app_context.api_instance._run())  # pylint: disable=W0212

    # Run forever
    loop.run_forever()
