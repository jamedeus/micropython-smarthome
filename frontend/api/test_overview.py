import json
from unittest.mock import patch
from django.test import TestCase
from django.db import IntegrityError
from .models import Macro
from node_configuration.unit_test_helpers import (
    create_test_nodes,
    JSONClient
)


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

    def test_overview_page_with_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Expected macro context object
        test_macro_context = {
            "test macro": [
                {
                    "ip": "192.168.1.123",
                    "args": [
                        "trigger_sensor",
                        "sensor1"
                    ],
                    "node_name": "Test1",
                    "target_name": "Motion Sensor",
                    "action_name": "Trigger Sensor"
                },
                {
                    "ip": "192.168.1.123",
                    "args": [
                        "disable",
                        "device1"
                    ],
                    "node_name": "Test1",
                    "target_name": "Cabinet Lights",
                    "action_name": "Disable"
                },
                {
                    "ip": "192.168.1.123",
                    "args": [
                        "enable",
                        "device2"
                    ],
                    "node_name": "Test1",
                    "target_name": "Overhead Lights",
                    "action_name": "Enable"
                }
            ]
        }

        # Create macro with same actions as expected context
        Macro.objects.create(
            name='Test Macro',
            actions=json.dumps(test_macro_context['test macro'])
        )

        # Request page, confirm correct template used, confirm context contains macro
        response = self.client.get('/api')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')
        self.assertEqual(response.context['macros'], test_macro_context)

    def test_overview_page_record_macro(self):
        # Create 3 test nodes
        create_test_nodes()

        # Request page with params to start recording macro named "New Macro Name"
        response = self.client.get('/api/recording/New Macro Name')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'api/overview.html')

        # Confirm context includes correct variables
        self.assertEqual(response.context['recording'], 'New Macro Name')

        # Set cookie to skip instructions (checkbox in popup), request page again
        self.client.cookies['skip_instructions'] = 'true'
        response = self.client.get('/api/recording/New Macro Name')
        self.assertEqual(response.status_code, 200)


# Test actions in overview top-right dropdown menu
class TestGlobalCommands(TestCase):
    def setUp(self):
        create_test_nodes()

    def test_reset_all(self):
        # Mock request to return expected response for each node
        expected_response = {
            'device1': 'Reverted to scheduled rule',
            'current_rule': 'disabled'
        }
        with patch('api_endpoints.request', return_value=expected_response):
            response = self.client.get('/reset_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

    def test_reset_all_offline(self):
        # Mock request to simulate offline nodes
        with patch('api_endpoints.asyncio.open_connection', side_effect=OSError):
            response = self.client.get('/reset_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

    def test_reboot_all(self):
        # Mock request to return expected response for each node
        with patch('api_endpoints.request', return_value='Rebooting'):
            response = self.client.get('/reboot_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")

    def test_reboot_all_offline(self):
        # Mock request to simulate offline nodes
        with patch('api_endpoints.asyncio.open_connection', side_effect=OSError):
            response = self.client.get('/reboot_all')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], "Done")


# Test endpoint that sets cookie to skip macro instructions modal
class SkipInstructionsTests(TestCase):
    def test_get_skip_instructions_cookie(self):
        response = self.client.get('/skip_instructions')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('skip_instructions' in response.cookies)
        self.assertEqual(response.cookies['skip_instructions'].value, 'true')


# Test model that stores and plays recorded macros
class MacroModelTests(TestCase):
    def setUp(self):
        # Create 3 test nodes
        create_test_nodes()

        # Payloads to macro actions
        self.set_rule_action = {
            "command": "set_rule",
            "instance": "device1",
            "rule": "248",
            "target": "192.168.1.123",
            "friendly_name": "Countertop LEDs"
        }

        self.turn_on_action = {
            "command": "turn_on",
            "instance": "device1",
            "target": "192.168.1.123",
            "friendly_name": "Countertop LEDs"
        }

        self.turn_off_action = {
            "command": "turn_off",
            "instance": "device1",
            "target": "192.168.1.123",
            "friendly_name": "Countertop LEDs"
        }

    # Test instantiation, name standardization, __str__ method
    def test_instantiation(self):
        # Confirm no Macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Create with capitalized name, should convert to lowercase
        macro = Macro.objects.create(name='New Macro')
        macro.refresh_from_db()
        self.assertEqual(macro.name, 'new macro')
        self.assertEqual(macro.__str__(), 'New Macro')

        # Create with underscore and hyphen, should replace with spaces
        macro = Macro.objects.create(name='new-macro-name')
        macro.refresh_from_db()
        self.assertEqual(macro.name, 'new macro name')
        self.assertEqual(macro.__str__(), 'New Macro Name')

        # Create with numbers, should cast to string
        macro = Macro.objects.create(name=1337)
        macro.refresh_from_db()
        self.assertEqual(macro.name, '1337')
        self.assertEqual(macro.__str__(), '1337')

        # Confirm 3 macros created
        self.assertEqual(len(Macro.objects.all()), 3)

    # Should refuse to create the same name twice
    def test_no_duplicate_names(self):
        with self.assertRaises(IntegrityError):
            Macro.objects.create(name='New Macro')
            Macro.objects.create(name='New Macro')

    # Should refuse to create an empty name
    def test_no_empty_names(self):
        with self.assertRaises(IntegrityError):
            Macro.objects.create(name='')

    def test_add_and_delete_action(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add action, confirm 1 action exists, confirm value correct
        macro.add_action(self.turn_off_action)
        actions = json.loads(macro.actions)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0], {
            "ip": "192.168.1.123",
            "args": [
                "turn_off",
                "device1"
            ],
            "node_name": "Test1",
            "target_name": "Countertop LEDs",
            "action_name": "Turn Off"
        })

        # Delete the just-created action, confirm removed
        macro.del_action(0)
        actions = json.loads(macro.actions)
        self.assertEqual(len(actions), 0)

    def test_add_action_invalid(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Attempt to add incomplete action (args only, no containing dict)
        with self.assertRaises(SyntaxError):
            macro.add_action(['turn_on', 'device1'])

        # Attempt to add action targeting instance that doesn't exist
        with self.assertRaises(KeyError):
            macro.add_action({
                "command": "turn_off",
                "instance": "device5",
                "target": "192.168.1.123",
                "friendly_name": "Countertop LEDs"
            })

        # Attempt to add ir action to node with no ir blaster
        with self.assertRaises(KeyError):
            macro.add_action({
                "command": "ir",
                "ir_target": "tv",
                "key": "power",
                "target": "192.168.1.123"
            })

    def test_delete_action_invalid(self):
        # Create test macro with 1 action
        macro = Macro.objects.create(name='New Macro')
        macro.add_action(self.set_rule_action)

        # Attempt to delete a non-integer index
        with self.assertRaises(SyntaxError):
            macro.del_action("enable")

        # Attempt to delete out-of-range index
        with self.assertRaises(ValueError):
            macro.del_action(5)

    # Should reformat certain commands for readability in edit macro modal
    def test_set_frontend_values(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add action containing set_rule, should change to Set Rule and append value
        macro.add_action(self.set_rule_action)
        self.assertEqual(json.loads(macro.actions)[0]['action_name'], 'Set Rule 248')

        # Add action containing ir command, (frontend converts to "{target} {key}" format)
        macro.add_action({
            "command": "ir",
            "ir_target": "ac",
            "key": "start",
            "target": "192.168.1.124"
        })
        self.assertEqual(json.loads(macro.actions)[1]['action_name'], 'Ac Start')

    # Confirm that new rules overwrite existing rules they would conflict with
    def test_no_conflicting_rules(self):
        # Create test macro
        macro = Macro.objects.create(name='New Macro')

        # Add 2 set_rule actions targeting the same instance with different values
        macro.add_action(self.set_rule_action)
        self.set_rule_action['rule'] = 456
        self.set_rule_action['target'] = "192.168.1.123"
        self.set_rule_action['friendly_name'] = "Countertop LEDs"
        macro.add_action(self.set_rule_action)

        # Should only contain 1 action, should have most-recent value (456)
        self.assertEqual(len(json.loads(macro.actions)), 1)
        self.assertEqual(json.loads(macro.actions)[0]['action_name'], 'Set Rule 456')

        # Add both enable and disable targeting the same instance
        macro.add_action({
            "command": "enable",
            "instance": "device1",
            "target": "192.168.1.123",
            "friendly_name": "Countertop LEDs"
        })
        macro.add_action({
            "command": "disable",
            "instance": "device1",
            "target": "192.168.1.123",
            "friendly_name": "Countertop LEDs"
        })

        # Should only contain 1 additional rule, should have most-recent value (disable)
        self.assertEqual(len(json.loads(macro.actions)), 2)
        self.assertEqual(json.loads(macro.actions)[1]['action_name'], 'Disable')

        # Add both turn_on and turn_off targeting the same instance
        macro.add_action(self.turn_on_action)
        macro.add_action(self.turn_off_action)

        # Should only contain 1 additional rule, should have most-recent value (turn_off)
        self.assertEqual(len(json.loads(macro.actions)), 3)
        self.assertEqual(json.loads(macro.actions)[2]['action_name'], 'Turn Off')


# Test endpoints used to record and edit macros
class MacroTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

        # Payloads to add macro actions
        self.action1 = {
            "name": "First Macro",
            "action": {
                "command": "turn_on",
                "instance": "device1",
                "target": "192.168.1.123",
                "friendly_name": "Cabinet Lights"
            }
        }
        self.action2 = {
            "name": "First Macro",
            "action": {
                "command": "enable",
                "instance": "device1",
                "target": "192.168.1.123",
                "friendly_name": "Cabinet Lights"
            }
        }

    def test_macro_name_available(self):
        # Should be available
        response = self.client.get('/macro_name_available/New')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Name New available')

        # Create in database, should no longer be available
        Macro.objects.create(name='New')
        response = self.client.get('/macro_name_available/New')
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()['message'], 'Name New already in use')

    def test_add_macro_action(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Send request, verify response, verify macro created
        response = self.client.post('/add_macro_action', self.action1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Done')
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_delete_macro_action(self):
        # Create macro, verify exists
        response = self.client.post('/add_macro_action', self.action1)
        self.assertEqual(len(Macro.objects.all()), 1)

        # Call view to delete just-created action
        response = self.client.get('/delete_macro_action/First Macro/0')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Done')

        # Should still exist
        # TODO the frontend deletes it when last action removed, should this be moved to backend?
        # Frontend will still need to check to reload, won't remove much code
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_delete_macro(self):
        # Create macro, verify exists in database
        Macro.objects.create(name='test')
        self.assertEqual(len(Macro.objects.all()), 1)

        # Call view to delete macro
        response = self.client.get('/delete_macro/test')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['message'], 'Done')
        self.assertEqual(len(Macro.objects.all()), 0)

    def test_run_macro(self):
        # Create macro with 2 actions, verify exists
        self.client.post('/add_macro_action', self.action1)
        self.client.post('/add_macro_action', self.action2)
        self.assertEqual(len(Macro.objects.all()), 1)

        # Mock parse_command to do nothing
        with patch('api.views.parse_command', return_value=True) as mock_parse_command:
            # Call view to run macro, confirm response, confirm parse_command called twice
            response = self.client.get('/run_macro/First Macro')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()['message'], 'Done')
            self.assertEqual(mock_parse_command.call_count, 2)

    def test_get_macro_actions(self):
        # Create macro with 2 actions, verify exists
        self.client.post('/add_macro_action', self.action1)
        self.client.post('/add_macro_action', self.action2)
        self.assertEqual(len(Macro.objects.all()), 1)

        # Request macro actions, confirm correct response
        response = self.client.get('/get_macro_actions/First Macro')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['message'],
            [
                {
                    "ip": "192.168.1.123",
                    "args": [
                        "turn_on",
                        "device1"
                    ],
                    "node_name": "Test1",
                    "target_name": "Cabinet Lights",
                    "action_name": "Turn On"
                },
                {
                    "ip": "192.168.1.123",
                    "args": [
                        "enable",
                        "device1"
                    ],
                    "node_name": "Test1",
                    "target_name": "Cabinet Lights",
                    "action_name": "Enable"
                }
            ]
        )


class InvalidMacroTests(TestCase):
    def setUp(self):
        # Set default content_type for post requests (avoid long lines)
        self.client = JSONClient()

        # Create 3 test nodes
        create_test_nodes()

    def test_add_macro_action_get_request(self):
        # Requires POST request
        response = self.client.get('/add_macro_action')
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.json()['message'], 'Must post data')

    def test_add_invalid_macro_action(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Payload containing non-existing device5
        payload = {
            "name": "First Macro",
            "action": {
                "command": "turn_on",
                "instance": "device5",
                "target": "192.168.1.123",
                "friendly_name": "Not Real"
            }
        }

        # Send request, verify response, verify macro not created
        response = self.client.post('/add_macro_action', payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['message'], 'Invalid action')
        self.assertEqual(len(Macro.objects.all()), 0)

        # Create macro with 1 valid action, confirm exists
        payload = {
            "name": "First Macro",
            "action": {
                "command": "turn_on",
                "instance": "device1",
                "target": "192.168.1.123",
                "friendly_name": "Cabinet Lights"
            }
        }
        response = self.client.post('/add_macro_action', payload)
        self.assertEqual(len(Macro.objects.all()), 1)

        # Attempt to add second invalid action (non-existing device5)
        payload = {
            "name": "First Macro",
            "action": {
                "command": "turn_on",
                "instance": "device5",
                "target": "192.168.1.123",
                "friendly_name": "Not Real"
            }
        }
        response = self.client.post('/add_macro_action', payload)

        # Confirm macro still exists but invalid action was not added
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Macro.objects.all()), 1)
        macro = Macro.objects.all()[0]
        self.assertEqual(len(json.loads(macro.actions)), 1)

    def test_delete_invalid_macro_action(self):
        # Create macro, verify exists
        payload = {
            "name": "First Macro",
            "action": {
                "command": "turn_on",
                "instance": "device1",
                "target": "192.168.1.123",
                "friendly_name": "Cabinet Lights"
            }
        }
        response = self.client.post('/add_macro_action', payload)
        self.assertEqual(len(Macro.objects.all()), 1)

        # Attempt to delete non-existing macro action, verify response
        response = self.client.get('/delete_macro_action/First Macro/5')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Macro action does not exist')
        self.assertEqual(len(Macro.objects.all()), 1)

    def test_invalid_macro_does_not_exist(self):
        # Confirm no macros
        self.assertEqual(len(Macro.objects.all()), 0)

        # Call all endpoints, confirm correct error
        response = self.client.get('/run_macro/not-real')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Macro not-real does not exist')

        response = self.client.get('/delete_macro/not-real')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Macro not-real does not exist')

        response = self.client.get('/delete_macro_action/not-real/1')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Macro not-real does not exist')

        response = self.client.get('/get_macro_actions/not-real')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], 'Macro not-real does not exist')
