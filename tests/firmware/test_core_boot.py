import os
import sys
import unittest
from cpython_only import cpython_only

# Import dependencies for tests that only run in mocked environment
if sys.implementation.name == 'cpython':
    import types
    from unittest.mock import patch, MagicMock


class TestBoot(unittest.TestCase):

    @cpython_only
    def setUp(self):
        # Create mock os with missing mount method (doesn't exist in cpython)
        self.mock_os = types.ModuleType('os')
        self.mock_os.mount = MagicMock(return_value=None)
        self.mock_os.listdir = os.listdir
        self.mock_os.remove = os.remove
        self.mock_os.path = os.path

    @cpython_only
    def test_boot_wifi_credentials_exist(self):
        # Mock start and serve_setup_page to confirm correct function called
        # Mock os module to add missing mount method
        with patch('main.start', MagicMock()) as mock_start, \
             patch('wifi_setup.serve_setup_page', MagicMock()) as mock_serve_setup, \
             patch.dict('sys.modules', {'os': self.mock_os}):

            # Import boot.py (runs immediately without checking __name__)
            import boot

            # Confirm that main.start was called, serve_setup_page was NOT called
            mock_start.assert_called_once()
            mock_serve_setup.assert_not_called()

    @cpython_only
    def test_boot_missing_wifi_credentials(self):
        # Simulate empty filesystem (no wifi_credentials.json)
        self.mock_os.listdir = MagicMock(return_value=[])

        # Mock start and serve_setup_page to confirm correct function called
        # Mock os module to add missing mount method
        with patch('main.start', MagicMock()) as mock_start, \
             patch('wifi_setup.serve_setup_page', MagicMock()) as mock_serve_setup, \
             patch.dict('sys.modules', {'os': self.mock_os}):

            # Import boot.py (runs immediately without checking __name__)
            import boot

            # Confirm serve_setup_page was called, main.start was NOT called
            mock_serve_setup.assert_called_once()
            mock_start.assert_not_called()
