import unittest
import os
import glob
import shutil

from pathlib import Path

from shared.config import Config
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths

from shared.logger import Logger   
 


from kb_builder.persistence.db_file_util import DBFileUtil

class TestDBFileUtil(unittest.TestCase):
    categories = ['Test/Sample/Category']
    # kb_builder_config.profile('test')  
    CategoryDBFilePaths.generate_file_paths(categories[0]);       
     
         
    def clean(self):   
        db_path = Path(Config.DB_FOLDER)    
        shutil.rmtree(db_path,ignore_errors=True)
        shutil.copytree(str(db_path) + '_test_backup', db_path)       
        
    def test_backup_delete(self):
        self.clean()
        
        # get file sizes
        sqlite_path = Path(CategoryDBFilePaths.sqlite_file_path)
        sqlite_size = os.stat(sqlite_path).st_size
        document_sqlite_path = Path(CategoryDBFilePaths.document_sqlite_file_path)  
        document_sqlite_size = os.stat(document_sqlite_path).st_size    
        hnswlib_path = Path(CategoryDBFilePaths.hnswlib_file_path)  
        hnswlib_size = os.stat(hnswlib_path).st_size    
    
        # backup
        DBFileUtil().backup_db_files()
        
        # get backup file of sqlite db 
        pattern =  os.path.join(os.path.dirname(sqlite_path), '*.backup')
        matched_files = glob.glob(pattern)
        self.assertTrue(len(matched_files) == 1)
        sqlite_backup_path = matched_files[0]
        sqlite_backup_size = os.stat(sqlite_backup_path).st_size   
        
        # get backup file of document db    
        pattern =  os.path.join(os.path.dirname(document_sqlite_path), '*.backup')
        matched_files = glob.glob(pattern)
        self.assertTrue(len(matched_files) == 1)
        document_sqlite_backup_path = matched_files[0]   
        document_sqlite_backup_size = os.stat(document_sqlite_backup_path).st_size   
        
        # get backup file of hnswlib db
        pattern =  os.path.join(os.path.dirname(hnswlib_path), '*.backup')
        matched_files = glob.glob(pattern)
        self.assertTrue(len(matched_files) == 1)
        hnswlib_backup_path = matched_files[0]   
        hnswlib_backup_size = os.stat(hnswlib_backup_path).st_size  
        
        # assert sizes are the same
        self.assertEqual(sqlite_size, sqlite_backup_size)
        self.assertEqual(document_sqlite_size, document_sqlite_backup_size)
        self.assertEqual(hnswlib_size, hnswlib_backup_size)
        
        # delete backup 
        DBFileUtil().delete_backup_db_files()
        
        self.assertFalse(os.path.exists(sqlite_backup_path))
        self.assertFalse(os.path.exists(document_sqlite_backup_path))  
        self.assertFalse(os.path.exists(hnswlib_backup_path))
        
        
        
        
          
       

if __name__ == '__main__':
    unittest.main()
