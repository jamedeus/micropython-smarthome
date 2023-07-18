class Handler:
    def close(self):
        print("logger closing")
        pass


class Logger:
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

    def addHandler(self, hdlr):
        pass


def basicConfig(*args, **kwargs):
    pass


def getLogger(name=None):
    return Logger()


def FileHandler(filename, mode=None, encoding=None, delay=False):
    return Handler()
