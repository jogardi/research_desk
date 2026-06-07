import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys
import colorlog
import requests
from shared.config import cfg
import traceback

class Logger:
    # Class variable to hold the logger instance
    _logger = None

    @staticmethod
    def initialize():
        """Initialize the logger."""
        # Get the log level from the environment variable, default to INFO if not set
        log_level = cfg().LOG_LEVEL.upper()
        print(f"*** Log level: {log_level}")
        valid_log_levels = {'DEBUG': logging.DEBUG, 'INFO': logging.INFO, 
                            'WARNING': logging.WARNING, 'ERROR': logging.ERROR, 
                            'CRITICAL': logging.CRITICAL}

        # Set to INFO if the provided level is invalid
        log_level = valid_log_levels.get(log_level, logging.INFO)

        # set app_log_path tp the root folder of the project:
        script_path = sys.argv[0]
        script_name_with_ext = os.path.basename(script_path)
        script_name = os.path.splitext(script_name_with_ext)[0]
        if not os.path.exists(cfg().LOG_FOLDER):
            os.makedirs(cfg().LOG_FOLDER)
        app_log_path = os.path.join(cfg().LOG_FOLDER, f'{script_name}.log')
        print(f"*** Log file: {app_log_path}")


        # Create a logger
        Logger._logger = logging.getLogger('ResearchDesk')
        Logger._logger.propagate = False # Prevents double logging - fix issue with Flask

        
        # set log level
        Logger._logger.setLevel(log_level)
        file_log_format = '%(asctime)s - %(levelname)s - %(message)s'

        #File handler
        file_handler = TimedRotatingFileHandler(app_log_path, when='midnight', interval=1, backupCount=7)
        file_handler.setLevel(log_level)
        file_handler_formatter = logging.Formatter(file_log_format)
        file_handler.setFormatter(file_handler_formatter)
        Logger._logger.addHandler(file_handler)
  
        #Colored console handler
        # console_log_format = "%(log_color)s%(levelname)-8s%(reset)s - %(filename)s:%(lineno)d - %(blue)s%(message)s"
        # colored_formatter = colorlog.ColoredFormatter(console_log_format)
        # console_handler = logging.StreamHandler()
        # console_handler.setFormatter(colored_formatter)
        # console_handler.setLevel(log_level)
        # Logger._logger.addHandler(console_handler)
        colored_formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(levelname)s -  %(filename)s:%(lineno)d - %(message)s",
            datefmt=None,
            reset=True,
            log_colors={
                'DEBUG': 'cyan',
                'INFO': 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'bold_red',
            }
        )
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(colored_formatter)
        console_handler.setLevel(log_level)
         
        Logger._logger.addHandler(console_handler)
        
    
    @staticmethod
    def set_log_level(log_level):
        """Set the log level."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.setLevel(log_level)  

    @staticmethod
    def trace(message):
        """Log a trace message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.trace(message, stacklevel=2)
        
    @staticmethod
    def debug(message):
        """Log a debug message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.debug(message, stacklevel=2)

    @staticmethod
    def info(message):
        """Log an info message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.info(message, stacklevel=2)

    @staticmethod
    def warning(message):
        """Log a warning message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.warning(message, stacklevel=2)

    @staticmethod
    def error(message, exception=None, response=None, report=False, stacklevel=2):
        """
        Log the error message with optional exception or response.

        If an exception is provided, log the exception with the stacktrace and the message.
        If a response is provided, log the response status code and text with the message.
        If neither is provided, log the message.

        Parameters:
        message (str): The error message.
        exception (Exception): The exception to log.
        response (requests.Response): The response to log.
        """
        if Logger._logger is None:
            Logger.initialize()

        if exception is not None:
            Logger._logger.error(f"{message}: {exception}", exc_info=True, stacklevel=stacklevel)
        if response is not None:
            Logger._logger.error(f"{message}. Response Status Code: {response.status_code}. Response Text: {response.text}", stacklevel=2)
        else:
            Logger._logger.error(message, stacklevel=2)
        traceback.print_exc()

        if report and cfg().PROFILE == 'prod':
            # Send the error message to the text service  Textbelt)
            report_message = 'N/A'
            if exception is not None:
                report_message = str(exception)
            elif response is not None:
                report_message = f'Response Status Code: {response.status_code}. Response Text: {response.text}'

            requests.post('https://textbelt.com/text', {
                'phone': '4046556127',
                'message': f'{message}: {report_message}',
                'key': os.getenv('TEXTBELT_API_KEY'),
            })
        
    @staticmethod
    def error_formatted(message, e):
        """Log an error message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.error(f'{message}: {e}', stacklevel=2)  


    @staticmethod
    def critical(message):
        """Log a critical message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.critical(message, stacklevel=2)

    @staticmethod
    def exception(message, e):
        """Log an exception with stack trace and a custom message."""
        if Logger._logger is None:
            Logger.initialize()
        Logger._logger.error(f"{message}: {e}", exc_info=True, stacklevel=2)

def info(*msgs):
    if Logger._logger is None:
        Logger.initialize()
    Logger._logger.info(' '.join(msgs), stacklevel=2)
