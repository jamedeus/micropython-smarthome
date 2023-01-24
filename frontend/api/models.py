from django.db import models
import json
import re

from node_configuration.models import Node

def default_actions():
    return json.dumps([])

# Override method to automatically convert to lowercase, replace -/_ with spaces, remove special chars
# Also allows case-insensitive lookups with Macro.objects.get()
class NameField(models.CharField):
    def to_python(self, value):
        if isinstance(value, str):
            value = re.sub('[-_]', ' ', value.lower())
        else:
            value = re.sub('[-_]', ' ', str(value).lower())

        return re.sub('[^0-9a-z ]+', '', value)



class Macro(models.Model):
    def __str__(self):
        # Each word capitalized
        return self.name.title()

    class Meta:
        constraints = [
            models.CheckConstraint(check=~models.Q(name=""), name="non_empty_title")
        ]

    # Lowercase alphanumeric characters only (case will be converted automatically)
    name = NameField(max_length=50, unique=True)

    # JSON-encoded list, contains dicts with 2 parameters:
    # - ip: IP of the target node
    # - args: API command + arguments (if any)
    # run_macro view iterates actions and passes each to parse_command view
    actions = models.JSONField(null=False, blank=False, default=default_actions)

    def add_action(self, action):
        if not isinstance(action, dict):
            raise SyntaxError

        ip = action['target']
        del action['target']
        args = list(action.values())

        node = Node.objects.get(ip = ip)
        node_name = node.friendly_name

        actions = json.loads(self.actions)

        command = args[0]
        if command == "set_rule":
            target_name = node.config.config[args[1]]['nickname']
            command = f'{command} {args[2]}'
        elif command == "turn_on" or command == "turn_off" or command == "trigger_sensor":
            target_name = node.config.config[args[1]]['nickname']
        elif command == "ir":
            target_name = "IR Blaster"
            command = re.sub('[\[\]\',]', '', str(args[1:]))
        else:
            target_name = node.config.config[args[1]]['nickname']

        actions.append({'ip': ip, 'args': args, 'node_name': node_name, 'target_name': target_name, 'action_name': command.replace('_', ' ').title()})

        self.actions = json.dumps(actions)
        self.save()

    def del_action(self, index):
        if not isinstance(index, int):
            raise SyntaxError

        actions = json.loads(self.actions)

        if index >= len(actions):
            raise ValueError

        del actions[index]
        self.actions = json.dumps(actions)
        self.save()
