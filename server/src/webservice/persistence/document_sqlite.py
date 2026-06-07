import json
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import List

from shared.sqlite import SQLite
from shared.config import Config
from shared.logger import Logger
from shared.db_support.enum_flag_reason import FlagReason
from webservice.categoryDBFilePaths import CategoryDBFilePaths
from shared.kb_folders import DB_FOLDER

class DocumentSqlite:
    flagged_document_ids = set()

    @classmethod
    @lru_cache(maxsize=128)
    def _load_flag_documents(cls, kb_name: str) -> None:
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.select("select ID from DOCUMENT where FLAG_REASON is not null")
            
            rows = sqldb.fetchall()
            cls.flagged_document_ids = {str(row[0]) for row in rows}
            
            count = len(cls.flagged_document_ids)   

            Logger.info(f"Loaded flagged {count} documents from the database")  

        finally:
            sqldb.close()
           
    @classmethod 
    def is_flagged_document(cls, id: int, kb_name: str) -> bool:
        cls._load_flag_documents(kb_name)
        return str(id) in cls.flagged_document_ids

    @classmethod
    def get_document_filename(cls, id: int, kb_name: str) -> None:
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.select("select CATEGORY, FILE_NAME from DOCUMENT where ID = ? and FLAG_REASON is null", (id,))
            row = sqldb.fetchone()
            
            return row

        finally:
            sqldb.close()
            
    @classmethod
    def get_document_summary(cls, id: int, kb_name: str) -> None:
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
            if id.isdigit():
                sqldb.select("select SUMMARY from DOCUMENT where ID = ?", (id,))
            else:
                 # replace all '__' with '/':
                doc_path = id.replace('__', '/')
                # get category and file name from the id - id is in the format of "cat1/cat2/.../file_name":
                path_segments = doc_path.split('/')
                category = '/'.join(path_segments[:-1])
                file_name = path_segments[-1]
                print(f"category: {category}\n file_name: {file_name}")
                
                sqldb.select("select SUMMARY from DOCUMENT where CATEGORY = ? and FILE_NAME = ?", (category, file_name))
            
            row = sqldb.fetchone()
            
            return row[0]

        finally:
            sqldb.close()       
            
    @classmethod
    def get_category_description(cls, categpry: str, kb_name: str) -> None:
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.select("select DESCRIPTION from CATEGORY where CATEGORY = ?", (categpry,))
            row = sqldb.fetchone()
            
            return row[0]

        finally:
            sqldb.close()
            
    @classmethod
    def get_doc_page_number(cls, category: str, chunk_id: int, kb_name: str) -> None:
        categoryDBFilePaths = CategoryDBFilePaths(kb_name)
        categoryDBFilePaths.generate_file_paths(category)   
    
        sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)

        try:
            sqldb.open() # Open the database for the category

            sqldb.select(f"select REGION from CHUNK where ROWID = {chunk_id}")
            row = sqldb.fetchone() 
            
            if row is not None:
                data = json.loads(row[0])  
                page_number = data.get("page_number") 
            else:
                page_number = None
            
            return page_number
        except Exception as e:
            print(f"An error occurred when retrieving the chunk from the SQL database:\n {e}")
            raise e
        finally:
            sqldb.close() # Close the database for the category

    @classmethod
    def getDistictCategories(cls, kb_name: str) -> None:
        """
        Get the list of distinct categories from the document database:
        """
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path)

        try:
            sqldb.open() 
            
            sqldb.select("SELECT DISTINCT CATEGORY FROM DOCUMENT")   
            rows = sqldb.fetchall()
            categories = [row[0] for row in rows] # Get the list of categories from the document database
            sqldb.close()
            return categories

        finally:
            sqldb.close()
            
    @classmethod
    def flag_document(cls, user_id: str, document_id: int, flag_reason: str, comments: str, kb_name: str) -> None:
        cls._load_flag_documents(kb_name)
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'stv.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.insert("insert into FLAG (UID, DOCUMENT_ID, REASON_CODE, COMMENTS) values (?, ?, ?, ?);", (user_id, document_id, flag_reason, comments))
            sqldb.commit()
            
            cls.flagged_document_ids.add(str(document_id))
            # Clear cache since we've modified the flagged documents
            # so next time we call is_flagged_document, we will load the flagged documents from the database
            cls._load_flag_documents.cache_clear()
        
        finally:
            sqldb.close()
            
    @classmethod
    def unflag_document(cls, document_id: int, kb_name: str) -> None:
        cls._load_flag_documents(kb_name)
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'stv.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.delete("delete from FLAG where DOCUMENT_ID = ?", (document_id,))
            sqldb.commit()
            
            cls.flagged_document_ids.discard(str(document_id)) # Remove the document ID from the flagged_document_ids set if exists
            # Clear cache since we've modified the flagged documents 
            # so next time we call is_flagged_document, we will load the flagged documents from the database
            cls._load_flag_documents.cache_clear()
        finally:
            sqldb.close()

    @classmethod
    def get_categories_by_ids(cls, ids, kb_name: str) -> List[str]:
        if len(ids) == 0:
            return []
        if type(ids[0]) is not str:
            ids = [str(id) for id in ids]
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'document.db' 
        
        sqldb = SQLite(document_db_file_path) 
        with sqldb.connection():
            sqldb.select(f"select ID, CATEGORY from CATEGORY where ID in ({','.join(ids)})")
            rows = sqldb.fetchall()
        return [row[1] for row in rows]



