'''Runs unit tests for tools in CLI/ directory.

Mocks cli_config.json contents and instantiates CliConfigManager before running
tests. Since CliConfigManager is a singleton the mocked instance will be reused
in all tests and the real cli_config.json file will not be read. This keeps the
environment consistent between machines with different cli_config.json contents
and CI/CD, which runs in docker and does not have cli_config.json.
'''

import json
import unittest
from unittest.mock import patch, mock_open, MagicMock
from cli_config_manager import CliConfigManager
from tests.cli.mock_cli_config import mock_cli_config

# Mock open builtin to return mock cli_config.json contents
# Prevents reading actual cli_config.json on dev machines, keeps tests
# consistent with CI/CD environment
mock_read_file = patch('cli_config_manager.open', mock_open(
    read_data=json.dumps(mock_cli_config)
))
mock_read_file.start()

# Mock requests.session to simulate successful django backend sync request
mock_session = patch('cli_config_manager.requests.session').start()
# Mock get method
mock_get = MagicMock()
mock_session.return_value.get = mock_get
# Mock get response
mock_response = MagicMock()
mock_get.return_value = mock_response
# Mock response contents (same as mock cli_config.json)
mock_response.status_code = 200
mock_response.json.return_value = {
    'status': 'success',
    'message': {
        'nodes': {
            'node1': '192.168.1.123',
            'node2': '192.168.1.234',
            'node3': '192.168.1.111'
        },
        'schedule_keywords': {
            'sunrise': '06:00',
            'sunset': '18:00',
            'sleep': '22:00'
        }
    }
}

# Instantiate CliConfigManager singleton with mocks active. Each time tests
# instantiate they will receive the same instance (singleton) with mock
# cli_config.json contents and initial sync request already complete.
CliConfigManager()

# Stop mocks before running tests
mock_read_file.stop()
mock_session.stop()

# Discover tests in tests/cli, run
loader = unittest.TestLoader()
suite = loader.discover('tests/cli')
runner = unittest.TextTestRunner()
result = runner.run(suite)

if result.wasSuccessful():
    raise SystemExit(0)
raise SystemExit(1)
