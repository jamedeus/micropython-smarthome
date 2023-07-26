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
        with open('app.log', 'w') as file:
            file.write(msg)

    def debug(self, msg, *args):
        with open('app.log', 'w') as file:
            file.write(msg)

    def warning(self, msg):
        with open('app.log', 'w') as file:
            file.write(msg)

    def error(self, msg):
        with open('app.log', 'w') as file:
            file.write(msg)

    def critical(self, msg):
        with open('app.log', 'w') as file:
            file.write(msg)

    def addHandler(self, hdlr=None):
        self.handlers.append(Handler())


def basicConfig(*args, **kwargs):
    pass


def getLogger(name=None):
    return Logger()


def FileHandler(filename, mode=None, encoding=None, delay=False):
    return Handler()


mock_root = Logger()
