import json
from shared.logger import Logger
from webservice.cache.disk_cache import disk_cache
from webservice.cache.redis_cache_depracated import redis_client
from webservice.runtime_env import IS_PROD

class Cache:
    @classmethod
    def connect(cls):
        Logger.info("*** Connection established")

    @classmethod
    def close(cls):
        pass

    @classmethod
    def set(cls, key: str, value: dict, ttl: int):
        """Store value in cache with TTL."""
        disk_cache.set(key, value, expire=ttl)

    @classmethod
    def get(cls, key: str) -> dict:
        """Retrieve data from cache."""
        return disk_cache.get(key)

    @classmethod
    def delete(cls, key: str):
        """Delete data from cache."""
        if key in disk_cache:
            del disk_cache[key]

    @classmethod
    def clear(cls, key_prefix):
        """Clear all cache entries."""
        for key in disk_cache.keys():
            if key.startswith(key_prefix):
                disk_cache.delete(key)
