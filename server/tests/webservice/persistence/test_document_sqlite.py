import unittest
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from shared.logger import Logger
from shared.db_support.enum_flag_reason import FlagReason  
from webservice.categoryDBFilePaths import CategoryDBFilePaths

from webservice.search.semantic_search import semantic_search
from webservice.persistence.document_sqlite import DocumentSqlite


class TestDocumentSqlite(unittest.TestCase):

    def setUp(self):
        categories = 'Test/Sample/Category', 
        self.categoryDBFilePaths = CategoryDBFilePaths()   
        self.categoryDBFilePaths.generate_file_paths(categories[0])
        self.db = DocumentSqlite()
        
        
    def get_document_id(self) -> int:    
        all_chunks = semantic_search(self.categoryDBFilePaths, 'What is the sample topic')  
        
        first_chunk = all_chunks[0] 
        
        return first_chunk['documentID']
          
    def test_get_document_filename_happy(self):
        document_id = self.get_document_id()
             
        result = self.db.get_document_filename(document_id)
        
        self.assertIsNotNone(result)    
        
    def test_flag_document_happy(self):
        document_id = self.get_document_id()
        
        # flag the document
        self.db.flag_document(document_id, 'COPYWRIGHT', '010', 'Test')
        result = self.db.get_document_filename(document_id) 
        self.assertIsNone(result) 
        
        self.assertTrue(self.db.is_flagged_document(document_id))    
        self.assertFalse(self.db.is_flagged_document(-1))
        
        # unflag the document   
        self.db.unflag_document(document_id)  
        self.assertFalse(self.db.is_flagged_document(document_id)) 
        result = self.db.get_document_filename(document_id) 
        self.assertIsNotNone(result)  
        
        #reflag dcoument to test cache
        self.db.flag_document(document_id, 'COPYWRIGHT', '010', 'Test')
        self.assertTrue(self.db.is_flagged_document(document_id)) 
        
        #clear flag
        self.db.unflag_document(document_id)     
 
          
        
          

    
   

if __name__ == '__main__':
    unittest.main()
