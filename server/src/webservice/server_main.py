# import sys_path

from shared.config import   Config, load_cli_args
# Read the command line arguments and load the configuration into Config
load_cli_args()

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
# Import FastAPI WebSockets (new implementation)
from webservice.websockets_fastapi import init_fastapi_websockets
import uvicorn
import os
import sys
import ssl

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# os.environ['PROFILE'] = 'test'

from shared.logger import Logger  

# Import security middleware
from webservice.security_middleware import SecurityMiddleware

# Import router configuration
from webservice.include_routers import include_routers

# Import Cache for connection management
from webservice.cache.cache import Cache

# Import runtime environment detection
from webservice.runtime_env import IS_PROD, get_environment_name

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown events."""
    # Startup
    Logger.info("*** Lifespan: FastAPI application starting up...")
    Logger.info(f"*** Lifespan: Running in {get_environment_name()} mode")
    
    # Initialize cache connections
    Cache.connect()
    
    yield
    
    # Shutdown
    Logger.info("*** Lifespan: FastAPI application shutting down...")
    
    # Close cache connections
    Cache.close()

#
# Initialize FastAPI app
#
app = FastAPI(
        title="Research Desk API",
        description="Research Desk FastAPI Application",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=None if IS_PROD else "/docs",
        redoc_url=None if IS_PROD else "/redoc",
        openapi_url=None if IS_PROD else "/openapi.json"
)

#
# Mount the static folder 
#
root_folder = os.path.dirname(__file__) 

# Store static folder path for later use in production
static_folder = None
if IS_PROD: 
    static_folder = os.path.abspath(os.path.join(root_folder, "../../static/dist/spa"))
    if not os.path.exists(static_folder):
        Logger.error(f"Critical: Static SPA folder not found: {static_folder}")
        Logger.error("Production mode requires the built frontend at static/dist/spa")
        raise FileNotFoundError(f"Required static folder not found: {static_folder}")

# other profiles - use the "static" folder and CORS is needed. This is in dev mode.
else: 
    static_folder = os.path.abspath(os.path.join(root_folder, "../../static"))
    if os.path.exists(static_folder):
        app.mount("/static", StaticFiles(directory=static_folder), name="static")
    else:
        Logger.warning(f"Static folder not found: {static_folder}")
        Logger.warning("Development mode: continuing without static files")
 
 #
 # Configure CORS for non-prod profile (dev)
 #
if not IS_PROD:
    # set CORS origins
    cors_origins = [Config.RESEARCH_DESK_URL] 

    if Config.RESEARCH_DESK_URL.startswith('http://localhost:'):
        port = Config.RESEARCH_DESK_URL.split(':')[-1]
        cors_origins.append(f"http://127.0.0.1:{port}")
    elif Config.RESEARCH_DESK_URL.startswith('http://127.0.0.1:'):
        port = Config.RESEARCH_DESK_URL.split(':')[-1]
        cors_origins.append(f"http://localhost:{port}")

    # setup the CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )
    Logger.info(f"*** CORS enabled for {cors_origins}")

# Add security middleware for .env protection and cache control
app.add_middleware(SecurityMiddleware)

# Include all routers
include_routers(app)

# Initialize FastAPI WebSockets
init_fastapi_websockets(app)

# Mount static files in production AFTER routers are included
if IS_PROD and static_folder:
    app.mount("/", StaticFiles(directory=static_folder, html=True, check_dir=False), name="spa") 
#
# Define a global error handler to prevent the server from crashing
#
@app.exception_handler(Exception)
async def handle_exception(request: Request, exc: Exception):
    # Pass through HTTP errors
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    # Log the exception
    print(f"Unhandled exception occurred: {exc}")

    # Return a generic error message
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred. Please try again later."}
    )

#
# Main entry point
#
def main():
    '''
        Main entry point for the application
    '''
    print('*** Starting the server ...')
    
    # Configure SSL if enabled in the config
    ssl_keyfile = None
    ssl_certfile = None
    
    if Config.SSL_ENABLED:
        try:
            # Validate SSL files exist
            if not os.path.exists(Config.SSL_CERT_PATH):
                raise FileNotFoundError(f"SSL certificate not found: {Config.SSL_CERT_PATH}")
            if not os.path.exists(Config.SSL_KEY_PATH):
                raise FileNotFoundError(f"SSL key not found: {Config.SSL_KEY_PATH}")
            
            ssl_certfile = Config.SSL_CERT_PATH
            ssl_keyfile = Config.SSL_KEY_PATH
            Logger.info(f"SSL enabled with cert: {Config.SSL_CERT_PATH}")
        except Exception as e:
            Logger.error("Error loading SSL certificate", exception=e)
            raise e
    
    # Run the FastAPI app with uvicorn: 
    print(f"*** FastAPI - host: {Config.HOST}, port: {Config.PORT}, debug: {Config.DEBUG_MODE}")
    
    if Config.SSL_ENABLED:
        print(f"*** SSL: ENABLED (cert: {Config.SSL_CERT_PATH})")
    else:
        print("*** SSL: DISABLED")
    
    # Use uvicorn with import string for reload mode, app instance otherwise
    if Config.DEBUG_MODE:
        # Use import string for reload mode
        uvicorn.run(
            "webservice.server_main:app",
            host=Config.HOST,
            port=Config.PORT,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            reload=Config.DEBUG_MODE,
            log_level="info"
            # Using compatible websockets 13.1 with uvicorn 0.35.0
        )
    else:
        # Use app instance for production mode
        uvicorn.run(
            app,
            host=Config.HOST,
            port=Config.PORT,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            reload=Config.DEBUG_MODE,
            log_level="info"
            # Using compatible websockets 13.1 with uvicorn 0.35.0
        )

# Initialize app and run the main entry point    
if __name__ == '__main__':
    # Run the main entry point
    main()
    

