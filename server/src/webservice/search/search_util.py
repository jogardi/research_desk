
from shared.logger import Logger
from webservice.categoryDBFilePaths import CategoryDBFilePaths
from shared.sqlite import SQLite
import re
import nltk
from nltk.tokenize import word_tokenize

from webservice.persistence.document_sqlite import DocumentSqlite

def fill_adjacent_numbers(comma_separated_string, before_offset=1, after_offset=1):
    """
    Expand each number n in the given comma-separated string by including
    the entire range from (n - beforeOffset) to (n + afterOffset).

    Example:
        Input:  "101,109,120,128"
        Offsets: beforeOffset=2, afterOffset=2
        Output: "99,100,101,102,103,107,108,109,110,111,118,119,120,121,122,126,127,128,129,130"
    """
    
    # Convert the comma-separated string to a list of integers
    numbers = list(map(int, comma_separated_string.split(",")))
    
    result = []
    # For each number, generate the expanded range
    for n in numbers:
        for x in range(n - before_offset, n + after_offset + 1):
            result.append(x)
            
    # Convert the result list back to a comma-separated string
    print('after: ' + ",".join(map(str, result)))
    return ",".join(map(str, result))       

def get_chunk_content(document_id: int, chunk_id: int, kb_name: str):
    row = DocumentSqlite.get_document_filename(document_id, kb_name)
    if (row is None):
        return None
    
    category, filename = row
    
    categoryDBFilePaths = CategoryDBFilePaths(kb_name)
    categoryDBFilePaths.generate_file_paths(category)   
    
    sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)

    try:
        sqldb.open() # Open the database for the category

        sqldb.select(f"select CONTENT from CHUNK where ROWID = {chunk_id}")
        row = sqldb.fetchone() 
        
        if row is not None:
            content = row[0]
        else:
            content = None
        
        return content
    except Exception as e:
        print(f"An error occurred when retrieving the chunk from the SQL database:\n {e}")
        raise e
    finally:
        sqldb.close() # Close the database for the category
        
        
def get_excerpt_content(document_id: int, first_chunk_id: int, last_chunk_id: int, kb_name: str):
    row = DocumentSqlite.get_document_filename(document_id, kb_name)
    if (row is None):
        return None
    
    category, filename = row
    
    categoryDBFilePaths = CategoryDBFilePaths(kb_name)
    categoryDBFilePaths.generate_file_paths(category)   
    
    sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)

    try:
        sqldb.open() 

        sqldb.select(f"select ROWID as id, CONTENT as text from CHUNK where ROWID between {first_chunk_id} and {last_chunk_id}")
        rows = sqldb.fetchall() 
        
        # Get column names from the cursor description
        column_names = [description[0] for description in sqldb.cursor.description]

        # Combine column names with each row to return a list of dictionaries
        result = [dict(zip(column_names, row)) for row in rows]

        return result
    except Exception as e:
        print(f"An error occurred when retrieving the excerpts {first_chunk_id} and {last_chunk_id} for category {category} from the SQL database:\n {e}")
        raise e
    finally:
        sqldb.close() 


def numeric_tokens_percentage(text):
    # Tokenize the text
    tokens = word_tokenize(text)
    
    # check if at least one token length greater than 25 characters:
    # if any(len(token) > 30 for token in tokens):
    #     return 100
    
    # Define a regular expression pattern for numeric tokens
    numeric_pattern = r'^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?[%]?$'
    
    # Count numeric tokens
    numeric_count = sum(1 for token in tokens if re.match(numeric_pattern, token.replace(',', '')))
    
    # Calculate the percentage
    total_tokens = len(tokens)
    percentage = (numeric_count / total_tokens) * 100 if total_tokens > 0 else 0
    
    return percentage


def fix_sup_tags(text):
    """
    Convert escaped sup tags back to proper HTML.
    Converts &lt;sup&gt;...&lt;/sup&gt; to <sup>...</sup>
    """
    if not text:
        return text
    
    # Replace escaped sup tags with proper HTML
    text = text.replace('&lt;sup&gt;', '<sup>')
    text = text.replace('&lt;/sup&gt;', '</sup>')
    text = text.replace('&lt;/sup>', '</sup>')
    text = text.replace('&amp;lt;sup&gt;', '<sup>')
    text = text.replace('&amp;lt;sup>;', '<sup>')
    
    return text


def clean_query(user_query):
    characters_to_remove = "'!@#$%^&-_=+\\|[]{};:/?.,"
    translation_table = str.maketrans("", "", characters_to_remove)

    # Step 1 & 2: Replace quoted substrings with safe placeholders and store them
    quoted_parts = []
    def replace_quotes(match):
        quoted_parts.append(match.group(0))
        return f"PLACEHOLDER{len(quoted_parts) - 1}XYZ"

    user_query = re.sub(r'"[^"]*"', replace_quotes, user_query)

    # Step 3: Remove special characters from the rest
    user_query = user_query.translate(translation_table)

    # Step 4: Restore quoted substrings
    for i, part in enumerate(quoted_parts):
        user_query = user_query.replace(f"PLACEHOLDER{i}XYZ", part)

    return user_query

