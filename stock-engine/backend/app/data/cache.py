"""Tiny thread-safe in-memory TTL cache."""
import threading
import time


class TTLCache:
    def __init__(self):
        self._data: dict[str, tuple[float, object]] = {}
        self._lock = threading.Lock()

    def get(self, key: str):
        with self._lock:
            item = self._data.get(key)
            if item is None:
                return None
            expires, value = item
            if time.time() > expires:
                del self._data[key]
                return None
            return value

    def set(self, key: str, value, ttl: float):
        with self._lock:
            self._data[key] = (time.time() + ttl, value)

    def clear(self):
        with self._lock:
            self._data.clear()


cache = TTLCache()


def cached(key: str, ttl: float, fn):
    """Return cached value for key, or compute via fn() and cache it."""
    value = cache.get(key)
    if value is not None:
        return value
    value = fn()
    if value is not None:
        cache.set(key, value, ttl)
    return value
