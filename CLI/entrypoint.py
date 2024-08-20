'''Entrypoint for smarthome_cli command (available after installing CLI tools).

Wrapper adds util and CLI packages to path and runs smarthome_cli.main_prompt
(expects util and CLI modules to be importable without relative paths).

Not necessary in development (pipenv adds util to path).
'''

import os
import sys

# Add util and CLI modules to python path
cli = os.path.dirname(os.path.abspath(__file__))
util = os.path.join(cli, '../util')
sys.path.insert(0, util)
sys.path.insert(0, cli)


def main():
    '''Runs smarthome_cli main prompt, exits if KeyboardInterrupt raised'''
    try:
        from smarthome_cli.CLI.smarthome_cli import main_prompt
        main_prompt()
    except KeyboardInterrupt as interrupt:
        raise SystemExit from interrupt
