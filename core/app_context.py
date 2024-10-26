'''This module is a shared context used to store instances of core classes,
allowing them to be imported by any other module.

Instances should ONLY be added by the `start` method in `main.py`.

Other modules may import the context with `import app_context` and access the
instances using the correct attribute (eg: app_context.config_instance.find()).

Do NOT use `from app_context import *` - this will create a local variable that
does not stay in sync with other modules.
'''

# Stores Api instance (core/Api.py)
api_instance = None

# Stores Config instance (core/Config.py)
config_instance = None

# Stores SoftwareTimer instance (core/SoftwareTimer.py)
timer_instance = None
