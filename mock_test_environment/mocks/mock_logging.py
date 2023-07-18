class Handler:
    def close(self):
        pass

    def setFormatter(*args):
        pass


class Logger:
    def __init__(self):
        self.handlers = []
        self.addHandler()

    def info(self, msg):
        pass

    def debug(self, msg, *args):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

    def critical(self, msg):
        pass

    def addHandler(self, hdlr=None):
        self.handlers.append(Handler())


def basicConfig(*args, **kwargs):
    pass


def getLogger(name=None):
    return Logger()


def FileHandler(filename, mode=None, encoding=None, delay=False):
    return Handler()


mock_root = Logger()
