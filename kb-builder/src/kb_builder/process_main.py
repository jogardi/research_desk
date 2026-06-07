import os
import google.generativeai as genai
import re
import io
import sys
import concurrent.futures
from typing import List, Tuple

from pathlib import Path
from datetime import datetime

#shared
from shared.config import Config, load_cli_args
load_cli_args()
from shared.category_tree import get_folders
from shared.sqlite import SQLite
from shared.embedding.sentence_transformer import SentenceTransformerModel
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths, dbs
from kb_builder.util.filename_util import sanitize_and_rename_file, sanitize_name, validate_name
from kb_builder.summarize.auto_categorize import summarize_categories

# pre processors
from kb_builder.pre_processor.text_file_processor import process_text
from kb_builder.pre_processor.pdf_file_processor import process_pdf
from kb_builder.pre_processor.docx_file_processor import process_docx
from kb_builder.hparams_config import hpc
# persistence
from kb_builder.persistence.db_file_util import DBFileUtil
from kb_builder.persistence.kb_artifact import delete_kb_artifact, backup_kb_artifact, deploy_kb_artifact, undeploy_kb_artifact, failed_kb_artifact
from kb_builder.persistence.document_sqlite import find_document, delete_document, insert_category
from kb_builder.persistence.category_sqlite import delete_category_chunks_for_document
from kb_builder.vectorize.vectorize import process as vectorize
from kb_builder.vectorize.vectorize import add_document
from kb_builder.vectorize.vectorize import add_category_vector

#logging
from shared.logger import Logger
from kb_builder.util.log_util import log_processing_warning, log_processing_error, set_log_file_path


import os
from kb_builder.load_env import load_env

# Load environment variables from the kb-builder .env (override any already-set env vars)
load_env(override=True)

# filter our warning messages
# warnings.filterwarnings("ignore", category=DeprecationWarning, module="imageio_ffmpeg._utils")
# warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")



def pre_process_artifact(file_extension: str, file_path: str):  
    # Convert file extension to lowercase for case-insensitive comparison
    file_extension = file_extension.lower()
    
    if file_extension == "":
        log_processing_warning(file_path, 'None', "No file extension")
        return None
    
    converted_to_text = None
    
    try:
        if file_extension in Config.AUDIO_FILE_EXTENSIONS:
            from kb_builder.pre_processor.audio_file_processor import process_audio 
            converted_to_text = process_audio(file_path)
        elif file_extension in Config.VIDEO_FILE_EXTENSIONS:
            from kb_builder.pre_processor.video_file_processor import process_video
            converted_to_text = process_video(file_path, Config.WORK_FOLDER)
        elif file_extension in Config.TEXT_FILE_EXTENSIONS:
            converted_to_text = process_text(file_path)
        elif file_extension in Config.PDF_FILE_EXTENSIONS:
            converted_to_text = process_pdf(file_path)
        elif file_extension in Config.DOCX_FILE_EXTENSIONS:
            converted_to_text = process_docx(file_path)
        elif file_extension in Config.IGNORE_FILE_EXTENSIONS:
            log_processing_warning(file_path, file_extension, "Ignoring file type")
        else:
            log_processing_warning(file_path, file_extension, "Invalid file type") 

    except Exception as e: # do not raise because I just want to skip this file
        log_processing_error(file_path, file_extension, str(e))
        Logger.file(f"Failed to process file: {file_path}")
        return None
        
    if converted_to_text is None:
        Logger.file(f"Failed to process file: {file_path}")
        return None
    
    return converted_to_text 

def check_and_resolve_duplicate_orphaned_artifact(file_path: str, file_name: str, file_extension, category: str):
    document = find_document(file_name, category);
    document_id = document[0]

    if document_id is not None:
        log_processing_warning(file_path, file_extension, f'Document already exists. Reprocessing.')
        
        delete_category_chunks_for_document(document_id)
        delete_document(file_name, category) #if prior step fail then this will be found when trying to load the document
        
        success = undeploy_kb_artifact(file_name, category)
        if not success:
            log_processing_warning(file_path, file_extension, "Undeploying artifact failed")

        
        kb_file_path = Config.KNOWLEDGEBASE_FOLDER + '/' + category + '/' + file_name   
        success = delete_kb_artifact(kb_file_path) #if prior step fail then this will be found when trying to load the document
        if not success:
            log_processing_warning(file_path, file_extension, "Deleting artifact failed")
            

def vectorize_blocks(pdf_blocks: List[str], file_name: str, category: str, document_id: int) -> List[Tuple[bool, str]]:
    max_workers = 1
    from shared.hparams_config import hpc as shared_hpc
    if shared_hpc().EMBED_MODEL.startswith('hug'):
        max_workers = 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(
            lambda block: vectorize(block, str(file_name), category, document_id),
            pdf_blocks
        ))
    return results

def process():
    if not os.path.exists(Config.STAGING_FOLDER + '/log/'):
        os.makedirs(Config.STAGING_FOLDER + '/log/')
    if not os.path.exists(Config.WORK_FOLDER):  
        os.makedirs(Config.WORK_FOLDER)

    main(Config.ARGV_PARAM1)
              
        
def main(source: str):
    Logger.info(f"*** KB Builder - Starting at {datetime.now()} ***")  

   # process all files in the staging folder
    folders = get_folders(Config.STAGING_FOLDER)
    from shared.config import cfg
    
    raw_text_f = open(os.path.join(cfg().LOG_FOLDER, 'knowledge_raw_text.txt'), 'a')
 
    for folder in folders:
        # get the category
        category = folder['path'][len('Root/'):]
       
        if category == 'log':
            continue   
        
        Logger.info(f"Processing category: {category}") 
        Logger.file(f"Category: {category}")
        CategoryDBFilePaths.generate_file_paths(category)
        
        #backup the category db files
        db_file_util = DBFileUtil()
        db_file_util.backup_db_files()
        
        # for each file in the category folder
        for root, dirs, files in os.walk(Path(f"{Config.STAGING_FOLDER}/{category}")):
            for file_name in files:
                Logger.info(f"Processing file: {file_name} at {datetime.now()}") 
                try:
                    file_path = os.path.join(root, file_name)
                    file_extension = os.path.splitext(file_name)[1].lower()  # Convert to lowercase
                    check_and_resolve_duplicate_orphaned_artifact(file_path, str(file_name), file_extension, category)

                    pdf_blocks = pre_process_artifact(file_extension, file_path) 
                    if pdf_blocks is None:
                        Logger.file(f"Failed to process file: {file_name}")
                        continue
                    for block in pdf_blocks:
                        # Handle both PDFBlock and VideoBlock types
                        if hasattr(block.region, 'page_number'):
                            # PDFBlock
                            raw_text_f.write(f"Processing file: {file_name} page {block.region.page_number}\n\n")
                        elif hasattr(block.region, 'start_time'):
                            # VideoBlock
                            raw_text_f.write(f"Processing file: {file_name} time {block.region.start_time:.2f}s - {block.region.end_time:.2f}s\n\n")
                        else:
                            raw_text_f.write(f"Processing other file type file: {file_name}\n\n")
                        raw_text_f.write(f"{block.text}\n\n-------------------\n\n")
                        raw_text_f.flush()
                    document_id = add_document(pdf_blocks, str(file_name), category, source)
                    
                    # Parallelize vectorization
                    results = vectorize_blocks(pdf_blocks, str(file_name), category, document_id)
                    if not all(results):
                        raise Exception("Vectorization failed")
                        
                    success = save_kb_artifact(file_path, category)
                    if not success:
                        raise Exception("Deploying artifact failed")                                   
                        
                    success = delete_kb_artifact(file_path)
                    if not success:
                        raise Exception("Removing artifact failed")
   
                except Exception as e: # only catching unexpected exceptions
                    Logger.file(f"Failed to process file: {file_name}")
                    log_processing_error(file_path, file_extension, str(e))
                    failed_kb_artifact(file_path, category)

                Logger.file(f"Processed file: {file_name}")

                if hpc().mini_run:
                    sys.exit(1)

                        
            dirs[:] = []  # don't recurse into subdirectories      
    
    Logger.info(f"*** KB Builder - Done at {datetime.now()} ***")
  
def save_kb_artifact(file_path: str, category: str) -> bool:
    success = deploy_kb_artifact(file_path, category)
    if not success:
        return False
        
    success = backup_kb_artifact(file_path, category)
    return success
    

def get_folders(root_folder: str):
    folders = []
    id = 0

    # Walk through the directory structure
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Check if this is a leaf directory (no sub-directories)
        # Get the relative path of the leaf folder
        folder = os.path.relpath(dirpath, root_folder) 
        if folder == '.':   
            continue
        # check if folder has files
        if not filenames:
            continue
        id += 1
        folders.append({'id': str(id), 'path': 'Root/' + folder})

    return folders




if __name__ == '__main__':
    if not sys.argv.__len__() != 6:
        print("Usage: python process_main.py --profile --artifact_source --rootfolder --stagingsubfolder")
        sys.exit(1)
 
    root_folder = Config.ARGV_PARAM2
    
    Config.ROOT_FOLDER = root_folder
    print('Root Folder: ' + root_folder) 
    Config.KNOWLEDGEBASE_FOLDER = Config.ROOT_FOLDER + '/knowledgebase' 
    Config.STAGING_FOLDER = Config.ROOT_FOLDER + '/staging/' + Config.ARGV_PARAM3 
    
    Config.LOG_FOLDER = Config.ROOT_FOLDER + '/log' 
    set_log_file_path(Config.ROOT_FOLDER + '/log/kb_builder_' + Config.FORMATTED_DATETIME + '.log')
    #print all folders
    print('Root Folder: ' + Config.ROOT_FOLDER)
    print('Knowledgebase Folder: ' + Config.KNOWLEDGEBASE_FOLDER)
    print('Staging Folder: ' + Config.STAGING_FOLDER)
    print('Work Folder: ' + Config.WORK_FOLDER)
    print('Failed Folder: ' + Config.FAILED_FOLDER)
    print('Log Folder: ' + Config.LOG_FOLDER)
    
    process()
    summarize_categories()

