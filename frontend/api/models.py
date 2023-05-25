import json
import re
from django.db import models
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

        # Get target IP, look up Node instance
        ip = action['target']
        del action['target']
        node = Node.objects.get(ip=ip)
        node_name = node.friendly_name

        # Throw error if target node config doesn't contain target instance
        if 'instance' in action.keys():
            if action['instance'] not in node.config.config.keys():
                raise KeyError(f"{node_name} has no instance {action['instance']}")
        else:
            if 'ir_blaster' not in node.config.config.keys():
                raise KeyError(f"{node_name} has no IR Blaster")

        # Get friendly_name of target instance (for frontend)
        if 'friendly_name' in action.keys():
            target_name = action['friendly_name']
            del action['friendly_name']

        # Get argument list (format expected by parse_command)
        args = list(action.values())

        # Get command name (for frontend)
        command = args[0]

        # Special adjustments for readability in edit macro modal
        if command == "set_rule":
            # Append new rule to command shown in frontend
            command = f'set_rule {args[2]}'
        elif command == "ir":
            # Set target name (paylod doesn't contain friendly_name)
            target_name = "IR Blaster"
            # Parse 'tv power' from ['ir', 'tv', 'power']
            command = re.sub(r'[\[\]\',]', '', str(args[1:]))

        # Deserialize existing macro actions to dict
        actions = json.loads(self.actions)

        # Get existing actions targeting the same node and instance
        potential_conflicts = [i for i in actions if i['node_name'] == node_name and i['target_name'] == target_name]

        # Remove conflicting actions for the same target instance
        for i in potential_conflicts:
            # Prevent multiple set_rule actions
            if i['action_name'].startswith('Set Rule') and command.startswith('set_rule'):
                del actions[actions.index(i)]
            # Prevent both enable and disable, or duplicates
            elif i['action_name'] in ["Enable", "Disable"] and command in ['enable', 'disable']:
                del actions[actions.index(i)]
            # Prevent both turn_on and turn_off, or duplicates
            elif i['action_name'] in ["Turn On", "Turn Off"] and command in ['turn_on', 'turn_off']:
                del actions[actions.index(i)]

        # Add new action, reserialize, save
        actions.append(
            {
                'ip': ip,
                'args': args,
                'node_name': node_name,
                'target_name': target_name,
                'action_name': command.replace('_', ' ').title()
            }
        )
        self.actions = json.dumps(actions)
        self.save()

    def del_action(self, index):
        if not isinstance(index, int):
            raise SyntaxError("Argument must be integer index of action to delete")

        # Deserialize existing macro actions to dict
        actions = json.loads(self.actions)

        if index >= len(actions):
            raise ValueError(f"Action {index} does not exist")

        # Delete, reserialize, save
        del actions[index]
        self.actions = json.dumps(actions)
        self.save()
