# import sys_path # Add the "ai_pipeline" directory to the sys.path
from pathlib import Path
import sqlite3

from shared.logger import Logger    
from shared.config import Config
from shared.sqlite import SQLite
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths


    
def exists_category_database() -> bool:
    db_file_path = CategoryDBFilePaths.sqlite_file_path  
    return Path(db_file_path).exists()  

def row_count_category() -> int:
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
    
    try:
        sqldb.open()
        sqldb.execute("select COUNT(*) from CHUNK")    
        return sqldb.fetchone()[0] 
    except sqlite3.Error as e:  
        Logger.error_formatted('An error occurred when counting the rows in the CHUNK table', e)
        return -1   
    
def insert_chunks(chunks, document_id: int):
    all_chunk_ids = []
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
    
    try:
        sqldb.open()
        sqldb.begin_transaction()  
         
        for chunk in chunks:
            id = sqldb.insert("insert into CHUNK (CONTENT, DOCUMENT_ID) values (?, ?)", (chunk, document_id))
            all_chunk_ids.append(id) 
            
        sqldb.commit()
    except sqlite3.Error as e: 
        sqldb.rollback()     
        Logger.error_formatted('An error occurred when inserting chunks into the CHUNK table', e)
        raise e
        
    return all_chunk_ids
    
def delete_category_chunks_for_document(document_id: id) -> None:
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
    
    try:
        sqldb.open()
        cnt = sqldb.delete("delete from CHUNK where DOCUMENT_ID = ?", (document_id,))  
        sqldb.commit()  
    except sqlite3.Error as e:
        Logger.error_formatted(f"An error occurred when deleting chunks for document {document_id}", e) 
        raise e  

    
def create_category_database():
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
    Logger.info(f'Creating database for category {CategoryDBFilePaths.sqlite_file_path}') 

    try:
        sqldb.open()
        
        # Create the CHUNK table
        sqldb.execute("""
            create virtual table "CHUNK" using fts5 (
                "CONTENT",
                "DOCUMENT_ID" unindexed,
                "TITLE" unindexed,
                "CONCISE_CONTENT" unindexed,
                "REGION" unindexed,
                "PAGE_NUMBER" unindexed
            );
        """)
        sqldb.commit() 
        
    except sqlite3.Error as e:
        Logger.error_formatted(f"An error occurred creating database for catagory {CategoryDBFilePaths.sqlite_file_path}", e)
        raise e
    finally:
        sqldb.close()  