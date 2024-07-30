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


# Start main loop if wifi_credentials file exists
if "wifi_credentials.json" in os.listdir():
    from main import start
    start()
# Serve access point, wait for setup if no wifi_credentials
else:
    from wifi_setup import serve_setup_page
    serve_setup_page()
