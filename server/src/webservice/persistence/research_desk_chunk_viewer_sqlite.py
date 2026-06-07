import os
import requests
import sqlite3

from pathlib import Path

from datetime import datetime
from shared.sqlite import SQLite
from shared.config import Config
from shared.logger import Logger

from webservice.categoryDBFilePaths import CategoryDBFilePaths


class ResearchDeskChunkViewerSqlite:
    @staticmethod
    def _get_sessions(categoryDBFilePaths: CategoryDBFilePaths, offset: int, chunk_id: int): 
        if (offset < 0):
            begin_row = chunk_id + offset
            end_row = chunk_id
        else:
            begin_row = chunk_id
            end_row = chunk_id + offset
            
       
        print(categoryDBFilePaths.sqlite_file_path) 
        sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)
        
        try:
            sqldb.open() 
 
            sqldb.select("select ROWID, CONTENT from CHUNK where ROWID between ? and ?", (begin_row, end_row))
            rows = sqldb.fetchall()
            
 
            print( rows)
        finally:
            sqldb.close()
      
if __name__ == '__main__':
    categories = 'Example/Category'
    kb_name = "demo"
    categoryDBFilePaths = CategoryDBFilePaths(kb_name)   
    categoryDBFilePaths.generate_file_paths(categories[0])
    
    ResearchDeskChunkViewerSqlite._get_sessions(categoryDBFilePaths, -5, 25)   
