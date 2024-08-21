'''Mock cli_config.json contents used by CLI unit tests'''

import os
import json
import tempfile

# Create temp directory where files will be written during tests
temp_dir = os.path.join(tempfile.gettempdir(), 'smarthome_cli_unit_tests')
if not os.path.exists(temp_dir):
    os.mkdir(temp_dir)

# Create mock CLI directory (mock to replace <repo>/CLI)
mock_cli_dir = os.path.join(temp_dir, 'CLI')
if not os.path.exists(mock_cli_dir):
    os.mkdir(mock_cli_dir)

# Create mock system config directory (mock to replace ~/.config)
mock_system_config_dir = os.path.join(temp_dir, 'system_config')
if not os.path.exists(mock_system_config_dir):
    os.mkdir(mock_system_config_dir)

# Create mock app config directory (mock to replace ~/.config/smarthome_cli)
mock_smarthome_config_dir = os.path.join(mock_system_config_dir, 'smarthome_cli')
if not os.path.exists(mock_smarthome_config_dir):
    os.mkdir(mock_smarthome_config_dir)

# Create mock ESP32 config directory (mock to replace ~/.config/config_files)
mock_config_dir = os.path.join(mock_system_config_dir, 'config_files')
if not os.path.exists(mock_config_dir):
    os.mkdir(mock_config_dir)

# Create mock ~/.config/smarthome_cli/cli_config.json contents
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


# Write mock cli_config.json to disk (in temp directory)
mock_cli_config_path = os.path.join(mock_smarthome_config_dir, 'cli_config.json')
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
