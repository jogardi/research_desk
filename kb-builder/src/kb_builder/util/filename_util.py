import os
import re

def validate_name(s: str) -> bool:
    return bool(re.match(r'^[a-zA-Z0-9./() _-]+$', s)) and '__' not in s

def sanitize_name(s: str) -> str:
    # Replace invalid characters (excluding allowed ones) with '-'
    sanitized = re.sub(r'[^a-zA-Z0-9./() _-]', '-', s)
    # Replace consecutive underscores ('__') with a single '-'
    sanitized = re.sub(r'__+', '-', sanitized)
    # Trim leading and trailing whitespace
    sanitized = sanitized.strip()
    return sanitized

def sanitize_and_rename_file(filepath: str):
    # Extract directory and filename
    directory, filename = os.path.split(filepath)
    sanitized_filename = sanitize_name(filename)    
    
    # Build the new filepath
    sanitized_filepath = os.path.join(directory, sanitized_filename)
    
    # Rename the file
    os.rename(filepath, sanitized_filepath)


