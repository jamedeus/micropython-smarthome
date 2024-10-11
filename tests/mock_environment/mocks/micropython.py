from types import FunctionType, MethodType


def schedule(function, arg):
    if type(function) not in [FunctionType, MethodType]:
        raise TypeError(f"'{type(function).__name__}' object isn't callable")
    function(arg)


def mem_info(verbose=False):
    print('''stack: 2048 out of 15360
GC: total: 112000, used: 39760, free: 72240, max new split: 34816
 No. of 1-blocks: 648, 2-blocks: 150, max blk sz: 43, max free sz: 1081''')
