import os
import requests
import sqlite3

from pathlib import Path

from datetime import datetime
from shared.sqlite import SQLite
from shared.config import Config
from shared.logger import Logger
from shared.kb_folders import DB_FOLDER

from webservice.persistence.compressor import Compressor 

class ResearchDeskSessionSqlite: 
    @staticmethod
    def resolve_kb_name(user_id: str, kb_list: list[dict], default_kb: str):
        kb_name = default_kb # default to the default kb
        recent_sessions = [] # list of recent sessions

        # get the recent sessions for each kb and add to the recent_sessions list
        for kb in kb_list:
            current_kb_name = kb['kb_name']
            sessions = ResearchDeskSessionSqlite.get_sessions(user_id, current_kb_name)
            if sessions is not None and len(sessions) > 0:
                # add to sessions[0] the current kb_name
                sessions[0]['kb_name'] = current_kb_name
                recent_sessions.append(sessions[0]) # get the most recent session
         
        # if there are recent sessions, get the kb_name from the most recent session
        if len(recent_sessions) > 0:
            # sort the recent_sessions by updated_on descending
            recent_sessions.sort(key=lambda x: x['updated_on'], reverse=True)
            # get the kb_name from the most recent session
            kb_name = recent_sessions[0]['kb_name']
        
        return kb_name
    
    @staticmethod
    def get_sessions(user_id: str, kb_name: str): 
        sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'rd.db') 
        
        try:
            sqldb.open() 
 
            sqldb.select("select ID, NAME, DESCRIPTION, UPDATED_ON from SESSION where CREATED_BY = ? order by UPDATED_ON desc", (user_id,))
            rows = sqldb.fetchall()
            
            sessions = [
                {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "updated_on": row[3]
                }
                for row in rows
            ]
 
            return sessions
        finally:
            sqldb.close()
      
    @staticmethod
    def get_session(session_id: str, user_id: str, kb_name: str):
        sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'rd.db') 
        
        try:
            sqldb.open() 
            sqldb.select("select DETAIL from SESSION where ID = ? and CREATED_BY = ?", (session_id, user_id))
            row = sqldb.fetchone()
            
            return Compressor.decompress(row[0])      
            
        finally:
            sqldb.close()
            
    @staticmethod
    def create_session(name: str, description: str, detail: str, 
                        user_id: str, kb_name: str) -> int:
        detail_compressed = Compressor.compress(detail)
        
        sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'rd.db') 
        
        try:
            sqldb.open() 
            project_id = 1 # TODO: Remove project_id from session table
            session_id = sqldb.insert("insert into SESSION (NAME, DESCRIPTION, DETAIL, CREATED_BY, PROJECT_ID) values (?,?,?,?,?)", (name, description, detail_compressed, user_id, project_id))
            sqldb.commit()
            
            return session_id
        finally:
            sqldb.close()
  
    @staticmethod
    def update_session(session_id: str, name: str, description: str, 
                       detail: str, user_id: str, kb_name: str):
        detail_compressed = Compressor.compress(detail)
        
        print(Path(DB_FOLDER(kb_name)) / 'rd.db')
        sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'rd.db') 
        
        try:
            sqldb.open() 
            print(f"*** user_id: {session_id} {user_id}, name: {name}, description: {description}")
            print(datetime.now())
            sqldb.update("update SESSION set NAME = ?, DESCRIPTION = ?, DETAIL = ?, UPDATED_ON = ? where ID = ? and CREATED_BY = ?", (name, description, detail_compressed, datetime.now(), session_id, user_id))
            sqldb.commit()
        finally:
            sqldb.close()
 
    @staticmethod
    def delete_session(session_id: str, user_id: str, kb_name: str):
        sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'rd.db') 
        
        try:
            sqldb.open() 
            sqldb.delete("delete from SESSION where ID = ? and CREATED_BY = ?", (session_id, user_id))
            sqldb.commit()
        finally:
            sqldb.close()
        