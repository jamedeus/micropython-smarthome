import os

# Copied from lib/logging.py
CRITICAL = 50
ERROR    = 40
WARNING  = 30
INFO     = 20
DEBUG    = 10
NOTSET   = 0

# Copied from lib/logging.py
_level_dict = {
    CRITICAL: "CRITICAL",
    ERROR: "ERROR",
    WARNING: "WARNING",
    INFO: "INFO",
    DEBUG: "DEBUG",
}

# Copied from lib/logging.p
_nameToLevel = {v: k for k, v in _level_dict.items()}


class Handler:
    def close(self):
        pass

    def setFormatter(*args):
        pass


class Logger:
    def __init__(self):
        self.handlers = []
        self.addHandler()

    def info(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def debug(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def warning(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def error(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def critical(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def addHandler(self, hdlr=None):
        self.handlers.append(Handler())


def basicConfig(*args, **kwargs):
    pass


def getLogger(name=None):
    return Logger()


def FileHandler(filename, mode=None, encoding=None, delay=False):
    if not os.path.exists(filename):
        open(filename, 'w')
    return Handler()


mock_root = Logger()
