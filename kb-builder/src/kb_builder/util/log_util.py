import os

from shared.logger import Logger


def set_log_file_path(log_file_path):
    global LOG_FILE_PATH
    LOG_FILE_PATH = log_file_path  
    #Logger.info('Log File Path: ' + LOG_FILE_PATH) 
    
def log_file(log_message): 
    global LOG_FILE_PATH
    with open(LOG_FILE_PATH, 'a') as file:
        file.write(log_message + '\n')
    
def log_processing_error(file_path, file_extension, message):
    Logger.error(f" {message} -- {file_extension} : {file_path}", stacklevel=3)
    log_file(f"ERROR: {message} -- {file_extension} : {file_path}")
    
def log_processing_warning(file_path, file_extension, message):
    Logger.warning(f" {message} -- {file_extension} : {file_path}")
    log_file(f"WARN: {message} -- {file_extension} : {file_path}")