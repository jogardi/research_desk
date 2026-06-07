import os
import redis
from shared.config import Config
from shared.logger import Logger

# Initialize the Redis client - exposes the redis_client variable

REDIS_HOST= 'dummy'
REDIS_PORT= 0

# redis_uri = f"redis://{os.environ.get('REDIS_USER')}:{os.environ.get('REDIS_PASSWORD')}@{Config.REDIS_HOST}:{Config.REDIS_PORT}/0"
redis_uri = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
#Logger.info(f"*** Redis URI: {redis_uri}")    

# Create a Redis client instance for the application cache
redis_client = redis.Redis.from_url(redis_uri, decode_responses=True)