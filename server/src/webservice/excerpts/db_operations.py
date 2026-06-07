import sqlite3
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from shared.config import cfg
from functools import lru_cache
import os
from shared.kb_folders import DB_FOLDER

def generate_excerpt_hash(document_id: int, chunk_ids: List[int]) -> str:
    """Generate a 4-character hash for an excerpt based on document ID and chunk IDs
    
    Parameters
    ----------
    document_id : int
        The document ID
    chunk_ids : List[int]
        List of chunk IDs in the excerpt
        
    Returns
    -------
    str
        A 4-character hash string
    """
    # Create a consistent string representation
    chunk_ids_sorted = sorted(chunk_ids)
    hash_input = f"{document_id}:{','.join(map(str, chunk_ids_sorted))}"
    
    # Generate SHA256 hash and take first 4 characters of hex digest
    hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()
    return hash_digest[:4]


def store_excerpt(document_id: int, chunk_ids: List[int], kb_name: str, excerpt_hash: Optional[str] = None) -> str:
    """Store an excerpt in the database
    
    Parameters
    ----------
    document_id : int
        The document ID
    chunk_ids : List[int]
        List of chunk IDs in the excerpt
    excerpt_hash : Optional[str]
        Pre-computed hash (if None, will be generated)
        
    Returns
    -------
    str
        The hash of the stored excerpt
    """
    if excerpt_hash is None:
        excerpt_hash = generate_excerpt_hash(document_id, chunk_ids)
    
    db_path = f'{DB_FOLDER(kb_name)}/document.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Store chunk IDs as JSON array
        chunk_ids_json = json.dumps(chunk_ids)
        
        # Use INSERT OR IGNORE to avoid duplicates
        cursor.execute("""
            INSERT OR IGNORE INTO EXCERPT 
            (HASH, DOCUMENT_ID, CHUNK_IDS)
            VALUES (?, ?, ?)
        """, (excerpt_hash, document_id, chunk_ids_json))
        
        conn.commit()
    
    return excerpt_hash


def get_excerpt_by_hash(excerpt_hash: str, kb_name: str) -> Optional[Dict]:
    """Retrieve excerpt information by hash
    
    Parameters
    ----------
    excerpt_hash : str
        The 4-character hash of the excerpt
        
    Returns
    -------
    Optional[Dict]
        Dictionary with excerpt information or None if not found
    """
    db_path = f'{DB_FOLDER(kb_name)}/document.db'
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DOCUMENT_ID, CHUNK_IDS
            FROM EXCERPT
            WHERE HASH = ?
        """, (excerpt_hash,))
        
        row = cursor.fetchone()
        
        if row:
            return {
                'document_id': row[0],
                'chunk_ids': json.loads(row[1])
            }
    
    return None


def get_excerpt_chunks_with_category(excerpt_hash: str, kb_name: str) -> Tuple[Optional[List[Dict]], Optional[str], Optional[int]]:
    """Get chunk details including PDF regions for an excerpt
    
    Parameters
    ----------
    excerpt_hash : str
        The 4-character hash of the excerpt
        
    Returns
    -------
    Tuple[Optional[List[Dict]], Optional[str], Optional[int]]
        (chunks_with_regions, error_message, status_code)
    """
    excerpt_info = get_excerpt_by_hash(excerpt_hash, kb_name)
    
    if not excerpt_info:
        return None, "Excerpt not found", 404
    
    document_id = excerpt_info['document_id']
    chunk_ids = excerpt_info['chunk_ids']
    
    # First get the category from the document table
    db_path = f'{DB_FOLDER(kb_name)}/document.db'
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT CATEGORY, DOC_TYPE
                FROM DOCUMENT
                WHERE ID = ?
            """, (document_id,))
            
            doc_row = cursor.fetchone()
            if not doc_row:
                return None, "Document not found", 404
                
            category = doc_row[0].replace('/', '__')
            doc_type = doc_row[1]
        
        # Now get the chunks from the category database
        category_db_path = f'{DB_FOLDER(kb_name)}/sqlite_db/{category}.db'
        assert os.path.exists(category_db_path)
        
        with sqlite3.connect(category_db_path) as conn:
            cursor = conn.cursor()
            
            # Build query for multiple chunk IDs
            placeholders = ','.join('?' * len(chunk_ids))
            query = f"""
                SELECT rowid, CONTENT, REGION 
                FROM CHUNK 
                WHERE rowid IN ({placeholders})
                ORDER BY rowid
            """
            
            cursor.execute(query, chunk_ids)
            rows = cursor.fetchall()
            
            chunks = []
            for row in rows:
                chunk = {
                    'id': row[0],
                    'text': row[1],
                }
                
                # Parse region JSON if available
                if row[2]:
                    try:
                        chunk['region'] = json.loads(row[2])
                    except json.JSONDecodeError:
                        chunk['region'] = None
                else:
                    chunk['region'] = None
                    
                chunks.append(chunk)
            
            # Return chunks along with minimal metadata
            result = {
                'chunks': chunks,
                'document_id': document_id,
                'category': category,
                'docType': doc_type
            }
            
            return result, None, 200
            
    except Exception as e:
        return None, f"Error retrieving chunks: {str(e)}", 500 