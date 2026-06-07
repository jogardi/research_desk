import sqlite3
from pathlib import Path
from shared.kb_folders import DB_FOLDER

from shared.config import Config
from shared.logger import Logger

def create_session_table(kb_name: str):
        """Creates the database and tables if they do not exist."""
        db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
        if not db_path.exists():
            Logger.info(f"Database {db_path} not found. Creating...")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()

                # Create PROJECT table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS PROJECT (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    NAME VARCHAR(50) NOT NULL,
                    DESCRIPTION VARCHAR(250)
                )
                """)

                # Create SESSION table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS SESSION (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    NAME VARCHAR(50) NOT NULL,
                    DESCRIPTION VARCHAR(250),
                    DETAIL TEXT,
                    KB_NAME VARCHAR(25) NOT NULL,
                    CREATED_BY VARCHAR(36) NOT NULL,
                    CREATED_ON TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UPDATED_BY VARCHAR(36),
                    UPDATED_ON TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)

                conn.commit()

def create_excerpts_table(kb_name: str) -> None:
    """Create the excerpts table in the main document database"""
    db_path = Path(DB_FOLDER(kb_name)) / 'document.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS EXCERPT (
                HASH TEXT PRIMARY KEY,
                DOCUMENT_ID INTEGER NOT NULL,
                CHUNK_IDS TEXT NOT NULL
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_excerpt_document 
            ON EXCERPT(DOCUMENT_ID)
        """)
        
        conn.commit()
        print("Excerpts table created successfully")


# def create_llm_role_default_table():
CREATE_LLM_ROLES_TABLE_SQL = """
    CREATE TABLE LLM_ROLE_DEFAULT (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        ROLE TEXT NOT NULL
                    );
    INSERT INTO LLM_ROLE_DEFAULT VALUES(1,'You are a research assistant. Use the selected knowledge base excerpts to answer accurately and cite sources when available.');
    INSERT INTO LLM_ROLE_DEFAULT VALUES(2,'You are a concise summarizer. Extract the main points from the selected documents and avoid adding unsupported claims.');
    INSERT INTO LLM_ROLE_DEFAULT VALUES(3,'You are a comparison assistant. Compare selected sources, call out agreements and conflicts, and keep conclusions grounded in the provided material.');
    INSERT INTO LLM_ROLE_DEFAULT VALUES(4,'You are a question generator. Suggest useful follow-up questions based on the selected excerpts.');
    INSERT INTO LLM_ROLE_DEFAULT VALUES(5,'You are a drafting assistant. Help turn selected notes and excerpts into clear prose while preserving citations.');
    """

def create_llm_role_tables(kb_name: str):
    """Creates the database and tables if they do not exist."""
    db_path = Path(DB_FOLDER(kb_name)) / 'rd.db' 
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if LLM_ROLE_DEFAULT table exists
        cursor.execute("""
        SELECT count(*) FROM sqlite_master 
        WHERE type='table' AND name='LLM_ROLE_DEFAULT'
        """)
        default_table_exists = cursor.fetchone()[0] > 0
        
        if not default_table_exists:
            Logger.info(f"Table LLM_ROLE_DEFAULT not found in database. Creating...")
            
            # Create LLM_ROLE_DEFAULT table and insert default roles
            cursor.executescript(CREATE_LLM_ROLES_TABLE_SQL)
            conn.commit()
        
        # Check if LLM_ROLE table exists
        cursor.execute("""
        SELECT count(*) FROM sqlite_master 
        WHERE type='table' AND name='LLM_ROLE'
        """)
        table_exists = cursor.fetchone()[0] > 0
        
        if not table_exists:
            Logger.info(f"Table LLM_ROLE not found in database. Creating...")
            
            # Create LLM_ROLE table with the correct schema
            cursor.execute("""
            CREATE TABLE LLM_ROLE (
                ID INTEGER PRIMARY KEY AUTOINCREMENT,
                ROLE TEXT NOT NULL,
                OWNER_ID VARCHAR(36) NOT NULL
            )
            """)
            
            conn.commit()
