# IR Blaster Codes

This directory contains a python module for each IR device supported by the [IrBlaster class](devices/IrBlaster.py).

Each module contains a set of IR codes for a single target (such as a TV or air conditioner). This usually includes the codes sent by each key on the remote that came with the device.

## Syntax

Module names begin with the name of the IR target (snake case) followed by `_ir_codes.py`. Adding the name (without `_ir_codes.py`) to an ESP32 config file will cause the node to import the codes at boot.

Example:
```
  "ir_blaster": {
    "target": [
      "whynter_ac",
      "samsung_tv"
    ],
    "pin": "4"
  }
```
* This config will import `whynter_ac_ir_codes.py` and `samsung_tv_ir_codes.py`

Each module contains a single variable `codes` containing a dict with names of IR keys/functions as keys and lists of pulse/space timings as values. Note that these are the literal pulse/space durations in microseconds, not hex codes (this reduces latency since codes do not have to be converted at runtime by the ESP32). In many cases hex codes for a device can be found online and converted to pulse/space durations using the included [convert_ir_codes.py](CLI/convert_ir_codes.py) script (may need to change the address constant). Codes can also be recorded with LIRC on a device like a raspberry pi.

The ESP32 `ir_key` API endpoint takes a target name (eg `samsung_tv`) as the first argument and the name of one of the target's keys (eg `vol_up`) as the second argument. When a file is added to this directory and the firmware is rebuilt the filename (without `_ir_codes.py`) automatically becomes a valid target argument, and all keys in the dict become valid key arguments.

## Integration

Add the module to the [firmware manifest](firmware/manifest.py) to freeze it into the firmware (IR codes are not written to the ESP32 filesystem because they contain large objects and cause memory fragmentation when loaded into RAM). Syntax:
```
module("samsung_tv_ir_codes.py", base_path="../lib/ir_codes")
```

Integration with the CLI tools is fully automated. When a module is added to this directory its name (part before `_ir_codes.py`) will automatically appear as an option in the [config generator](CLI/config_generator.py) and [interactive API client](CLI/api_client.py), and all keys inside the module will appear as command options in the interactive API client (shown after the target is selected).

To integrate a new target with the webapp a react component that renders the remote UI must be added to [frontend/src/pages/api_card/IrRemotes.js](frontend/src/pages/api_card/IrRemotes.js). No changes are required for the config editor, the target name will appear automatically (with spaces instead of underscores and each word capitalized).
