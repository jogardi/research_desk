import unittest
import os

from pathlib import Path

from shared.config import Config
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths

from kb_builder.persistence.document_sqlite import *
from kb_builder.persistence.category_sqlite import *
from kb_builder.persistence.kb_artifact import *
from shared.logger import Logger

#test if duplicate filename  
#test if no change to files
# in test_artifact_happy need to clean out the knowledgebase folder
class TestPersistence(unittest.TestCase):
    # kb_builder_config.profile('test') 
     
    test_category_name = 'test_category_name'  
    test_file_name = 'test_file_name'
    CategoryDBFilePaths.generate_file_paths(test_category_name);    
       
    
        
    def test_document_happy(self):
        #clean
        delete_category_documents(self.test_category_name)   
        
        # crud
        document_id = insert_document(self.test_file_name, self.test_category_name)  
        self.assertIsNotNone(document_id)
        found_document_id = find_document(self.test_file_name, self.test_category_name)
        self.assertEqual(document_id, found_document_id[0])
        delete_document(self.test_file_name, self.test_category_name)  
        document_id = find_document(self.test_file_name, self.test_category_name)
        self.assertIsNone(document_id[0])
        
        #delete by category
        insert_document(self.test_file_name, self.test_category_name) 
        insert_document(self.test_file_name + '1', self.test_category_name)  
        delete_category_documents(self.test_category_name)  
        
        document_id = find_document(self.test_file_name, self.test_category_name)   
        self.assertIsNone(document_id[0])
        document_id = find_document(self.test_file_name + '1', self.test_category_name)   
        self.assertIsNone(document_id[0])
         
        
    def test_category_happy(self):
        #clean 
        sqlite_path = Path(CategoryDBFilePaths.sqlite_file_path) 
 
        if os.path.isfile(sqlite_path):  
            os.remove(sqlite_path)
            
        exists = exists_category_database()   
        self.assertFalse(exists) 
        
        # create table
        create_category_database()   
        
        exists = exists_category_database()   
        self.assertTrue(exists) 

        # insert chunkcs
        chunks = ['chunk1', 'chunk2']   
        document_id = 5
        chunck_ids = insert_chunks(chunks, document_id)  
        self.assertEqual(len(chunck_ids), 2)
        row_count = row_count_category() 
        self.assertEqual(row_count, 2)  
        
        # delete chunks
        delete_category_chunks_for_document(document_id)
        row_count = row_count_category() 
        self.assertEqual(row_count, 0)
        
        # clean
        os.remove(sqlite_path)
 
        
    def test_artifact_happy(self):
        kb_path = Config.KNOWLEDGEBASE_FOLDER 
        staging_path = Config.STAGING_FOLDER      
        artifact_name = 'sample-document.pdf' 
        category = 'Sample/Category' 
        
        # refresh staging folder 
        shutil.rmtree(Path(staging_path) , ignore_errors=True) 
        shutil.copytree(staging_path + '_init', staging_path)   
        
        source_path = staging_path + '/' + category + '/' + artifact_name
        target_path = kb_path + '/' + category + '/' + artifact_name  
        
        move_kb_artifact(source_path, category)
        if not os.path.exists(target_path):
            self.fail('Artifact not moved') 
            
        if os.path.exists(source_path):
            self.fail('Artifact not moved')   
        
        delete_kb_artifact(target_path) 
        if os.path.exists(target_path):
            self.fail('Artifact not remove')   

        
        
        
        
       

if __name__ == '__main__':
    unittest.main()
