import sqlite3

from pathlib import Path
from datetime import datetime

from shared.logger import Logger
from shared.sqlite import SQLite
from shared.config import Config
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths, dbs
processed_on = datetime.now().strftime("%Y-%m-%d")

def count_documents() -> int:
    sqldb = dbs.document_db 

    try:
        sqldb.open() 

        sqldb.execute("select count(*) from DOCUMENT")
        
        return sqldb.fetchone()[0] 

    except Exception as e:
        Logger.error_formatted(f"An error occurred when counting documents", e) 
        raise e 
    finally:
        sqldb.close()

def insert_category(category: str, description: str):
    
    sqldb = dbs.document_db 
    
    try:
        sqldb.open() 
        sqldb.begin_transaction() 

        sqldb.delete("delete from CATEGORY where CATEGORY = ?", (category,))
        category_id = sqldb.insert("insert into CATEGORY (CATEGORY, DESCRIPTION) values (?, ?)", (category, description))
            
        sqldb.commit() 
    except Exception as e:
        Logger.error_formatted(f"An error occurred when inserting category {category}", e) 
        raise e 
    finally:
        sqldb.close()
    
    return category_id


def insert_document(file_name: str, category: str, source: str, summary: str, publication_date: str = None) -> int:
    sqldb = dbs.document_db 

    try:
        sqldb.open()
        sqldb.begin_transaction() 

        document_id = sqldb.insert("insert into DOCUMENT (FILE_NAME, CATEGORY, SOURCE, PROCESSED_ON, SUMMARY, PUBLICATION_DATE) values (?,?,?,?,?,?)", (file_name, category, source, processed_on, summary, publication_date))
        sqldb.commit() 
        
        return document_id

    
    except Exception as e:
        Logger.error_formatted(f"An error occurred when inserting document {file_name}", e) 
        raise e 
    finally:
        sqldb.close()
        
def find_document(file_name: str, category: str):
    sqldb = dbs.document_db

    try:
        sqldb.open() 
        
        #must have unique index on table
        sqldb.select("select ID, FILE_NAME from DOCUMENT where CATEGORY = ? and FILE_NAME = ?", (category, file_name))
        row = sqldb.fetchone()
        
        if row is not None:
            return row[0], row[1]  
        else:
            return None, None 
        
    except Exception as e:
        Logger.error_formatted(f"An error occurred when checking if document {file_name} exists", e)  
        raise e 
    finally:
        sqldb.close()
        
def get_categories() -> list:
    sqldb = dbs.document_db 

    try:
        sqldb.open() 
        
        sqldb.select("select DISTINCT CATEGORY from DOCUMENT where CATEGORY not in (SELECT CATEGORY FROM CATEGORY)")
        rows = sqldb.fetchall()
        
        return rows       
        
    except Exception as e:
        Logger.error_formatted(f"An error occurred when getting", e)  
        raise e 
    finally:
        sqldb.close()
        
def get_category_summaries(category: str) -> list:
    document_db_file_path = CategoryDBFilePaths.document_sqlite_file_path

    sqldb = SQLite(document_db_file_path) 

    try:
        sqldb.open() 
        
        sqldb.select("select FILE_NAME, SUMMARY from DOCUMENT where CATEGORY = ?", (category,))
        rows = sqldb.fetchall()
        
        return rows       
        
    except Exception as e:
        Logger.error_formatted(f"An error occurred when getting category summaries for {category}", e)  
        raise e 
    finally:
        sqldb.close()
        

def delete_document(file_name: str, category: str) -> int:
    document_db_file_path = CategoryDBFilePaths.document_sqlite_file_path
    sqldb = SQLite(document_db_file_path) 

    try:
        sqldb.open() 
        rows_deleted = sqldb.delete("delete from DOCUMENT where CATEGORY = ? and FILE_NAME = ?", (category, file_name))
        sqldb.commit()
        
    except Exception as e:
        Logger.error_formatted(f"An error occurred when deleting document {file_name}", e)  
        raise e 
    finally:
        sqldb.close()
        
        
def delete_category_documents(category: str) -> int:
    document_db_file_path = CategoryDBFilePaths.document_sqlite_file_path
    sqldb = SQLite(document_db_file_path) 

    try:
        sqldb.open() 
        sqldb.delete("delete from DOCUMENT where CATEGORY = ?", (category,))
        sqldb.commit()
        
    except Exception as e:
        Logger.error_formatted(f"An error occurred when deleting documents {category}", e)  
        raise e 
    finally:
        sqldb.close()
 
