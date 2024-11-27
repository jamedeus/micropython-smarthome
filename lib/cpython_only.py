import sys

PYTHON_IMPLEMENTATION = sys.implementation.name


def cpython_only(func):
    '''Decorator prevents unit tests from running on micropython.
    Used to skip tests with mocks, too much mem allocation, etc.
    '''
    def wrapper(*args, **kwargs):
        if PYTHON_IMPLEMENTATION != 'cpython':
            print(' SKIP (cpython only)')
        else:
            return func(*args, **kwargs)
    return wrapper
