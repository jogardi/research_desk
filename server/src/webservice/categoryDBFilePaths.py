# import sys_path # Add the "ai_pipeline" directory to the sys.path

from pathlib import Path
from shared.kb_folders import DB_FOLDER

class CategoryDBFilePaths:
    """
    A class to generate the database file paths for the given category.
    This version requires kb_name and uses user-specific knowledge base folders.
    """

    def __init__(self, kb_name: str):
        """ Constructor """
        self.kb_name: str = kb_name
        self.category: str = None
        self.category_name: str = None # category name with '/' replaced by '__'

        self.sqlite_file_path: str = None    # The SQLite database file path for the category
        self.hnswlib_file_path: str = None   # The Hnswlib vector database file path for the category
        self.annoy_file_path: str = None     # The Annoy vector database file path for the category
        
        self.document_sqlite_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 

    def generate_file_paths(self, category: str) -> None:
        """
        Generate the database file paths for the given category using kb_name.

        Params:
            category: str: The category name. 
                            This is a leaf folder path under the knowledge base folder tree. 
                            For example: "Pre History/Ancient Civilizations/Egypt/Pyramids"
        Returns: None
        """
        self.category = category
        self.category_name = category.replace('/', '__')

        # Use kb_name-specific database folder
        db_folder = DB_FOLDER(self.kb_name)

        path = Path(db_folder) / 'sqlite_db' / f'{self.category_name}.db'
        self.sqlite_file_path = str(path)
        
        path = Path(db_folder) / 'vector_db' / 'hnswlib' / f'{self.category_name}.bin'
        self.hnswlib_file_path = str(path)
        
        path = Path(db_folder) / 'vector_db' / 'annoy' / f'{self.category_name}.ann'
        self.annoy_file_path = str(path)
        print("db paths", self.sqlite_file_path, self.hnswlib_file_path, self.annoy_file_path)

        path = Path(db_folder) / 'vector_db' / 'lucene' / f'{self.category_name}'
        self.lucene_dir_path = str(path) 