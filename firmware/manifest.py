include("$(PORT_DIR)/boards/manifest.py")
require("functools")
require("unittest")

# Core modules
module("Api.py", base_path="../core")
module("boot.py", base_path="../core")
module("Config.py", base_path="../core")
module("Group.py", base_path="../core")
module("main.py", base_path="../core")
module("SoftwareTimer.py", base_path="../core")
module("util.py", base_path="../core")
module("wifi_setup.py", base_path="../core")
module("Instance.py", base_path="../core")

# Device driver modules
module("ApiTarget.py", base_path="../devices")
module("DesktopTarget.py", base_path="../devices")
module("Device.py", base_path="../devices")
module("DimmableLight.py", base_path="../devices")
module("DumbRelay.py", base_path="../devices")
module("IrBlaster.py", base_path="../devices")
module("LedStrip.py", base_path="../devices")
module("Mosfet.py", base_path="../devices")
module("TasmotaRelay.py", base_path="../devices")
module("Tplink.py", base_path="../devices")
module("Wled.py", base_path="../devices")

# Sensor driver modules
module("DesktopTrigger.py", base_path="../sensors")
module("Dummy.py", base_path="../sensors")
module("Ld2410.py", base_path="../sensors")
module("LoadCell.py", base_path="../sensors")
module("MotionSensor.py", base_path="../sensors")
module("Sensor.py", base_path="../sensors")
module("Switch.py", base_path="../sensors")
module("Thermostat.py", base_path="../sensors")

# System libraries
module("logging.py", base_path="../lib")
module("testing.py", base_path="../lib")
module("cpython_only.py", base_path="../lib")

# Hardware driver libraries
package("ir_tx", base_path="../lib")
module("si7021.py", base_path="../lib")
module("hx711.py", base_path="../lib")

# Configuration constants
module("api_keys.py", base_path="../lib")
module("setup_ssl_certs.py", base_path=".")
module("default_config.py", base_path="../lib")
module("hardware_classes.py", base_path="../lib")
module("samsung_ir_codes.py", base_path="../lib")
module("whynter_ir_codes.py", base_path="../lib")
