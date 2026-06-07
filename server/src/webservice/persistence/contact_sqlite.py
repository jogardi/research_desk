import sqlite3

from shared.config import Config
from shared.logger import Logger
from shared.sqlite import SQLite
from shared.kb_folders import DB_FOLDER


class ContactSqlite:

    @staticmethod
    def contact(user_id, payload, kb_name: str) -> bool:
        sqldb = SQLite(DB_FOLDER(kb_name) + '/stv.db') 

        isError = False
        try:
            sqldb.open() 
            sqldb.begin_transaction() 

            sqldb.insert("insert into CONTACT (UID, EMAIL, QUERY_FUNC_AREA, QUERY_TYPE, BODY) values (?,?,?,?,?)", 
                (user_id, payload['email'], payload['func_area'], payload['query_type'], payload['message']))
            sqldb.commit() 
        
        except Exception as e:
            Logger.error(f"Error inserting contact: {payload['email']} {payload['message']}", exception=e)
            isError = True
        finally:
            sqldb.close()  
            
                
        return isError
   
    



