import os
import shutil

from shared.config import Config   
from shared.kb_ftp import KBFTP   

from shared.logger import Logger


def delete_kb_artifact(file_path: str) -> bool:
    try:
        os.remove(file_path)
        
        return True
    except Exception as e:
        Logger.error_formatted(f'Error deleting artifact {file_path}', e)
        return False
    
        
def backup_kb_artifact(file_path: str, category: str) -> bool:
    artifact_filename = os.path.basename(file_path) 
    target_file_path_root = Config.KNOWLEDGEBASE_FOLDER + '/' + category
    target_file_path = target_file_path_root + '/' + artifact_filename
    
    try:
        if not os.path.exists(target_file_path_root):
            os.makedirs(target_file_path_root)
            
        shutil.copy(file_path, target_file_path)
        
        return True
    except Exception as e:
        Logger.error_formatted(f'Error moving artifact {file_path} to {target_file_path}', e)
        return False
    

def failed_kb_artifact(file_path: str, category: str) -> bool:
    artifact_filename = os.path.basename(file_path) 
    target_file_path_root = Config.FAILED_FOLDER + '/' + category
    target_file_path = target_file_path_root + '/' + artifact_filename
    
    try:
        if not os.path.exists(target_file_path_root):
            os.makedirs(target_file_path_root)
            
        shutil.move(file_path, target_file_path)
        
        return True
    except Exception as e:
        Logger.error_formatted(f'Error moving artifact {file_path} to {target_file_path}', e)
        return False
    

def deploy_kb_artifact(file_path: str, category: str) -> bool:
    try:
        if (Config.KB_FTP_ENABLED == '1'): 
            KBFTP.deploy_artifact(file_path, category)   
        
        return True
    except Exception as e:
        Logger.error_formatted(f'Error deplolying artifact {file_path}', e)
        return False
    

def undeploy_kb_artifact(filename: str, category: str) -> bool:
    try:
        if (Config.KB_FTP_ENABLED == '1'): 
            KBFTP.undeploy_artifact(filename, category)   
        
        return True
    except Exception as e:
        Logger.error_formatted(f'Error undeplolying artifact {filename} in {category}', e)
        return False
  