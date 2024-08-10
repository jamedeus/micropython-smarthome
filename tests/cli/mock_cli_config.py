'''Mock cli_config.json contents used by CLI unit tests'''

import os
import json
import tempfile

# Create temp directory to write config files to
temp_dir = tempfile.gettempdir()

# Get path to mock config_directory
mock_config_dir = os.path.join(temp_dir, 'config_files')

# Get path to mock CLI dir
mock_cli_dir = os.path.join(temp_dir, 'CLI')

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
    'config_directory': mock_config_dir,
    'django_backend': 'http://192.168.1.100'
}

# Create mock config directory if it doesn't exist
if not os.path.exists(mock_cli_config['config_directory']):
    os.mkdir(mock_cli_config['config_directory'])

# Create mock CLI directory if it doesn't exist
if not os.path.exists(mock_cli_dir):
    os.mkdir(mock_cli_dir)

# Create mock cli_config.json on disk
mock_cli_config_path = os.path.join(mock_cli_dir, 'cli_config.json')
with open(mock_cli_config_path, 'w', encoding='utf-8') as file:
    json.dump(mock_cli_config, file)

# Create mock config files for each node in mock cli_config.json
node1_config = os.path.join(mock_config_dir, 'node1.json')
if not os.path.exists(node1_config):
    with open(node1_config, 'w', encoding='utf-8') as file:
        json.dump({'metadata': {'id': 'Node1'}}, file)
node2_config = os.path.join(mock_config_dir, 'node2.json')
if not os.path.exists(node2_config):
    with open(node2_config, 'w', encoding='utf-8') as file:
        json.dump({'metadata': {'id': 'Node2'}}, file)
node3_config = os.path.join(mock_config_dir, 'node3.json')
if not os.path.exists(node3_config):
    with open(node3_config, 'w', encoding='utf-8') as file:
        json.dump({'metadata': {'id': 'Node3'}}, file)
