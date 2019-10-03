def safe_execute(default, exception, function, *args):
    try:
        return function(*args)
    except exception:
        return default

class Struct:
    def __init__(self, dct=None, **kwargs):
        if dct is not None:
            kwargs.update(dct)
        for key, value in kwargs.items():
            setattr(self, key, value)