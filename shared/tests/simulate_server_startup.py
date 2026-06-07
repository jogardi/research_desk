#!/usr/bin/env python3
"""
Script to simulate the server startup process and reproduce the meta tensor issue.
Run this from the webservice directory with the same command as the server:
HF_HUB_DISABLE_TQDM=1 poetry run python3 simulate_server_startup.py --profile default --kb demo
"""

import os
import sys
import argparse
from shared.kb_folders import DB_FOLDER

def main(kb_name: str):
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='default', help='Profile name')
    parser.add_argument('--kb', default=kb_name, help='Knowledge base name')
    args = parser.parse_args()
    kb_name = args.kb
    
    # Set up environment exactly as the server does
    os.environ['PROFILE'] = args.profile
    os.environ['HF_HUB_DISABLE_TQDM'] = '1'
    
    print(f"Starting simulation with profile: {args.profile}")
    print(f"Environment: HF_HUB_DISABLE_TQDM={os.environ.get('HF_HUB_DISABLE_TQDM')}")
    
    # Import modules in the same order as the server
    print("\n1. Importing semantic_search module...")
    from webservice.search.semantic_search import semantic_search, load_vector_db
    
    print("\n2. Creating CategoryDBFilePaths...")
    from webservice.category_DB_filePaths import CategoryDBFilePaths
    
    # Simulate what happens when a search request comes in
    print("\n3. Simulating search request...")
    
    # Get a real category from the database
    from shared.sqlite import SQLite
    
    db = SQLite(DB_FOLDER(kb_name) + '/document.db')
    db.open()
    db.select("SELECT DISTINCT CATEGORY FROM DOCUMENT LIMIT 1")
    row = db.fetchone()
    db.close()
    
    if row and row[0]:
        category = row[0]
        print(f"   Using category: {category}")
        
        categoryDBFilePaths = CategoryDBFilePaths()
        categoryDBFilePaths.generate_file_paths(category)
        
        print(f"\n4. Loading vector database...")
        print(f"   Path: {categoryDBFilePaths.hnswlib_file_path}")
        
        try:
            # This is where the error occurs in the server
            embedding_model, vector_db = load_vector_db(categoryDBFilePaths.hnswlib_file_path)
            print("   ✓ Vector database loaded successfully")
            
            # Try to use the model
            print("\n5. Testing embedding model...")
            dimension = embedding_model.dim()
            print(f"   ✓ Model dimension: {dimension}")
            
            print("\n6. Testing query embedding...")
            query_embedding = embedding_model.embed("test query")
            print(f"   ✓ Query embedding shape: {query_embedding.shape}")
            
        except Exception as e:
            print(f"\n   ✗ Error occurred: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            
            if "Cannot copy out of meta tensor" in str(e):
                print("\n🎯 Successfully reproduced the meta tensor issue!")
                sys.exit(1)
            else:
                print("\n❌ Different error occurred")
                sys.exit(2)
    else:
        print("   No categories found in database")
        sys.exit(3)
    
    print("\n✅ No errors - issue not reproduced")

if __name__ == "__main__":
    main("demo")
