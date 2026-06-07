from title_generator import TitleGenerator

from shared.config import Config
from shared.sqlite import SQLite

from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths
from shared.logger import Logger

def main():
    Logger.info(f"Starting Title Chunks Process:  {Config.ARGV_PARAM1} - {Config.ARGV_PARAM2  or 'default'}")   
     
    tg = TitleGenerator()

    CategoryDBFilePaths.generate_file_paths(Config.ARGV_PARAM1)
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path) 
    
    if Config.ARGV_PARAM2 == 'override':
        select_stmt = "select ROWID, CONTENT from CHUNK"  
    else:
        select_stmt = "select ROWID, CONTENT from CHUNK where (TITLE is null or TITLE = '' or TITLE = 'N/A')"
    
    print(select_stmt)  
    

    try: 
        sqldb.open()     
        sqldb.select(select_stmt)         
        rows = sqldb.fetchall()
    except Exception as e:
        Logger.error_formatted(f"An error occurred while selecting chunks", e)
        raise e
    finally:
        sqldb.close()
      
        

    
    try:
        sqldb.open()
        
        for row in rows:
            chunk_id = row[0]
            chunk = row[1]
            
            title = tg.generate_title(chunk)
            if not title:
                title = tg.generate_title(chunk, .7)
                if not title:
                    title = tg.generate_title(chunk, .9)
                    if not title:
                        title = "N/A"
                                        
            Logger.info(f"Title: {title}")
            
            print(f"Updating title {title} for chunk {chunk_id}")
            
            try:
                
                update_stmt = "UPDATE CHUNK SET TITLE = ? WHERE ROWID = ?"
                sqldb.update(update_stmt, (title, chunk_id))

                sqldb.commit()
            except Exception as e:
                Logger.error_formatted(f"An error occurred while updating title {title} for chunk {chunk_id}", e)
                raise e
    except Exception as e:
        Logger.error_formatted(f"An error occurred while updating titles", e)
        raise e
    finally: 
        sqldb.close()





        


           
    
    
   
    
    
if __name__ == "__main__":
    main()
