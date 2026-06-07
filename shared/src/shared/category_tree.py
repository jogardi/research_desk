import uuid
import os
from pathlib import Path
from shared.sqlite import SQLite
from shared.kb_folders import KNOWLEDGEBASE_FOLDER, DB_FOLDER

# import sys_path # Add the "ai_pipeline" directory to the sys.path
from shared.config import cfg

def _add_folder_to_tree(tree, path_segments, path_id, file_name):
    """
    Recursively adds a folder to the tree structure based on its hierarchical path.

    Parameters:
    tree: List representing the current tree structure - the sub-tree.
    path_segments: List of path segments indicating the location of the folder in the hierarchy.
    path_id: The unique identifier for the folder.

    returns: None
    """

    # If the folder path is empty, stop the recursion
    if not path_segments:
        return

    # Start with the root of the tree
    children = tree # Start with the current sub-tree
    
    # Index of the last path segment in the path - the leaf segment's index in the path
    last_segment_index = len(path_segments) - 1 

    # Iterate through the path segments and add them to the tree
    for index, path_segment in enumerate(path_segments):
        # Check if path segment is already in the tree at the current sub tree
        found = False
        # Check if the this path segment is already in the tree
        for node in children: 
            if node['label'] == path_segment: # If the this path segment is found in the tree
                found = True
                if index < last_segment_index and 'children' in node:  # Not at the leaf yet and has children
                    children = node['children'] # Set the current sub-tree to the found node's children
                break

        # If this path segment is not found, create a new node for it - add it to the tree
        if not found:
            new_node = {'label': path_segment} # Create a new node for the this path segment
            
            # If not a leaf node, prepare for children
            if index < last_segment_index: 
                new_node['children'] = [] # Create an empty children list
                new_node['id'] = str(uuid.uuid4()) # Assign a unique ID
                children.append(new_node) # Add the new node to the current sub-tree

                children = new_node['children'] # Set the current sub-tree to the new node's children
            else:
            # If it's a leaf node, add the leaf node and break out of the loop
                new_node['id'] = path_id # Assign the ID from the path
                children.append(new_node) # Add the new node to the current sub-tree
                if file_name:
                    new_node['file_name'] = file_name
                # last path segment added as Leaf node - now will break out of the loop

def get_folders_from_root_folder(kb_name: str):
    return get_folders(KNOWLEDGEBASE_FOLDER(kb_name))

def get_folders(root_folder: str):
    '''
    Get the list of leaf folders from the root folder.
    Each leaf folder represents a Category and contains the document files for that category.

    parameters:
    root_folder: The root folder of the knowledge base.

    returns: A list of dictionaries containing the folder's id and path.
    '''

    folders = []
    id = 0

    # Walk through the directory structure
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Check if this is a leaf directory (no sub-directories)
        if not dirnames:
            # Get the relative path of the leaf folder
            folder = os.path.relpath(dirpath, root_folder) 
            # check if folder has files
            if not filenames:
                continue
            id += 1
            folders.append({'id': str(id), 'path': folder})

    folders = sorted(folders, key=lambda x: x['path'])
    return folders

def _get_folders_from_database_files(kb_name: str):
    '''
    Get the list of leaf folders from the database files names under the sqlite_db
    This are the folders that have a sql and vector database generated for them.

    returns: A list of dictionaries containing the folder's id and path.
    ''' 
    db_path = Path(DB_FOLDER(kb_name)) / 'sqlite_db' # The path to the sqlite_db folder

    # Get the list of database files
    db_files = [f for f in os.listdir(str(db_path)) if f.endswith('.db')]

    # Get the list of distinct categories from the document database:
    sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'document.db')
    try:
        sqldb.open() 
        sqldb.select("SELECT DISTINCT CATEGORY FROM DOCUMENT")   
        rows = sqldb.fetchall()
        categories = [row[0] for row in rows] # Get the list of categories from the document database
    except Exception as e:
        raise e
    finally:
        sqldb.close()

    folders = []
    id = 0
    
    # Process each database file
    for db_file in db_files:
        db_file = db_file[:-3] # Remove the '.db' extension
        folder = db_file.replace('__', '/') # Replace the '__' with '/'
        
        id += 1

        if any(category_path.startswith(f'{folder}/') for category_path in categories): # If the folder has both files and sub-folders
            folders.append({'id': str(id), 'path': folder + '/General'})
        else: # If this is a leaf folder
            folders.append({'id': str(id), 'path': folder})
    # sort the folders by path:
    folders = sorted(folders, key=lambda x: x['path'])
    return folders

def _get_filepaths_from_document_table(kb_name: str):
    '''
    Get the list of filepaths from the document table in the document database.

    returns: A list of dictionaries containing the document's id and path.
    '''
    sqldb = SQLite(Path(DB_FOLDER(kb_name)) / 'document.db')
    try:
        sqldb.open() 
        sqldb.select("SELECT CATEGORY, FILE_NAME, TITLE FROM DOCUMENT")   
        rows = sqldb.fetchall()
        # get list with categoy/filename:
        documents = []
        id = 0
        for row in rows:
            id += 1
            if row[2] is None:
                # get the file name without the extension:
                # file_name = row[1].split('.')[0]
                file_name = row[1]

                title = file_name.replace('/', ' | ')
            else:
                title = row[2].replace('/', ' | ')
            documents.append({'id': str(id), 'path': f'{row[0]}/{title}', 'file_name': row[1]})
        # sort the documents by category:
        documents = sorted(documents, key=lambda x: x['path'].split('/')[0])
        return documents
    except Exception as e:
        raise e
    finally:
        sqldb.close()

def get_category_tree(type: str, kb_name: str):
    '''
    Get the category tree structure and the list of category IDs 

    parameters:
    type: str: The type of folders to get. 
                'all' - Get all the folders from the Knowledge Base root folder.
                'active' - Get the folders from the database files names in thr sqlite_db folder.

    returns: A tuple containing:
                the list of leaf folders, 
                the category tree structure, and 
                the list of category IDs.
    '''
    if (type == 'all'):
        folders = get_folders_from_root_folder(kb_name) # Get All folders from the root folder
    elif type == 'active': # type == 'active'
        folders = _get_folders_from_database_files(kb_name) # Get the folders from the database files names
    elif type == 'documents': # type == 'document'
        folders = _get_filepaths_from_document_table(kb_name) # Get the filepaths from the document table
    print(f'get_category_tree') 

    # The category tree structure
    tree = []

    # Process each folder and add it to the tree
    for folder in folders:
        path_segments = folder['path'].split('/')  # Split the folder path into segments
        file_name = folder['file_name'] if type == 'documents' else None
        _add_folder_to_tree(tree, path_segments, folder['id'], file_name)

    # print(json.dumps(tree, indent=2))  # Print the tree in JSON format for better visualization

    IDs = [folder['id'] for folder in folders]
    # print(ids)

    return (folders, tree, IDs)
