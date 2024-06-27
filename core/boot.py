import os
import gc
from flashbdev import bdev

# Mount filesystem (or format if first boot)
try:
    if bdev:
        os.mount(bdev, "/")
except OSError:
    import inisetup
    vfs = inisetup.setup()
gc.collect()


# Start main loop if config file exists
if "config.json" in os.listdir():
    from main import start
    start()
# Serve access point, wait for setup if no config file
else:
    from wifi_setup import serve_setup_page
    serve_setup_page()
