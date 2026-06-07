from fastapi import APIRouter, HTTPException, Depends
from shared.category_tree import get_folders_from_root_folder
from webservice.schemas.vector import (
    GenerateDatabasesRequest, GenerateDatabasesResponse, 
    DatabaseGenerationStatusResponse, IsRunningResponse, AbortResponse
)
from webservice.session_manager import protected
import json
import subprocess
import signal
import os

# FastAPI Router for all vector database generation routes
router = APIRouter(tags=["vector"], dependencies=[Depends(protected)])

#
# Vector and SQLite database generation routes
#

# Variables to track the database generation process
db_generator_process = None

# Get the path to the kb-builder project folder
kb_builder_folder = os.getcwd().replace('webservice/src/webservice', 'kb-builder')

# Start the database generation process
@router.post("/api/generate_databases/start", response_model=GenerateDatabasesResponse)
def generate_databases_start(request: GenerateDatabasesRequest):
    """Start the database generation process."""
    global db_generator_process

    is_process_running = db_generator_process is not None and db_generator_process.poll() is None
    if is_process_running:
        raise HTTPException(status_code=400, detail="A database generation process is already running.")

    categoryIDs = request.categoryIDs
    print(f'categoryIDs: {categoryIDs}')

    if not categoryIDs:
        raise HTTPException(status_code=400, detail="No category IDs provided.")

    # Get the category paths
    categories = []
    all_categoriesPaths = get_folders_from_root_folder()
    for categoryID in categoryIDs:
        for category in all_categoriesPaths:
            if category['id'] == categoryID:
                categories.append(category['path'][5:])
                break
    print(categories)

    # is status.json file does not exist, create it:
    if not os.path.exists('status.json'):
        with open('status.json', 'w') as f:
            json.dump({}, f)

    # Initialize the status file to empty
    with open('status.json', 'w') as f:
        json.dump({}, f)

    # Spawn db_generation.py as a separate process    
    db_generator_process = subprocess.Popen(['python', f'{kb_builder_folder}/src/kb_builder/process_main.py'] + categories)
        
    return GenerateDatabasesResponse(message="Database generation started.")

# Abort the database generation process
@router.post("/api/generate_databases/abort", response_model=AbortResponse)
def generate_databases_abort():
    """Abort the database generation process."""
    global db_generator_process
    is_process_running = db_generator_process is not None and db_generator_process.poll() is None
    if not is_process_running:
        raise HTTPException(status_code=400, detail="No database generation process is running.")

    # Send the interrupt signal to the process
    db_generator_process.send_signal(signal.SIGINT) # Send the interrupt signal to the process 
    return AbortResponse(message="Database generation aborted.")

# Check if the database generation process is running
@router.get("/api/generate_databases/is-running", response_model=IsRunningResponse)
def generate_databases_is_running():
    """Check if the database generation process is running."""
    global db_generator_process

    # Check if the process is still running or has terminated
    is_process_running = db_generator_process is not None and db_generator_process.poll() is None
    if not is_process_running:
        db_generator_process = None
        print("Process is not running!")
    return IsRunningResponse(isRunning=is_process_running)

# Get the status of the database generation process
@router.get("/api/generate_databases/status", response_model=DatabaseGenerationStatusResponse)
def generate_databases_status():
    """Get the status of the database generation process."""
    global db_generator_process

    is_process_running = db_generator_process is not None and db_generator_process.poll() is None
    
    try:
        with open('status.json', 'r') as f:
            current_status = json.load(f)
    except FileNotFoundError:
        current_status = {'error': 'Status file not found. No process has been started yet.'}
    
    return DatabaseGenerationStatusResponse(isRunning=is_process_running, status=current_status)

# ----------------------------------------------------
# generate/regenerate the vector DB and the SQLite DB - NOT USED
# @router.get('/api/generate_databases')
# def generateDatabases():
#     categoryIDs = request.args.get('categoryIDs', default = '', type = str).split(',')
#     paths = []
#     for categoryID in categoryIDs:
#         for category in cache.all_categoriesPaths:
#             if category['id'] == categoryID:
#                 paths.append(category['path'][5:])
#                 break
#     print(paths)
#     return {'status': 'success'}

# ----------------------------------------------------

