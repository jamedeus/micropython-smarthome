from django.test import TestCase
from .models import ScheduleKeyword

# Large JSON objects, helper functions
from .unit_test_helpers import create_test_nodes, test_config_1


class CliSyncTests(TestCase):
    '''Tests endpoints called by CLI tools to update cli_config.json'''

    def setUp(self):
        # Create 3 test nodes and configs to edit
        create_test_nodes()

        # Create 2 test schedule keywords
        ScheduleKeyword.objects.create(keyword='morning', timestamp='08:00')
        ScheduleKeyword.objects.create(keyword='sleep', timestamp='23:30')

    def test_get_nodes(self):
        '''Endpoint should return a dict with all node names as keys, dict
        containing IP address as values.
        '''
        response = self.client.get('/get_nodes')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            {
                'test1': '192.168.1.123',
                'test2': '192.168.1.124',
                'test3': '192.168.1.125',
            }
        )

    def test_get_schedule_keywords(self):
        '''Endpoint should return a dict with all schedule keywords as keys,
        timestamps as values.
        '''
        response = self.client.get('/get_schedule_keywords')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            {
                'morning': '08:00',
                'sleep': '23:30',
                'sunrise': '06:00',
                'sunset': '18:00'
            }
        )

    def test_get_node_config(self):
        '''Endpoint should return JSON config file matching requested IP.'''
        response = self.client.get('/get_node_config/192.168.1.123')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], test_config_1)

    def test_get_node_config_does_not_exist(self):
        '''Endpoint should return error if requested IP not found.'''
        response = self.client.get('/get_node_config/192.168.1.99')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()['message'],
            'Node with IP 192.168.1.99 not found'
        )
