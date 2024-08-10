'''Mock cli_config.json contents used by CLI unit tests'''

import os

# Get path to config_dir
cli = os.path.dirname(os.path.realpath(__file__))
tests = os.path.split(cli)[0]
repo = os.path.dirname(tests)
config_dir = os.path.join(repo, 'config_files')

mock_cli_config = {
    'nodes': {
        'node1': '192.168.1.123',
        'node2': '192.168.1.234',
        'node3': '192.168.1.111'
    },
    'schedule_keywords': {
        'sunrise': '06:00',
        'sunset': '18:00',
        'sleep': '22:00'
    },
    'webrepl_password': 'password',
    'config_directory': config_dir,
    'django_backend': 'http://192.168.1.100'
}

# Create config directory if it doesn't exist
if not os.path.exists(mock_cli_config['config_directory']):
    os.mkdir(mock_cli_config['config_directory'])
