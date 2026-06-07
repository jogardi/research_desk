

from shared.logger import Logger
from webservice.categoryDBFilePaths import CategoryDBFilePaths
from shared.sqlite import SQLite

import json
# from webservice.llm.together.title_chat import generate_title
from webservice.persistence.document_sqlite import DocumentSqlite
from webservice.search.search_util import fill_adjacent_numbers, fix_sup_tags 
from webservice.hparams_config import hpc   

def fts_search(categoryDBFilePaths: CategoryDBFilePaths, user_query: str, kb_name: str  ):
    sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)
    Logger.info(f"Opened database: {categoryDBFilePaths.sqlite_file_path}\n")
    
    try:
        sqldb.open() # Open the database for the category

        sqldb.select(f"select ROWID as ID, CONTENT, DOCUMENT_ID, TITLE, CONCISE_CONTENT, REGION, bm25(CHUNK) as SCORE from CHUNK where CONTENT match '{user_query}'") 
        rows = sqldb.fetchall()
        
        ids1 = list(rows[row][0] for row in range(len(rows)))

        ids_adjacent = []

        if len(ids1) > 0:
            comma_separated_string = ", ".join(map(str, ids1))

            in_clause = fill_adjacent_numbers(comma_separated_string, hpc().SENTENCE_BEFORE_OFFSET, hpc().SENTENCE_AFTER_OFFSET)  
        
            sqldb.select(f"select ROWID as ID, CONTENT, DOCUMENT_ID, TITLE, CONCISE_CONTENT, REGION, bm25(CHUNK) as SCORE from CHUNK where ROWID in ({in_clause})") 
            rows = sqldb.fetchall()

            ids2 = list(rows[row][0] for row in range(len(rows)))
            # get all ids that are in ids2 but not in ids2:
            ids_adjacent = [id for id in ids2 if id not in ids1]

    
        
        chunks = []

        for row in rows:
            if DocumentSqlite.is_flagged_document(row[2], kb_name): 
                print(f"Document {row[2]} is flagged, skipping ...")
                Logger.debug(f"Document {row[2]} is flagged, skipping ...")
                continue
    
            # content = ' '.join(row[1].split())  # Remove extra spaces from the content
            content = row[1]
            
            # Fix escaped sup tags
            content = fix_sup_tags(content)

            # Generate title 
            title = row[3]  
            # if title is None:
            #     title = generate_title(content)
            #     sqldb.update("update CHUNK set TITLE = (?) where ROWID = (?)", (title, row[0]))
 
            # sqldb.commit()
            
            region = json.loads(row[5])
            
            # If there's an image URL, clear the text content (which is the description)
            if region.get('image_url'):
                content = ""
                
            chunk = { 
                "id": row[0], 
                "title": title, 
                "text": content.replace('\n', '<br/>'), 
                "concise_text": row[4], 
                "documentID": row[2], 
                "region": region,
                "search": "Text", 
                "score": 2 if row[0] in ids_adjacent else 1, 
                "status": "O", 
                "checked": False } # Create a dictionary for the chunk
            chunks.append(chunk)
    except Exception as e:
        print(f"An error occurred when retrieving the chunks from the SQL database:\n {e}")
        raise e
    finally:
        sqldb.close() 

    return chunks
