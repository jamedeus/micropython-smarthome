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

    level = ERROR

    def __init__(self):
        self.handlers = []
        self.addHandler()

    def log(self, level, msg, *args):
        if level >= self.level:
            with open('app.log', 'w') as file:
                file.write(msg)

    def debug(self, msg, *args):
        self.log(DEBUG, msg, *args)

    def info(self, msg, *args):
        self.log(INFO, msg, *args)

    def warning(self, msg, *args):
        self.log(WARNING, msg, *args)

    def error(self, msg, *args):
        self.log(ERROR, msg, *args)

    def critical(self, msg, *args):
        self.log(CRITICAL, msg, *args)

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
