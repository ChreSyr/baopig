
from .logging import LOGGER


class _ClipBoard:
    def __init__(self):
        self._data = {}

    data = property(lambda self: self._data)

    def get(self, type):
        try:
            return self.data[type]
        except KeyError:
            return None

    def put(self, data):
        self.data[type(data)] = data
        # LOGGER.info("Copied {} object : '{}' inside clipboard".format(type(data).__name__, data))

    def contains(self, type):
        return type in self.data

    def get_types(self):
        return self.data.keys()


clipboard = _ClipBoard()