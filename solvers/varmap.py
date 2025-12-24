class VarManager:
    def __init__(self):
        self._map = {}
        self._rev = {}
        self._counter = 0

    def new(self, key):
        if key in self._map:
            return self._map[key]
        self._counter += 1
        self._map[key] = self._counter
        self._rev[self._counter] = key
        return self._counter

    def get(self, key):
        return self._map.get(key)

    def key_of(self, var):
        return self._rev.get(var)

    def nvars(self):
        return self._counter
