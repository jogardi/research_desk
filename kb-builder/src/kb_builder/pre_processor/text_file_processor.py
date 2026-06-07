from shared.logger import Logger
 
def process_text(text_file_path: str):   
    #shutil.copy(text_file_path,target_processed_file_path)
    
    with open(text_file_path, 'r') as file:
        file_contents = file.read()
   
    return file_contents


