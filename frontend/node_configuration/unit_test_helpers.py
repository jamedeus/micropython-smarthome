import json, os
from django.conf import settings
from django.http import JsonResponse
from .models import Config, Node



# Simulated input from user creating config with frontend
# Used by GenerateConfigFileTests, DeleteConfigTests, DuplicateDetectionTests
request_payload = {"friendlyName":"Unit Test Config","location":"build pipeline","floor":"0","ssid":"jamnet","password":"cjZY8PTa4ZQ6S83A","sensors":{"sensor1":{"id":"sensor1","new":False,"modified":False,"type":"pir","nickname":"Motion","pin":"4","default_rule":5,"targets":["device1","device2","device5","device6"],"schedule":{"08:00":"5","22:00":"1"}},"sensor2":{"id":"sensor2","new":False,"modified":False,"type":"switch","nickname":"Switch","pin":"5","default_rule":"enabled","targets":["device4","device7"],"schedule":{}},"sensor3":{"id":"sensor3","new":False,"modified":False,"type":"dummy","nickname":"Override","default_rule":"on","targets":["device3"],"schedule":{"06:00":"on","18:00":"off"}},"sensor4":{"id":"sensor4","new":False,"modified":False,"type":"desktop","nickname":"Activity","ip":"192.168.1.150","default_rule":"enabled","targets":["device1","device2","device5","device6"],"schedule":{"08:00":"enabled","22:00":"disabled"}},"sensor5":{"id":"sensor5","new":False,"modified":False,"type":"si7021","nickname":"Temperature","mode":"cool","tolerance":"3","default_rule":71,"targets":["device4","device7"],"schedule":{"08:00":"73","22:00":"69"}}},"devices":{"device1":{"id":"device1","new":False,"modified":False,"type":"dimmer","nickname":"Overhead","ip":"192.168.1.105","default_rule":100,"schedule":{"08:00":"100","22:00":"35"}},"device2":{"id":"device2","new":False,"modified":False,"type":"bulb","nickname":"Lamp","ip":"192.168.1.106","default_rule":75,"schedule":{"08:00":"100","22:00":"35"}},"device3":{"id":"device3","new":False,"modified":False,"type":"relay","nickname":"Porch Light","ip":"192.168.1.107","default_rule":"enabled","schedule":{"06:00":"disabled","18:00":"enabled"}},"device4":{"id":"device4","new":False,"modified":False,"type":"dumb-relay","nickname":"Fan","pin":"18","default_rule":"disabled","schedule":{}},"device5":{"id":"device5","new":False,"modified":False,"type":"desktop","nickname":"Screen","ip":"192.168.1.150","default_rule":"enabled","schedule":{"08:00":"enabled","22:00":"disabled"}},"device6":{"id":"device6","new":False,"modified":False,"type":"pwm","nickname":"Cabinet Lights","pin":"26","min":"0","max":"1023","default_rule":721,"schedule":{}},"device7":{"id":"device7","new":False,"modified":False,"type":"mosfet","nickname":"Humidifier","pin":"19","default_rule":"disabled","schedule":{}},"device8":{"id":"device8","new":False,"modified":False,"type":"wled","nickname":"TV Bias Lights","ip":"192.168.1.110","default_rule":128,"schedule":{"08:00":"100"}},"device9":{"id":"device9","new":True,"modified":False,"type":"ir-blaster","pin":"23","target":["tv"],"schedule":{}}}}



# Full test configs used to create fake Configs + Nodes (see create_test_nodes)
test_config_1 = {"metadata": {"id": "Test1", "location": "Inside cabinet above microwave", "floor": "1"}, "wifi": {"ssid": "jamnet", "password": "cjZY8PTa4ZQ6S83A"}, "device1": {"type": "pwm", "nickname": "Cabinet Lights", "pin": "4", "min": "0", "max": "1023", "default_rule": 1023, "schedule": {"22:00": "1023", "22:01": "fade/256/7140", "00:00": "fade/32/7200", "05:00": "Disabled"}}, "device2": {"type": "relay", "nickname": "Overhead Lights", "ip": "192.168.1.217", "default_rule": "enabled", "schedule": {"05:00": "enabled", "22:00": "disabled"}}, "sensor1": {"type": "pir", "nickname": "Motion Sensor", "pin": "15", "default_rule": "2", "targets": ["device1", "device2"], "schedule": {"10:00": "2", "22:00": "2"}}}

test_config_2 = {"metadata": {"id": "Test2", "location": "Bedroom", "floor": "2"}, "wifi": {"ssid": "jamnet", "password": "cjZY8PTa4ZQ6S83A"}, "device1": {"type": "api-target", "nickname": "Air Conditioner", "ip": "192.168.1.232", "default_rule": {"on": ["ir_key", "ac", "start"], "off": ["ir_key", "ac", "stop"]}, "schedule": {}}, "sensor1": {"type": "si7021", "nickname": "Thermostat", "mode": "cool", "tolerance": "0.5", "default_rule": 74, "targets": ["device1"], "schedule": {}}}

test_config_3 = {"metadata": {"id": "Test3", "location": "Inside cabinet under sink", "floor": "1"}, "wifi": {"ssid": "jamnet", "password": "cjZY8PTa4ZQ6S83A"}, "device1": {"type": "pwm", "nickname": "Bathroom LEDs", "pin": "4", "min": "0", "max": "1023", "default_rule": 0, "schedule": {"22:00": "1023", "22:01": "fade/256/7140", "00:00": "fade/32/7200", "05:00": "Disabled"}}, "device2": {"type": "relay", "nickname": "Bathroom Lights", "ip": "192.168.1.239", "default_rule": "enabled", "schedule": {"05:00": "enabled", "22:00": "disabled"}}, "device3": {"type": "relay", "nickname": "Entry Light", "ip": "192.168.1.202", "default_rule": "enabled", "schedule": {"05:00": "enabled", "23:00": "disabled"}}, "sensor1": {"type": "pir", "nickname": "Motion Sensor (Bath)", "pin": "15", "default_rule": "2", "targets": ["device1", "device2"], "schedule": {"10:00": "2", "22:00": "2"}}, "sensor2": {"type": "pir", "nickname": "Motion Sensor (Entry)", "pin": "16", "default_rule": "1", "targets": ["device3"], "schedule": {"00:00": "1"}}}




# Replaces provision view to simulate partially successful reupload_all
def simulate_reupload_all_partial_success(config, ip, modules, libs):
    if config == "test2.json":
        return JsonResponse("Error: Unable to connect to node, please make sure it is connected to wifi and try again.", safe=False, status=404)
    else:
        return JsonResponse("Upload complete.", safe=False, status=200)



# Replaces Webrepl.put_file to simulate uploading to a node with no /lib directory
def simulate_first_time_upload(self, src_file, dst_file):
    if src_file.split("/")[1] == "lib":
        raise AssertionError



# Helper function to create test nodes with known values
def create_test_nodes():
    with open(f'{settings.CONFIG_DIR}/test1.json', 'w') as file:
        json.dump(test_config_1, file)

    node1 = Node.objects.create(friendly_name='test1', ip='192.168.1.123', floor='1')
    config1 = Config.objects.create(config=test_config_1, filename='test1.json', node=node1)

    with open(f'{settings.CONFIG_DIR}/test2.json', 'w') as file:
        json.dump(test_config_2, file)

    node2 = Node.objects.create(friendly_name='test2', ip='192.168.1.124', floor='1')
    config2 = Config.objects.create(config=test_config_2, filename='test2.json', node=node2)

    with open(f'{settings.CONFIG_DIR}/test3.json', 'w') as file:
        json.dump(test_config_2, file)

    node3 = Node.objects.create(friendly_name='test3', ip='192.168.1.125', floor='1')
    config2 = Config.objects.create(config=test_config_3, filename='test3.json', node=node3)



# Deletes files written to disk by create_test_nodes
def clean_up_test_nodes():
    os.remove(f'{settings.CONFIG_DIR}/test1.json')
    os.remove(f'{settings.CONFIG_DIR}/test2.json')
    os.remove(f'{settings.CONFIG_DIR}/test3.json')
