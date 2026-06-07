import unittest
import os
import shutil
import glob

from pathlib import Path

from shared.logger import Logger
from shared.config import Config 
from shared.embedding.sentence_transformer import SentenceTransformerModel
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths
   

from kb_builder.process_main import main as process_main

from kb_builder.persistence.document_sqlite import *
from kb_builder.persistence.category_sqlite import *
from kb_builder.persistence.kb_artifact import *

from kb_builder.vector_db.hnswlib import HnswlibVectorDB

    
class TestKBBuilder(unittest.TestCase): 
    # kb_builder_config.profile('test') 
    
    SAMPLE_CATEGORY = 'Sample/Category'
    REFERENCE_CATEGORY = 'Reference'  
    TRANSFORM_CATEGORY = 'Transform'  
    
    embedding_model = SentenceTransformerModel()
    dim = embedding_model.dim()
 
      
          
    def clean(self):   
        # db folder
        db_path = Path(Config.DB_FOLDER)    
        shutil.rmtree(db_path,ignore_errors=True)
        shutil.copytree(str(db_path) + '_init', db_path) 
        
        #kb folder
        kb_path = Path(Config.KNOWLEDGEBASE_FOLDER)    
        shutil.rmtree(kb_path, ignore_errors=True) 
  
        #staging folder
        staging_path = Path(Config.STAGING_FOLDER)    
        shutil.rmtree(staging_path, ignore_errors=True) 
        shutil.copytree(str(staging_path) + '_init', staging_path) 
        
    def test_duplicate_or_retry_scenario(self):
        # clean
        self.clean()
       
        # only keep sample category
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.REFERENCE_CATEGORY, ignore_errors=True) 
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.TRANSFORM_CATEGORY, ignore_errors=True)
        
        # first process
        process_main() 
        
        # clear the artificact that is not a duplicate
        not_duplicate_artifact = 'sample-document.pdf'
        not_duplicate_document_id = find_document(not_duplicate_artifact, self.SAMPLE_CATEGORY)[0]
        delete_document(not_duplicate_artifact, self.SAMPLE_CATEGORY) # won't be triggered as a duplice        
        delete_category_chunks_for_document(not_duplicate_document_id) 
        kb_file_path = Config.KNOWLEDGEBASE_FOLDER + '/' + self.SAMPLE_CATEGORY + '/' + not_duplicate_artifact   
        delete_kb_artifact(kb_file_path) 
        staging_path = Path(Config.STAGING_FOLDER)    
        shutil.rmtree(staging_path, ignore_errors=True) 
        shutil.copytree(str(staging_path) + '_init', staging_path) 
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.REFERENCE_CATEGORY, ignore_errors=True) 
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.TRANSFORM_CATEGORY, ignore_errors=True)
     
        # second process
        process_main() 
        
        # assert log file
        log_file_path = self.get_log_file_path() 
        line_count = 0
        with open(log_file_path, 'r') as file:
            for line in file:
                line_count += 1
                self.assertTrue('WARN: No file extension' in line or 'WARN: Document already exists. Reprocessing.' in line)     
                 
        self.assertTrue(line_count, 2) 
        
        self.assert_processing(self.SAMPLE_CATEGORY, 2)
   
    def test_update_category_happy(self):
        new_file_name = 'newfile.pdf'
        
        # clean
        self.clean()
       
        # only keep sample category
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.REFERENCE_CATEGORY, ignore_errors=True) 
        shutil.rmtree(Config.STAGING_FOLDER + '/' + self.TRANSFORM_CATEGORY, ignore_errors=True)
        
        #process first time
        process_main()

        CategoryDBFilePaths.generate_file_paths(self.SAMPLE_CATEGORY);
        # count rows before process
        vector_db = HnswlibVectorDB(CategoryDBFilePaths.hnswlib_file_path, self.dim)
        vectordb_before_count = vector_db.item_count()
        categorydb_before_count = row_count_category()

        # copy one of the documents to a new file
        filenames = os.listdir(f'{Config.KNOWLEDGEBASE_FOLDER}/{self.SAMPLE_CATEGORY}')
        source_document_path = os.path.join(Config.KNOWLEDGEBASE_FOLDER, self.SAMPLE_CATEGORY, filenames[1])
        target_document_path = os.path.join(Config.STAGING_FOLDER, self.SAMPLE_CATEGORY, new_file_name)
        
        shutil.copy(source_document_path,target_document_path)
        path = Path(target_document_path)
        
        # process second time
        process_main()  
        
        # count rows after process
        vectordb_after_count = vector_db.item_count()
        categorydb_after_count = row_count_category()


        # assert log file
        log_file_path = self.get_log_file_path()   
        line_count = 0
        with open(log_file_path, 'r') as file:
            for line in file:
                line_count += 1
                self.assertTrue('WARN: No file extension' in line) 
                 
        self.assertTrue(line_count, 2) 

        
        self.assertGreater(vectordb_after_count, vectordb_before_count) 
        self.assertGreater(categorydb_after_count, categorydb_before_count)
        self.assertEqual(vectordb_after_count, categorydb_after_count)
   
        document = find_document(new_file_name, self.SAMPLE_CATEGORY)   
        self.assertIsNotNone(document)
  
    
    def test_new_categories_happy(self):
        # clean
        self.clean()
        
        number_of_artifacts = 7
               
        # process
        process_main()
        
        # assert log file
        log_file_path = self.get_log_file_path() 
        line_count = 0
        with open(log_file_path, 'r') as file:
            for line in file:
                line_count += 1
                self.assertTrue('WARN: No file extension' in line) 
                 
        self.assertTrue(line_count, 2) 
        
        self.assert_processing(self.SAMPLE_CATEGORY, number_of_artifacts)
        self.assert_processing(self.REFERENCE_CATEGORY, number_of_artifacts)
        self.assert_processing(self.TRANSFORM_CATEGORY, number_of_artifacts)
       
    def assert_processing(self, category, number_of_artifacts): 
        #assert artifacts moved
        kb_folder = Path(Config.KNOWLEDGEBASE_FOLDER)    
        kb_artifact_count = self.count_files_recursively(kb_folder)    
        self.assertEqual(number_of_artifacts, kb_artifact_count)
        
        staging_folder = Path(Config.STAGING_FOLDER)   
        staging_artifact_count = self.count_files_recursively(staging_folder)    
        self.assertEqual(1, staging_artifact_count) #the one file is the log file

        # assert document table
        document_count = count_documents()
        self.assertEqual(document_count,  number_of_artifacts)               
        
        # assert category
        CategoryDBFilePaths.generate_file_paths(category)
        exists = exists_category_database()
        self.assertTrue(exists)
        
        #assert vector db 
        row_count = row_count_category() 
        self.assertGreater(row_count, 0)        
        vector_db_size = os.stat(CategoryDBFilePaths.hnswlib_file_path).st_size
        self.assertGreater(vector_db_size, 0)  
      
    @staticmethod
    def get_log_file_path():
        pattern = os.path.join(Config.STAGING_FOLDER + '/log', '*.log')
        log_files = glob.glob(pattern)
        return log_files[0]     
    
        
    @staticmethod
    def count_files_recursively(directory):
        path = Path(directory)
        # Count all files and folders matching the pattern recursively        
        file_count = sum(1 for item in path.rglob('*') if item.is_file() and item.name != '.DS_Store')
        return file_count
  
        
        
 
        
        

        
       
             

if __name__ == '__main__':
    unittest.main()
