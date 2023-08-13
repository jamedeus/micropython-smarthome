from types import FunctionType, MethodType


def schedule(function, arg):
    if type(function) not in [FunctionType, MethodType]:
        raise TypeError(f"'{type(function).__name__}' object isn't callable")
    function(arg)
