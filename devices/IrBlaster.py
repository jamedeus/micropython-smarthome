import asyncio
import logging
from machine import Pin
from ir_tx import Player
from ir_code_classes import ir_code_classes
from util import read_ir_macros_from_disk, write_ir_macros_to_disk, print_with_timestamp


class IrBlaster():
    '''Driver for MOSFET connected to IR LED used to replay recorded IR codes.
    Supports replaying codes for individual IR remote buttons or macros with
    multiple button presses and configurable delays between each button.

    Args:
      pin:     The ESP32 pin connected to the mosfet
      target:  List containing names of one or more IR target devices

    Codes for supported IR target devices are in lib/ir_codes. These are frozen
    into firmware and automatically imported based the target argument. Each
    module contains pulse/space timings in microseconds that control how long
    the IR LED is turned on and off to simulate each key. The frontend will
    display a remote control UI element for each configured IR target.

    A maximum of 1 IrBlaster can be configured per ESP32 (upstream driver
    limitation). Unlike other device drivers IrBlaster can not be targeted by
    sensors - IR codes and macros are only played in response to API calls. It
    is possible to circumvent this by configuring an ApiTarget device with the
    node's own IP (or 127.0.0.1) that sends IR API calls when turned on/off by
    a sensor. This allows multiple sensors to send different IR codes despite
    the 1 IrBlaster limitation.
    '''

    def __init__(self, pin, target):
        # Set name for module's log lines
        self.log = logging.getLogger("IrBlaster")

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

        self.log.info("Instantiated IrBlaster on pin %s", pin)

    def populate_codes(self, target):
        '''Takes target name, imports codes and adds to self.codes dict.'''

        if target not in ir_code_classes.keys():
            self.log.error("Unsupported IR target %s", target)
            raise ValueError(f'Unsupported IR target "{target}"')

        module = __import__(ir_code_classes[target])
        self.codes[target] = getattr(module, 'codes')

    def send(self, dev, key):
        '''Takes IR target name and key, plays IR code.'''

        self.log.debug("IrBlaster: Sending IR key %s to %s", key, dev)
        print_with_timestamp(f"IrBlaster: Sending IR key {key} to {dev}")
        try:
            self.ir.play(self.codes[dev.lower()][key.lower()])
            self.log.debug("IrBlaster: Send success")
            print_with_timestamp("IrBlaster: Send success")
            return True
        except (KeyError, AttributeError):
            self.log.error("IrBlaster: Send fail")
            print_with_timestamp("IrBlaster: Send fail")
            return False

    def get_existing_macros(self):
        '''Returns dict of existing macros formatted for readability.'''

        response = {}
        for macro in self.macros:
            response[macro] = []
            for action in self.macros[macro]:
                # Convert each action list to string
                # Keeps each action on 1 line in printed json output
                response[macro].append(' '.join(map(str, action)))
        return response

    def create_macro(self, name):
        '''Takes new macro name, creates a new key in self.macros containing an
        empty list. Raises ValueError if the macro name already exists.
        '''
        if name not in self.macros.keys():
            self.log.debug("IrBlaster.create_macro: creating macro named %s", name)
            self.macros[name] = []
        else:
            self.log.error("IrBlaster.create_macro: macro named %s already exists", name)
            raise ValueError(f"Macro named {name} already exists")

    def delete_macro(self, name):
        '''Takes name of existing macro, removes from self.macros. Raises
        ValueError if the macro name does not exist.
        '''
        if name in self.macros.keys():
            self.log.debug("IrBlaster.delete_macro: deleting macro %s", name)
            del self.macros[name]
        else:
            self.log.error("IrBlaster.delete_macro: macro named %s does not exist", name)
            raise ValueError(f"Macro named {name} does not exist")

    def save_macros(self):
        '''Writes current IR macros to ir_macros.json on disk.'''

        write_ir_macros_to_disk(self.macros)

    def add_macro_action(self, name, target, key, delay=0, repeat=1):
        '''Add a single action to an existing macro in self.macros
        Required args: Existing macro name, IR target name, IR key name.
        Optional: Delay (ms) after replaying code for IR key.
        Optional: Repeat (number of times the code is replayed). The delay, if
                  configured, is repeated after each repeat.
        '''
        self.log.debug(
            "IrBlaster: add_macro_action args: name=%s, target=%s, key=%s, delay=%s, repeat=%s",
            name, target, key, delay, repeat
        )

        # Validation
        if name not in self.macros:
            self.log.error("IrBlaster.add_macro_action: macro named %s does not exist", name)
            raise ValueError(f"Macro {name} does not exist, use create_macro to add")
        if target not in self.codes:
            self.log.error("IrBlaster.add_macro_action: no codes for %s", target)
            raise ValueError(f"No codes for {target}")
        if key not in self.codes[target]:
            self.log.error("IrBlaster.add_macro_action: target %s has no key %s", target, key)
            raise ValueError(f"Target {target} has no key {key}")
        try:
            delay = int(delay)
        except ValueError:
            self.log.error("IrBlaster.add_macro_action: delay arg must be integer")
            raise ValueError("Delay arg must be integer (milliseconds)")  # pylint: disable=W0707
        try:
            repeat = int(repeat)
        except ValueError:
            self.log.error("IrBlaster.add_macro_action: repeat arg must be integer")
            raise ValueError("Repeat arg must be integer (number of times to press key)")  # pylint: disable=W0707

        # Add action
        self.macros[name].append((target, key, delay, repeat))
        self.log.debug("IrBlaster.add_macro_action: action added")

    def run_macro(self, name):
        '''Takes name of existing macro, runs all actions in async coroutine to
        avoid blocking API response if macro contains long delays.'''

        if name not in self.macros.keys():
            self.log.error("IrBlaster.run_macro: macro named %s does not exist", name)
            raise ValueError(f"Macro {name} does not exist, use create_macro to add")

        # Run macro
        self.log.debug("IrBlaster.run_macro: running %s", name)
        asyncio.run(self.run_macro_coro(name))

    async def run_macro_coro(self, name):
        '''Async coroutine called by run_macro. Takes name of existing macro,
        runs all actions.
        '''
        self.log.debug("IrBlaster: run macro coro start")
        # Iterate actions and run each action
        for action in self.macros[name]:
            for _ in range(0, int(action[3])):
                self.send(action[0], action[1])
                await asyncio.sleep_ms(int(action[2]))
        self.log.debug("IrBlaster: run macro coro end")
