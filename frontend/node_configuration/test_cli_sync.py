from django.test import TestCase
from .models import ScheduleKeyword, Node, Config

# Large JSON objects, helper functions
from .unit_test_helpers import JSONClient, create_test_nodes, test_config_1


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

    def test_add_node(self):
        '''Endpoint should create Config and Node when payload is valid.'''

        # Confirm no Configs or Nodes exist
        Config.objects.all().delete()
        Node.objects.all().delete()
        self.assertEqual(len(Config.objects.all()), 0)
        self.assertEqual(len(Node.objects.all()), 0)

        # Post payload with valid IP and config JSON
        response = JSONClient().post(
            '/add_node',
            {
                'ip': '192.168.1.100',
                'config': test_config_1
            }
        )

        # Confirm correct response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            'Node created'
        )

        # Confirm added to database
        self.assertEqual(len(Config.objects.all()), 1)
        self.assertEqual(len(Node.objects.all()), 1)

        # Confirm config entry contains posted JSON
        config = Config.objects.all()[0]
        self.assertEqual(config.config, test_config_1)

        # Confirm reverse relation
        node = Node.objects.all()[0]
        self.assertEqual(config.node, node)
        self.assertEqual(node.config, config)

    def test_add_node_invalid_ip(self):
        '''Endpoint should return error when an invalid IP is received.'''

        # Post payload with invalid IP, valid config JSON
        response = JSONClient().post(
            '/add_node',
            {
                'ip': '192.168.1.999',
                'config': test_config_1
            }
        )

        # Confirm correct error
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            'Invalid IP 192.168.1.999'
        )

    def test_add_node_invalid_config(self):
        '''Endpoint should return error when an invalid IP is received.'''

        # Post payload with valid IP, invalid config JSON (missing metadata)
        response = JSONClient().post(
            '/add_node',
            {
                'ip': '192.168.1.100',
                'config': {
                    'device1': test_config_1['device1']
                }
            }
        )

        # Confirm correct error
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()['message'],
            'Missing required top-level metadata key'
        )

    def test_add_node_duplicate_name(self):
        '''Endpoint should create Config and Node when payload is valid.'''

        # Post payload with valid IP and config JSON of existing node
        response = JSONClient().post(
            '/add_node',
            {
                'ip': '192.168.1.100',
                'config': test_config_1
            }
        )

        # Confirm correct error
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            response.json()['message'],
            'Config already exists with identical name'
        )
