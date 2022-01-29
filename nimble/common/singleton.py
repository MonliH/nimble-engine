class Singleton(type):
    """A singleton metaclass.
    Taken from https://stackoverflow.com/a/6798042/9470078"""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
