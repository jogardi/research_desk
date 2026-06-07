#!/usr/bin/env python3
"""
Script to build Lucene index for a given category or all categories.
This script reads chunks from the SQLite database and creates a Lucene index for BM25 search.
"""

import os
import sys
import argparse
from pathlib import Path
from tqdm import tqdm

# Add the kb-builder src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


def main():
    parser = argparse.ArgumentParser(description='Build Lucene index for a category or all categories')
    parser.add_argument('--category', help='Category name (e.g., "Example Category/Reports")')
    parser.add_argument('--all-categories', action='store_true', 
                       help='Build Lucene index for all categories')
    parser.add_argument('--force-rebuild', action='store_true', 
                       help='Force rebuild the index even if it already exists')
    parser.add_argument('--profile', help='Profile to use (defaults to current profile)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.category and not args.all_categories:
        parser.error("Either --category or --all-categories must be specified")
    
    if args.category and args.all_categories:
        parser.error("Cannot specify both --category and --all-categories")
    
    # Set profile if specified - must be done before any config-dependent imports
    if args.profile:
        os.environ['PROFILE'] = args.profile
    
    # Now import modules that depend on config
    from shared.config import cfg
    from shared.sqlite import SQLite
    from shared.logger import Logger
    from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths
    from kb_builder.non_learned_search import NonLearnedSearch
    
    def get_all_categories():
        """
        Get all categories that have database files.
        
        Returns:
            List of category names
        """
        db_path = Path(cfg().DB_FOLDER) / 'sqlite_db'
        
        if not db_path.exists():
            Logger.error(f"SQLite database directory not found: {db_path}")
            return []
        
        # Get the list of database files
        db_files = [f for f in os.listdir(str(db_path)) if f.endswith('.db')]
        
        categories = []
        for db_file in db_files:
            # Remove the '.db' extension and replace '__' with '/'
            category = db_file[:-3].replace('__', '/')
            categories.append(category)
        
        return sorted(categories)
    
    def build_lucene_index(category: str, force_rebuild: bool = False):
        """
        Build Lucene index for the specified category.
        
        Args:
            category: The category name (e.g., "Example Category/Reports")
            force_rebuild: If True, delete existing index and rebuild from scratch
            
        Returns:
            bool: True if successful, False otherwise
        """
        Logger.info(f"Building Lucene index for category: {category}")
        
        # Generate file paths for the category
        CategoryDBFilePaths.generate_file_paths(category)
        
        # Check if SQLite database exists
        if not os.path.exists(CategoryDBFilePaths.sqlite_file_path):
            Logger.error(f"SQLite database not found: {CategoryDBFilePaths.sqlite_file_path}")
            return False
        
        # Check if Lucene directory exists and handle force rebuild
        lucene_dir = Path(CategoryDBFilePaths.lucene_dir_path)
        if lucene_dir.exists():
            if force_rebuild:
                Logger.info(f"Removing existing Lucene index at: {lucene_dir}")
                import shutil
                shutil.rmtree(lucene_dir)
        
        # Create Lucene directory
        lucene_dir.mkdir(parents=True, exist_ok=True)
        
        # Read chunks from SQLite database
        sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
        chunks_data = []
        
        try:
            sqldb.open()
            
            # Query to get all chunks with their IDs and content
            query = """
            SELECT rowid, CONTENT 
            FROM CHUNK 
            ORDER BY rowid
            """
            
            cursor = sqldb.cursor.execute(query)
            rows = cursor.fetchall()
            
            Logger.info(f"Found {len(rows)} chunks to index")
            
            # Prepare data for Lucene indexing
            for row in rows:
                chunk_id, content = row
                chunks_data.append({
                    'id': str(chunk_id),
                    'contents': content
                })
            
            if not chunks_data:
                Logger.warning("No chunks found in the database")
                return False
            
            # Build Lucene index
            Logger.info(f"Building Lucene index with {len(chunks_data)} chunks")
            lucene_indexer = NonLearnedSearch()
            lucene_indexer.add_batch_dict(CategoryDBFilePaths.lucene_dir_path, chunks_data)
            
            Logger.info(f"Successfully built Lucene index at: {CategoryDBFilePaths.lucene_dir_path}")
            return True
            
        except Exception as e:
            Logger.error_formatted(f"Error building Lucene index for category {category}", e)
            return False
        finally:
            sqldb.close()
    
    # Build the index(es)
    if args.all_categories:
        categories = get_all_categories()
        if not categories:
            Logger.error("No categories found to process")
            sys.exit(1)
        
        Logger.info(f"Found {len(categories)} categories to process")
        
        successful_builds = 0
        failed_builds = 0
        
        for category in tqdm(categories):
            Logger.info(f"Processing category {successful_builds + failed_builds + 1}/{len(categories)}: {category}")
            success = build_lucene_index(category, args.force_rebuild)
            if success:
                successful_builds += 1
            else:
                failed_builds += 1
        
        Logger.info(f"Lucene index build completed. Successful: {successful_builds}, Failed: {failed_builds}")
        
        if failed_builds == 0:
            Logger.info("All Lucene indexes built successfully")
            sys.exit(0)
        else:
            Logger.error(f"Some Lucene indexes failed to build ({failed_builds} failures)")
            sys.exit(1)
    else:
        # Single category build
        success = build_lucene_index(args.category, args.force_rebuild)
        
        if success:
            Logger.info("Lucene index build completed successfully")
            sys.exit(0)
        else:
            Logger.error("Lucene index build failed")
            sys.exit(1)


if __name__ == "__main__":
    main() 
