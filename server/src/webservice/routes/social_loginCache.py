from cachetools import TTLCache
import json
from shared.config import Config
from webservice.cache.redis_cache_depracated import redis_client
from webservice.runtime_env import IS_PROD

class SocialLoginCache:
    TTL = 60  # TTL of 60 seconds for each cache item
    
    # Class-level cache with specified max size and TTL (time-to-live)
    _cache = TTLCache(maxsize=1000, ttl=TTL) # Max size of 1000 items with a TTL of 60 seconds

    @classmethod
    def store(cls, user_id: str, user_data: dict):
        """ Store the user data in cache with a TTL of 60 seconds. """
        if (IS_PROD):
            cls._cache[user_id] = user_data
        else:
            redis_client.set('social-login:' + user_id, json.dumps(user_data), ex=cls.TTL)  # Serialize as JSON for Redis

    @classmethod
    def retrieve(cls, user_id: str) -> dict:
        """Retrieve and remove the value from the cache if it exists."""
        try:
            # Retrieve and remove the item from the cache
            if (IS_PROD):
                return cls._cache.pop(user_id)
            else: # use Redis in production
                user_data = redis_client.get('social-login:' + user_id)
                if user_data:                
                    user_data = json.loads(user_data) # Deserialize JSON back to a dictionary
                    redis_client.delete(user_id) # Remove the key from the cache
                return user_data
        except KeyError:
            # Return None if the key does not exist or has expired
            return None

