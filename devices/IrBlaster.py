import asyncio
import logging
from machine import Pin
from ir_tx import Player
from util import read_ir_macros_from_disk, write_ir_macros_to_disk, print_with_timestamp
from ir_code_classes import ir_code_classes

# Set name for module's log lines
log = logging.getLogger("IrBlaster")


class IrBlaster():
    def __init__(self, pin, target):
        led = Pin(int(pin), Pin.OUT, value=0)
        self.ir = Player(led)
        self.target = target
        self._type = "ir_blaster"

        # Add codes for each device in target list
        self.codes = {}
        for target in self.target:
            self.populate_codes(target)

        # Read ir_macros.json from disk (returns {} if file not found)
        # Dict with macro names as key, list of actions as value
        self.macros = read_ir_macros_from_disk()

        log.info(f"Instantiated IrBlaster on pin {pin}")

    # Takes target name, imports codes and adds to self.codes dict
    def populate_codes(self, target):
        if target not in ir_code_classes.keys():
            raise ValueError(f'Unsupported IR target "{target}"')

        module = __import__(ir_code_classes[target])
        self.codes[target] = getattr(module, 'codes')

    def send(self, dev, key):
        print_with_timestamp(f"IR Blaster: Sending IR key {key} to {dev}")
        try:
            self.ir.play(self.codes[dev.lower()][key.lower()])
            print_with_timestamp("IR Blaster: Send success")
            return True
        except (KeyError, AttributeError):
            print_with_timestamp("IR Blaster: Send fail")
            return False

    # Returns dict of existing macros formatted for readability
    def get_existing_macros(self):
        response = {}
        for macro in self.macros:
            response[macro] = []
            for action in self.macros[macro]:
                # Convert each action list to string
                # Keeps each action on 1 line in printed json output
                response[macro].append(' '.join(map(str, action)))
        return response

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

    # Write current macros to ir_macros.json on disk
    def save_macros(self):
        write_ir_macros_to_disk(self.macros)

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
        print_with_timestamp("IR Blaster: run macro coro start")
        # Iterate actions and run each action
        for action in self.macros[name]:
            for i in range(0, int(action[3])):
                self.send(action[0], action[1])
                await asyncio.sleep_ms(int(action[2]))
        print_with_timestamp("IR Blaster: run macro coro end")
