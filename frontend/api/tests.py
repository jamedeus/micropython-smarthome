from django.test import TestCase
from django.conf import settings

from node_configuration.models import *
from node_configuration.unit_test_helpers import create_test_nodes, clean_up_test_nodes, create_config_and_node_from_json, test_config_1, test_config_2, test_config_3
from .models import Macro

import json



# Test legacy api page
class LegacyApiTests(TestCase):
    def test_legacy_api_page(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/legacy_api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/legacy_api.html')

        # Confirm context contains correct number of nodes
        self.assertEqual(len(response.context['context']), 3)

        # Confirm one button for each node
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test1">Test1</button>')
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test2">Test2</button>')
        self.assertContains(response, '<button onclick="select_node(this)" type="button" class="select_node btn btn-primary m-1" id="Test3">Test3</button>')



# Test api overview page
class OverviewPageTests(TestCase):
    def test_overview_page_no_nodes(self):
        # Request page, confirm correct template used
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm correct context (empty template)
        self.assertEqual(response.context['nodes'], {})
        self.assertEqual(response.context['macros'], {})

        # Confirm no floor or macro sections
        self.assertNotContains(response, '<div id="floor1" class="section mt-3 mb-4 p-3">')
        self.assertNotContains(response, '<h1 class="text-center mt-5">Macros</h1>')

        # Confirm link to create first node
        self.assertContains(response, '<h2>No Nodes Configured</h2>')
        self.assertContains(response, '<p>Click <a href="/new_config">here</a> to create</p>')

    def test_overview_page_with_nodes(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page, confirm correct template used
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm context contains correct number of nodes on each floor
        self.assertEqual(len(response.context['nodes'][1]), 2)
        self.assertEqual(len(response.context['nodes'][2]), 1)
        self.assertEqual(response.context['macros'], {})

        # Confirm floor and macro sections both present
        self.assertContains(response, '<div id="floor1" class="section mt-3 mb-4 p-3">')
        self.assertContains(response, '<h1 class="text-center mt-5">Macros</h1>')

        # Confirm no link to create node
        self.assertNotContains(response, '<h2>No Nodes Configured</h2>')
        self.assertNotContains(response, '<p>Click <a href="/new_config">here</a> to create</p>')

    def test_overview_page_with_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Expected macro context object
        test_macro_context = {'test macro': [{'ip': '192.168.1.123', 'args': ['trigger_sensor', 'sensor1'], 'node_name': 'Test1', 'target_name': 'Motion Sensor', 'action_name': 'Trigger Sensor'}, {'ip': '192.168.1.123', 'args': ['disable', 'device1'], 'node_name': 'Test1', 'target_name': 'Cabinet Lights', 'action_name': 'Disable'}, {'ip': '192.168.1.123', 'args': ['enable', 'device2'], 'node_name': 'Test1', 'target_name': 'Overhead Lights', 'action_name': 'Enable'}]}

        # Create macro with same actions as expected context
        Macro.objects.create(name='Test Macro', actions=json.dumps(test_macro_context['test macro']))

        # Request page, confirm correct template used, confirm context contains macro
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')
        self.assertEqual(response.context['macros'], test_macro_context)

        # Confirm macro section present with correct-name macro
        self.assertContains(response, '<h1 class="text-center mt-5">Macros</h1>')
        self.assertContains(response, '<h3 class="mx-auto my-auto">Test Macro</h3>')

    def test_overview_page_record_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page with params to start recording macro named "New Macro Name"
        response = self.client.get('/api/recording/New Macro Name/start')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm context includes correct variables
        self.assertEqual(response.context['recording'], 'New Macro Name')
        self.assertEqual(response.context['start_recording'], True)

        # Confirm contains instructions modal
        self.assertContains(response, '<h3 class="mx-auto mb-0" id="error-modal-title">Macro Instructions</h3>')

        # Set cookie to skip instructions (checkbox in popup), request page again
        self.client.cookies['skip_instructions'] = 'true'
        response = self.client.get('/api/recording/New Macro Name/start')
        self.assertEqual(response.status_code, 200)

        # Should not contain instructions modal, context should include skip_instructions variable
        self.assertNotContains(response, '<h3 class="mx-auto mb-0" id="error-modal-title">Macro Instructions</h3>')
        self.assertEqual(response.context['skip_instructions'], True)
