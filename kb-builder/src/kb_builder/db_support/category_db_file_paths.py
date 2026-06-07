# import sys_path # Add the "ai_pipeline" directory to the sys.path

from pathlib import Path
from shared.config import Config, cfg
from shared.utils import prep_path, prep_dir
from functools import cached_property

class CategoryDBFilePaths:
    """
    A class to generate the database file paths for the given category.
    """
    category: str = None
    category_name:str  = None # category name with '/' replaced by '__'

    sqlite_file_path: str =  None    # The SQLite database file path for the category
    hnswlib_file_path: str =  None   # The Hnswlib vector database file path for the category
    annoy_file_path: str =  None     # The Annoy vector database file path for the category
    
    document_sqlite_file_path = Path(cfg().DB_FOLDER) / 'document.db' 


    @classmethod
    def generate_file_paths(cls, category: str) -> None:
        """
        Generate the database file paths for the given category.

        Params:
            category: str: The category name. 
                            This is a leaf folder path under the knowledge base folder tree. 
                            For example: "Pre History/Ancient Civilizations/Egypt/Pyramids"
        Returns: None
        """
        cls.category = category
        cls.category_name = category.replace('/', '__')

        path = prep_path(Path(Config.DB_FOLDER) / 'sqlite_db' / f'{cls.category_name}.db')
        cls.sqlite_file_path = str(path)
        
        path = prep_path(Path(Config.DB_FOLDER) / 'vector_db' / 'hnswlib' / f'{cls.category_name}.bin')
        cls.hnswlib_file_path = str(path)

        path = prep_dir(Path(Config.DB_FOLDER) / 'vector_db' / 'lucene' / f'{cls.category_name}')
        cls.lucene_dir_path = str(path)
        
        path = prep_path(Path(Config.DB_FOLDER) / 'vector_db' / 'annoy' / f'{cls.category_name}.ann')
        cls.annoy_file_path = str(path)
        
 



    # The following methods are not used in the current version of the code
    # @classmethod
    # def get_sqlite_file_path(cls, category: str) -> str:
    #     category_name = category.replace('/', '__')
    #     path = Path(Config.DB_FOLDER) / 'sqlite_db' / f'{category_name}.db'
    #     return str(path)
    
    # @classmethod
    # def get_hnswlib_file_path(cls, category: str) -> str:
    #     category_name = category.replace('/', '__')
    #     path = Path(Config.DB_FOLDER) / 'vector_db' / 'hnswlib' / f'{category_name}.bin'
    #     return str(path)
    
    # @classmethod
    # def get_annoy_file_path(cls, category: str) -> str:
    #     category_name = category.replace('/', '__')
    #     path = Path(Config.DB_FOLDER) / 'vector_db' / 'annoy' / f'{category_name}.ann'
    #     return str(path)

class Dbs:
    @cached_property
    def document_db(self):
        from shared.sqlite import SQLite
        path = CategoryDBFilePaths.document_sqlite_file_path
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            create_documents_sql = """CREATE TABLE "DOCUMENT" (
	"ID"	INTEGER,
	"FILE_NAME"	VARCHAR(255) NOT NULL,
	"CATEGORY"	VARCHAR(1024) NOT NULL,
	"FLAG_REASON"	VARCHAR(10),
	"SOURCE" VARCHAR(100) NOT NULL, 
    PROCESSED_ON TEXT,
    "SUMMARY" varchar(2096),
    "TITLE" varchar(255),
    "PUBLICATION_DATE" TEXT,
    "DOC_TYPE VARCHAR(100),
	PRIMARY KEY("ID" AUTOINCREMENT)
)"""
            create_category_sql = """
CREATE TABLE CATEGORY (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CATEGORY VARCHAR(1024) NOT NULL,
    DESCRIPTION VARCHAR(2096) NOT NULL
)"""
            sqldb = SQLite(path)
            with sqldb.connection():
                sqldb.cursor.execute(create_documents_sql)
                sqldb.cursor.execute(create_category_sql)
            return sqldb
        
        return SQLite(path)
    
    @cached_property
    def category_vectors(self):
        from kb_builder.vector_db.hnswlib import HnswlibVectorDB
        from shared.embedding.sentence_transformer import sentence_transformer_model
        dim = sentence_transformer_model().dim()
        path = str(Path(cfg().DB_FOLDER) / 'vector_db/categories.bin')
        return HnswlibVectorDB(path, dim) 


dbs = Dbs()