import os
import shutil

from pathlib import Path

from shared.logger import Logger
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths

from shared.config import Config


class DBFileUtil:
    def __init__(self):
        # sqlite db
        self.sqlite_path = Path(CategoryDBFilePaths.sqlite_file_path) 
        self.sqlite_backup_path = f"{self.sqlite_path}_{Config.FORMATTED_DATETIME}.backup"
        
        # document db
        self.document_sqlite_path = Path(CategoryDBFilePaths.document_sqlite_file_path)
        self.document_sqlite_backup_path =  f"{self.document_sqlite_path}_{Config.FORMATTED_DATETIME}.backup"

        # hnswlib db
        self.hnswlib_path = Path(CategoryDBFilePaths.hnswlib_file_path)
        self.hnswlib_backup_path = f"{self.hnswlib_path}_{Config.FORMATTED_DATETIME}.backup"
        
    def backup_db_files(self): 
        # backup the original sqlite file
        if self.sqlite_path.exists():
            shutil.copy2(self.sqlite_path, self.sqlite_backup_path) 
            
        # backup the original document file
        if self.document_sqlite_path.exists():
            shutil.copy2(self.document_sqlite_path, self.document_sqlite_backup_path) 

        # backup the original hnswlib file
        if self.hnswlib_path.exists():
            shutil.copy2(self.hnswlib_path, self.hnswlib_backup_path) 
            
        Logger.info(f'Database files backed up for category {CategoryDBFilePaths.category}')  

    def delete_backup_db_files(self):
        os.remove(self.sqlite_backup_path)
        os.remove(self.document_sqlite_backup_path)
        os.remove(self.hnswlib_backup_path)

        
        Logger.info(f'Backup Database files deleted for category {CategoryDBFilePaths.category}')    
        

    # def restore_db_files(self):
    #     # restore the original sqlite file
    #     if self.sqlite_backup_path.exists():
    #         shutil.copy2(self.sqlite_backup_path, self.sqlite_path)
           
    #     if self.document_sqlite_backup_path.exists():
    #         shutil.copy2(self.document_sqlite_backup_path, self.document_sqlite_path)

    #     # restore the original hnswlib file 
    #     if self.hnswlib_backup_path.exists():
    #         shutil.copy2(self.hnswlib_backup_path, self.hnswlib_path)

    #     # restore the original annoy file   
    #     if self.annoy_backup_path.exists():
    #         shutil.copy2(self.annoy_backup_path, self.annoy_path)
            
    #     Logger.info(f'\t--- Database files restored for category {CategoryDBFilePaths.category}')   

        # delete the backup files
        #self.sqlite_backup_path.unlink(missing_ok=True) 
        #self.hnswlib_backup_path.unlink(missing_ok=True)
        #self.annoy_backup_path.unlink(missing_ok=True)
