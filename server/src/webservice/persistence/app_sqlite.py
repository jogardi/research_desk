import sqlite3
from pathlib import Path

from shared.sqlite import SQLite
from shared.config import Config
from shared.logger import Logger
from shared.kb_folders import DB_FOLDER

class AppSqlite:
    @classmethod
    def _log_query(cls, categories: str, query: str, query_type: str, kb_name: str) -> None:
        if not Config.IS_PROD:
            return
            
        document_db_file_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        
        sqldb = SQLite(document_db_file_path) 
        try:
            sqldb.open() 
 
            sqldb.update("insert into QUERY_LOG (CATEGORIES, QUERY, QUERY_TYPE, APP_ID) values (?,?,?,?)", (categories,query,query_type,'TRD'))
           
            sqldb.commit()
        except Exception as e:
            Logger.error(f"Error logging query {categories} {query} {query_type}", exception=e)  
            
        finally:
            sqldb.close()
            
    @classmethod
    def log_ss_query(cls, categories: str, query: str, kb_name: str) -> None:
        cls._log_query(categories, query, 'SS', kb_name)
        
         
    @classmethod
    def log_fts_query(cls, categories: str, query: str, kb_name: str) -> None:
        cls._log_query(categories, query, 'FTS', kb_name)
          


   
