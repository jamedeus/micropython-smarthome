from django.db import models
import json

def default_actions():
    return json.dumps([])



class Macro(models.Model):
    def __str__(self):
        return self.name

    name = models.CharField(max_length=50, unique=True)

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

        actions = json.loads(self.actions)
        actions.append({'ip': ip, 'args': args})
        self.actions = json.dumps(actions)

    def del_action(self, index):
        if not isinstance(action, int):
            raise SyntaxError

        actions = json.loads(self.actions)

        if index >= len(actions):
            raise ValueError

        del actions[index]
        self.actions = json.dumps(actions)
