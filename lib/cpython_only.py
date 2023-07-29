import sys

PYTHON_IMPLEMENTATION = sys.implementation.name


# Decorator prevents unit tests from running on micropython
# Used to skip tests with mocks, too much mem allocation, etc
def cpython_only(func):
    def wrapper(*args, **kwargs):
        if PYTHON_IMPLEMENTATION != 'cpython':
            print(' SKIP (cpython only)')
        else:
            return func(*args, **kwargs)
    return wrapper
