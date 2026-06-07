from flask import request
from flask_limiter import Limiter
from shared.config import Config
from shared.logger import Logger
from webservice.cache.redis_cache_depracated import redis_uri
from webservice.session_manager import protected_user_id

#
# Rate Limiter module
#
# This module initializes the rate limiter for the Flask application.
# The rate limiter is used to limit the number of requests that can be made to the application.
#
# This module exposes the following function:
#     * init_rate_limiter: Initialize the rate limiter with the Flask application.
#
# This modeuleexposes the following variables:
#     * limiter: The rate limiter instance.

# limit key function
def _get_limit_key():
    key = protected_user_id() # use the user ID as the key
    if key is None:
        key = request.remote_addr # use the IP address as the key
    return key

# Create an instance of the rate limiter with our custom key function and default rate limits.
limiter = Limiter(  
    key_func=_get_limit_key,  # Key function to get the rate limit key
    default_limits=Config.RATE_LIMIT_GLOBAL.split('; '),  # Default global rate limits
    storage_uri="memory://" if Config.PROFILE != 'prod' else redis_uri  # Use in-memory storage in development, Redis in production
)

def init_rate_limiter(app):
    """ Initialize the rate limiter with the Flask application. """
    if Config.ENABLE_RATE_LIMIT:
        limiter.init_app(app)
        Logger.info("*** Rate limiter initialized ***")

