from functools import lru_cache

@lru_cache()
def mem():
    import joblib
    from pathlib import Path
    return joblib.Memory(location=Path.home() / 'research_desk_cache', compress=True, verbose=0).cache
