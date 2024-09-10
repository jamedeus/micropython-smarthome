import os
import gc
import logging
from flashbdev import bdev
try:
    from log_level import LOG_LEVEL
except ImportError:
    LOG_LEVEL = 'ERROR'

print("--------Booted--------")

# Mount filesystem (or format if first boot)
try:
    if bdev:
        os.mount(bdev, "/")
except OSError:
    import inisetup
    vfs = inisetup.setup()
gc.collect()

# Set log file and syntax
logging.basicConfig(
    level=logging._nameToLevel[LOG_LEVEL],
    filename='app.log',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    style='%'
)
log = logging.getLogger("Boot")
log.critical("Booted, log level: %s", LOG_LEVEL)


# Start main loop if wifi_credentials file exists
if "wifi_credentials.json" in os.listdir():
    from main import start
    start()
# Serve access point, wait for setup if no wifi_credentials
else:
    from wifi_setup import serve_setup_page
    serve_setup_page()
