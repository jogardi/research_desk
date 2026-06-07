from shared.config import Config
from shared.logger import Logger

# Define production environment detection
IS_PROD = Config.IS_PROD
Logger.info("++++IS_PROD: "+ str(IS_PROD))
# Additional environment helpers
IS_DEV = not IS_PROD
IS_TEST = Config.PROFILE == 'test'
IS_DEBUG = Config.DEBUG_MODE

def get_environment_name() -> str:
    """Get a human-readable environment name."""
    if IS_PROD:
        return "Production"
    elif IS_TEST:
        return "Test"
    else:
        return "Development" 