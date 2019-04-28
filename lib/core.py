def safe_execute(default, exception, function, *args):
    try:
        return function(*args)
    except exception:
        return default

# Empty class to use as struct
class Struct:
	pass