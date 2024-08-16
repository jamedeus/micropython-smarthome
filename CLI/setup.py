import os
import glob
import shutil
import setuptools

# Get path to util module
cli = os.path.dirname(os.path.realpath(__file__))
repo = os.path.split(cli)[0]
util_path = os.path.join(repo, 'util')

setuptools.setup(
    name='smarthome_cli',
    version='0.1.0',
    py_modules=[
        'api_client',
        'cli_config_manager',
        'config_generator',
        'config_prompt_validators',
        'config_rule_prompts',
        'provision',
        'smarthome_cli',
    ],
    install_requires=[
        'questionary==2.0.1',
        'colorama==0.4.3',
        'requests==2.32.3',
        f'util @ file://{util_path}',
    ],
    entry_points={
        'console_scripts': [
            'smarthome_cli=smarthome_cli:main_prompt',
        ],
    },
)

# Remove metadata clutter
for i in glob.glob('*.egg-info'):
    shutil.rmtree(i)
