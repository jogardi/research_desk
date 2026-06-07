from functools import lru_cache

@lru_cache()
def dotenvvars():
    import os
    from kb_builder.load_env import load_env
    load_env(override=True)
    return os.environ
