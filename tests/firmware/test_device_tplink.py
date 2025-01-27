import json
import asyncio
import unittest
from Tplink import Tplink
from cpython_only import cpython_only

# Read mock API receiver address
with open('config.json', 'r') as file:
    config = json.load(file)


class TestTplink(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.instance = Tplink("device1", "device1", "dimmer", 42, {}, 1, 100, config["mock_receiver"]["ip"])

    def test_01_initial_state(self):
        self.assertIsInstance(self.instance, Tplink)
        self.assertTrue(self.instance.enabled)
        self.assertFalse(self.instance.fading)

    def test_02_turn_off(self):
        self.assertTrue(self.instance.send(0))

        # Repeat as bulb
        self.instance._type = "bulb"
        self.assertTrue(self.instance.send(0))

    def test_03_turn_on(self):
        self.assertTrue(self.instance.send(1))

        # Repeat as dimmer
        self.instance._type = "dimmer"
        self.assertTrue(self.instance.send(1))

    def test_04_turn_on_while_disabled(self):
        self.instance.disable()
        self.assertTrue(self.instance.send(1))
        self.instance.enable()

    def test_05_send_method_error(self):
        # Instantiate with invalid IP, confirm send method returns False
        test = Tplink("device1", "device1", "dimmer", 42, {}, 1, 100, "0.0.0.")
        self.assertFalse(test.send())

    def test_06_parse_response(self):
        # Should return True if response does not contain error
        self.assertTrue(self.instance._parse_response(
            '{"smartlife.iot.dimmer":{"set_brightness":{"err_code":0}}}'
        ))
        self.assertTrue(self.instance._parse_response(
            '{"smartlife.iot.smartbulb.lightingservice":{"transition_light_state":{"err_code":0}}}'
        ))

        # Should return False if response contains error
        self.assertFalse(self.instance._parse_response(
            '{"smartlife.iot.dimmer":{"set_brightness":{"err_code":-3,"err_msg":"invalid argument"}}}'
        ))

        # Should return False if response is empty
        self.assertFalse(self.instance._parse_response('{}'))

    @cpython_only
    def test_07_send_detects_errors(self):
        from unittest.mock import patch

        # Simulate error response from dimmer, confirm send returns False
        with patch.object(self.instance, '_send_payload', return_value=False):
            self.assertFalse(self.instance.send(1))

        # Simulate error response on second dimmer request, confirm send returns False
        with patch.object(self.instance, '_send_payload'), \
             patch.object(self.instance, '_parse_response', side_effect=[True, False]):
            self.assertFalse(self.instance.send(1))

        # Simulate error response from bulb, confirm send returns False
        self.instance._type = 'bulb'
        with patch.object(self.instance, '_send_payload', return_value=False):
            self.assertFalse(self.instance.send(1))

    @cpython_only
    def test_08_check_device_status(self):
        from unittest.mock import patch

        # Simulate dimmer status object with dimmer turned on and brightness = 100
        self.instance._type = 'dimmer'
        with patch.object(self.instance, '_send_payload', return_value='{"system":{"get_sysinfo":{"sw_ver":"1.0.3 Build 200326 Rel.082355","hw_ver":"2.0","model":"HS220(US)","deviceId":"800683BE95BB206B76B732288E8915B47A19CDD1","oemId":"5BB206A037C71BB76B732285E9B0C417","hwId":"CA321B76B73228706FC7C34C5BB206A4","rssi":-42,"latitude_i":0,"longitude_i":0,"alias":"TP-LINK_Smart Dimmer_E9D1","mic_type":"IOT.SMARTPLUGSWITCH","feature":"TIM","mac":"B2:21:A8:2D:E9:D1","updating":0,"led_off":1,"relay_state":1,"brightness":100,"on_time":1230,"icon_hash":"","dev_name":"Wi-Fi Smart Dimmer","active_mode":"none","next_action":{"type":-1},"preferred_state":[{"index":0,"brightness":100},{"index":1,"brightness":75},{"index":2,"brightness":50},{"index":3,"brightness":25}],"err_code":0}}}'):
            self.assertEqual(self.instance._check_device_status(), (True, 100))

        # Simulate bulb status object with bulb turned off and brightness = 50
        self.instance._type = 'bulb'
        with patch.object(self.instance, '_send_payload', return_value='{"system":{"get_sysinfo":{"sw_ver":"1.0.6 Build 200630 Rel.102631","hw_ver":"2.0","model":"KL130(US)","deviceId":"800683BE95BB206B76B732288E8915B47A19CDD1","oemId":"5BB206A037C71BB76B732285E9B0C417","hwId":"CA321B76B73228706FC7C34C5BB206A4","rssi":-58,"latitude_i":0,"longitude_i":0,"alias":"TP-LINK_Smart Bulb_E9D1","status":"new","description":"Smart Wi-Fi LED Bulb with Color Changing","mic_type":"IOT.SMARTBULB","mic_mac":"B221A82DE9D1","dev_state":"normal","is_factory":false,"disco_ver":"1.0","ctrl_protocols":{"name":"Linkie","version":"1.0"},"active_mode":"none","is_dimmable":1,"is_color":1,"is_variable_color_temp":1,"light_state":{"on_off":0,"mode":"normal","hue":360,"saturation":0,"color_temp":2801,"brightness":50},"preferred_state":[{"index":0,"hue":0,"saturation":0,"color_temp":2700,"brightness":50},{"index":1,"hue":0,"saturation":100,"color_temp":0,"brightness":100},{"index":2,"hue":120,"saturation":100,"color_temp":0,"brightness":100},{"index":3,"hue":240,"saturation":100,"color_temp":0,"brightness":'):
            self.assertEqual(self.instance._check_device_status(), (False, 50))

        # Simulate error response, confirm _check_device_status raises RuntimeError
        with patch.object(self.instance, '_send_payload', return_value=False), \
             self.assertRaises(RuntimeError):
            self.instance._check_device_status()

    @cpython_only
    def test_17_monitor(self):
        from unittest.mock import patch

        # Task breaks monitor loop after first reading
        async def break_loop(task):
            await asyncio.sleep(1.1)
            task.cancel()

        # Runs instance.monitor + task to kill loop after first request
        async def test_monitor_and_kill():
            task_monitor = asyncio.create_task(self.instance.monitor())
            task_kill = asyncio.create_task(break_loop(task_monitor))
            await asyncio.gather(task_monitor, task_kill)

        # Set current_rule to 50, state to False
        self.instance.current_rule = 50
        self.instance.state = False

        # Run loop for 1 second while mocking status response to simulate light
        # turned on with brightness = 75
        with patch.object(self.instance, '_check_device_status', return_value=(True, 75)):
            asyncio.run(test_monitor_and_kill())

        # Confirm current_rule changed to 75, state changed to True
        self.assertEqual(self.instance.current_rule, 75)
        self.assertTrue(self.instance.state)
