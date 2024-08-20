'''Globally installs CLI tools, dependencies needed to provision ESP32 nodes.

Creates a single package called smarthome_cli under site-packages with sub-
packages containing CLI, core, devices, sensors, and util modules.

Interactive menu can be opened by calling `smarthome_cli` after install.
'''

import os
import glob
import shutil
import setuptools

# Get path to CLI and util packages
repo = os.path.dirname(os.path.realpath(__file__))
cli_path = os.path.join(repo, 'CLI')
util_path = os.path.join(repo, 'util')

setuptools.setup(
    name='smarthome_cli',
    version='0.1.0',
    packages=[
        'smarthome_cli.CLI',
        'smarthome_cli.core',
        'smarthome_cli.devices',
        'smarthome_cli.sensors',
        'smarthome_cli.util',
    ],
    package_dir={
        'smarthome_cli.CLI': 'CLI',
        'smarthome_cli.core': 'core',
        'smarthome_cli.devices': 'devices',
        'smarthome_cli.sensors': 'sensors',
        'smarthome_cli.util': 'util',
    },
    package_data={
        'smarthome_cli.util': [
            'metadata/devices/*.json',
            'metadata/sensors/*.json',
        ],
    },
    include_package_data=True,
    install_requires=[
        'questionary==2.0.1',
        'colorama==0.4.3',
        'requests==2.32.3',
    ],
    entry_points={
        'console_scripts': [
            'smarthome_cli=smarthome_cli.CLI.entrypoint:main',
        ],
    }
)

# Remove metadata clutter
for i in glob.glob('*.egg-info'):
    shutil.rmtree(i)
