import logging
from machine import Pin
from ir_tx import Player
import uasyncio as asyncio
from util import read_config_from_disk, write_config_to_disk

# Set name for module's log lines
log = logging.getLogger("IrBlaster")


class IrBlaster():
    def __init__(self, pin, target, macros):
        led = Pin(int(pin), Pin.OUT, value=0)
        self.ir = Player(led)
        self.target = target
        self._type = "ir_blaster"

        self.codes = {}

        # Dict with macro names as key, list of actions as value
        self.macros = macros

        if "tv" in self.target:
            from ir_codes import samsung
            self.codes["tv"] = samsung

        if "ac" in self.target:
            from ir_codes import whynter
            self.codes["ac"] = whynter

        log.info(f"Instantiated IrBlaster on pin {pin}")

    def send(self, dev, key):
        try:
            self.ir.play(self.codes[dev.lower()][key.lower()])
            return True
        except (KeyError, AttributeError):
            return False

    # Creates a new key in self.macros
    def create_macro(self, name):
        if name not in self.macros.keys():
            self.macros[name] = []
        else:
            raise ValueError(f"Macro named {name} already exists")

    # Takes name of existing macro, removes from self.macros
    def delete_macro(self, name):
        if name in self.macros.keys():
            del self.macros[name]
        else:
            raise ValueError(f"Macro named {name} does not exist")

    # Write current macros to config file on disk
    def save_macros(self):
        config = read_config_from_disk()
        config['ir_blaster']['macros'] = self.macros
        write_config_to_disk(config)

    # Add a single action to an existing key in self.macros
    # Required args: Macro name, IR target, IR key
    # Optional: Delay (ms) after sending key
    # Optional: Repeat (number of times key is pressed, delay applied after each)
    def add_macro_action(self, name, target, key, delay=0, repeat=1):
        # Validation
        if name not in self.macros.keys():
            raise ValueError(f"Macro {name} does not exist, use create_macro to add")
        if target not in self.codes.keys():
            raise ValueError(f"No codes for {target}")
        if key not in self.codes[target]:
            raise ValueError(f"Target {target} has no key {key}")
        try:
            delay = int(delay)
        except ValueError:
            raise ValueError("Delay arg must be integer (milliseconds)")
        try:
            repeat = int(repeat)
        except ValueError:
            raise ValueError("Repeat arg must be integer (number of times to press key)")

        # Add action
        self.macros[name].append((target, key, delay, repeat))

    # Takes macro name, creates async coroutine to run macro
    def run_macro(self, name):
        if name not in self.macros.keys():
            raise ValueError(f"Macro {name} does not exist, use create_macro to add")

        # Run macro
        asyncio.run(self.run_macro_coro(name))

    # Takes macro name, runs
    async def run_macro_coro(self, name):
        # Iterate actions and run each action
        for action in self.macros[name]:
            for i in range(0, int(action[3])):
                self.send(action[0], action[1])
                await asyncio.sleep_ms(int(action[2]))
