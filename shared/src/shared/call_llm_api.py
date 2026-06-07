import hashlib
import json
from shared.logger import Logger
from shared.cache import mem

def retry_generate_until_success(model, prompt, system_message=None):
    for _ in range(20):
        try:
            return model.generate_content(prompt).text
        except Exception as e:
            Logger.warning(f"Error generating content: {e}")
            import time
            print("gemini fail")
            time.sleep(1)
    raise Exception("Failed to generate content after retries")


def _cached_retry_completion(kwargs_hash, kwargs):
    from litellm import completion_with_retries
    return completion_with_retries(**kwargs)
_cached_retry_completion = mem()(_cached_retry_completion, ignore=['kwargs'])

def cached_retry_completion(**kwargs):
    """
    Wraps the completion_with_retries call with caching.
    
    This function computes a hash for the provided kwargs to be used as a caching key,
    then delegates the call to a cached helper that ignores the kwargs parameter when 
    building the cache key.
    """
    # Create a reproducible hash based on the kwargs
    kwargs_serialized = json.dumps(kwargs, sort_keys=True)
    kwargs_hash = hashlib.sha256(kwargs_serialized.encode('utf-8')).hexdigest()
    return _cached_retry_completion(kwargs_hash, kwargs)
