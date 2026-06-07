from pathlib import Path
import time
from contextlib import contextmanager

def prep_path(path) -> Path:
    # creates parent directories if they don't exist
    x = Path(path)
    x.parent.mkdir(parents=True, exist_ok=True)
    return x

def prep_dir(path) -> Path:
    x = Path(path)
    x.mkdir(parents=True, exist_ok=True)
    return x

PRINT_PERF=False

@contextmanager
def timing(description: str='', print_start: bool = False):
    """
    Context manager for timing code execution.
    
    Usage:
        with timing("Database query"):
            # code to time
            
        # Can also capture the elapsed time:
        with timing("Processing") as timer:
            # code to time
        print(f"Took {timer.elapsed:.3f}s")
    """
    class Timer:
        def __init__(self):
            self.start = None
            self.elapsed = None
            
    timer = Timer()
    
    if print_start and PRINT_PERF:
        print(f"[TIMING] Starting: {description}")
    
    timer.start = time.time()
    try:
        yield timer
    finally:
        timer.elapsed = time.time() - timer.start
        if PRINT_PERF:
            print(f"[TIMING] {description}: {timer.elapsed:.3f}s")

@contextmanager
def detailed_timing(description: str, details_callback=None):
    """
    Context manager for timing with ability to add details after execution.
    
    Usage:
        with detailed_timing("Noun extraction") as timer:
            # code to time
            timer.details = {"nouns_found": 10, "threshold_passed": 3}
            
        # To suppress output, set timer.elapsed = -1
    """
    class DetailedTimer:
        def __init__(self):
            self.start = None
            self.elapsed = None
            self.details = {}
            self.sub_timers = {}
            
        def add_sub_timing(self, name: str, duration: float):
            """Add a sub-timing measurement"""
            self.sub_timers[name] = duration
            
    timer = DetailedTimer()
    timer.start = time.time()
    
    try:
        yield timer
    finally:
        if timer.elapsed is None:
            timer.elapsed = time.time() - timer.start
        
        # Skip output if elapsed is negative (suppression flag) or PRINT_PERF is False
        if timer.elapsed < 0 or not PRINT_PERF:
            return
            
        # Basic timing output
        print(f"[TIMING] {description}: {timer.elapsed:.3f}s")
        
        # Output sub-timings if any
        if timer.sub_timers:
            total_sub_time = sum(timer.sub_timers.values())
            for name, duration in timer.sub_timers.items():
                percentage = (duration / timer.elapsed * 100) if timer.elapsed > 0 else 0
                print(f"        - {name}: {duration:.3f}s ({percentage:.1f}%)")
            
            # Account for overhead
            overhead = timer.elapsed - total_sub_time
            if overhead > 0.001:  # Only show if significant
                overhead_pct = (overhead / timer.elapsed * 100) if timer.elapsed > 0 else 0
                print(f"        - Overhead: {overhead:.3f}s ({overhead_pct:.1f}%)")
        
        # Output additional details if provided
        if timer.details:
            details_str = ", ".join(f"{k}: {v}" for k, v in timer.details.items())
            print(f"        - {details_str}")
        
        # Call details callback if provided
        if details_callback:
            details_callback(timer)

def dict2obj(dictionary):
    from types import SimpleNamespace
    new_dict = {}
    for k, v in dictionary.items():
        if isinstance(v, dict):
            new_dict[k] = dict2obj(v)
        else:
            new_dict[k] = v
    return SimpleNamespace(**new_dict)
    # obj = object()
    # for key, value in dictionary.items():
    #     if isinstance(value, dict):
    #         value = dict2obj(value)
    #     setattr(obj, key, value)
   

def obj2dict(obj):
    from types import SimpleNamespace
    dictionary = {}
    for k, v in obj.__dict__.items():
        if isinstance(v, SimpleNamespace):
            dictionary[k] = obj2dict(v)
        else:
            dictionary[k] = v
    return dictionary


def truncate_dict_strings(d, max_length=500):
    """Recursively truncate long strings in a dictionary for better logging.
    Returns a new copy without modifying the original."""
    if isinstance(d, dict):
        return {k: truncate_dict_strings(v, max_length) for k, v in d.items()}
    elif isinstance(d, list):
        return [truncate_dict_strings(item, max_length) for item in d]
    elif isinstance(d, str) and len(d) > max_length:
        return d[:max_length] + "... [truncated]"
    else:
        return d