import json
from shared.logger import Logger
from webservice.cache.disk_cache import disk_cache
from webservice.cache.redis_cache import redis_client
from webservice.runtime_env import IS_PROD

class Cache:
    @classmethod
    def connect(cls):
        Logger.info("*** Redis connection established")

    @classmethod
    def close(cls):
        if not IS_PROD and redis_client is not None:
            # Close Redis connection
            try:
                redis_client.close()
                Logger.info("*** Redis connections closed")
            except Exception as e:
                Logger.error(f"Error closing Redis connections: {e}")

    @classmethod
    def set(cls, key: str, value: dict, ttl: int):
        """Store value in cache or Redis with TTL."""
        if not IS_PROD:
            disk_cache.set(key, value, expire=ttl)
        else:
            redis_client.set(key, json.dumps(value), ex=ttl)

    @classmethod
    def get(cls, key: str) -> dict:
        """Retrieve data from cache or Redis."""
        if not IS_PROD:
            return disk_cache.get(key)
        else:
            value = redis_client.get(key)
            return json.loads(value) if value else None

    @classmethod
    def delete(cls, key: str):
        """Delete data from cache or Redis."""
        if not IS_PROD:
            if key in disk_cache:
                del disk_cache[key]
        else:
            redis_client.delete(key)

    @classmethod
    def clear(cls, key_prefix):
        """Clear all cache entries."""
        if not IS_PROD:
            for key in disk_cache.keys():
                if key.startswith(key_prefix):
                    disk_cache.delete(key)
        else:
            for key in redis_client.keys():
                if key.startswith(key_prefix): 
                    redis_client.delete(key)
