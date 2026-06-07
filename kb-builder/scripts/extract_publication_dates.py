#!/usr/bin/env python3
"""
Script to extract publication dates from documents by analyzing the first page chunks
using Claude Sonnet via litellm with structured output (JSON mode).
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the profile BEFORE importing anything that uses Config
# os.environ['PROFILE'] = 'default'

# Add the parent directory to the path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'lib' / 'shared' / 'src'))

import litellm
from pydantic import BaseModel
from shared.logger import Logger
from shared.sqlite import SQLite
from shared.config import Config  # This will load API keys from config
from kb_builder.db_support.category_db_file_paths import CategoryDBFilePaths, dbs


class PublicationDateResult(BaseModel):
    """Structured output model for publication date extraction"""
    has_publication_date: bool
    publication_date: Optional[str] = None  # Format: YYYY-MM-DD
    confidence: str  # "high", "medium", "low"
    reasoning: str


def get_all_documents() -> List[Dict]:
    """Get all documents from the document database"""
    sqldb = dbs.document_db
    documents = []
    
    try:
        sqldb.open()
        sqldb.select("SELECT ID, FILE_NAME, CATEGORY, PUBLICATION_DATE FROM DOCUMENT")
        rows = sqldb.fetchall()
        
        for row in rows:
            documents.append({
                'id': row[0],
                'file_name': row[1],
                'category': row[2],
                'publication_date': row[3]
            })
        
        return documents
    
    except Exception as e:
        Logger.error_formatted("Error getting documents", e)
        raise e
    finally:
        sqldb.close()


def get_first_page_chunks(document_id: int, category: str) -> str:
    """Get all chunks from the first 3 pages of a document"""
    # Generate the category database file path
    CategoryDBFilePaths.generate_file_paths(category)
    sqldb = SQLite(CategoryDBFilePaths.sqlite_file_path)
    
    chunks_text = []
    
    try:
        sqldb.open()
        # Get chunks from the first 3 pages
        sqldb.select("""
            SELECT CONTENT, REGION 
            FROM CHUNK 
            WHERE DOCUMENT_ID = ? 
            ORDER BY ROWID
        """, (document_id,))
        
        rows = sqldb.fetchall()
        
        # Filter for first 3 pages chunks
        first_pages_chunks = []
        for row in rows:
            content = row[0]
            region_json = row[1]
            
            # Try to parse region to check page number
            if region_json:
                try:
                    region = json.loads(region_json)
                    page_num = region.get('page_number', 1)
                    if page_num <= 3:
                        first_pages_chunks.append(content)
                except:
                    # If parsing fails, include it (might be from early pages)
                    first_pages_chunks.append(content)
            else:
                # If no region info, include it (might be from early pages)
                first_pages_chunks.append(content)
        
        # If we found chunks from first 3 pages, use them; otherwise use first 30 chunks
        if first_pages_chunks:
            chunks_text = first_pages_chunks[:60]  # Limit to 60 chunks from first 3 pages
        else:
            # Fallback: use first 30 chunks regardless of page
            for row in rows[:30]:
                chunks_text.append(row[0])
        
        return '\n'.join(chunks_text)
    
    except Exception as e:
        Logger.error_formatted(f"Error getting chunks for document {document_id} in category {category}", e)
        return ""
    finally:
        sqldb.close()


def extract_publication_date(text: str, file_name: str) -> PublicationDateResult:
    """Extract publication date from text using Claude Sonnet via litellm"""
    
    prompt = f"""Analyze the following text from the first 3 pages of a document titled "{file_name}" and extract the publication date if present.

Text to analyze:
{text[:200_000]}  # Limit text to avoid token limits

Instructions:
1. Look for explicit publication dates, copyright dates, or dates when the document was published/released
2. Common patterns include: "Published on", "Publication Date:", copyright symbols with years, dates in headers/footers
3. If no date is found in the content, check if the filename contains a clear date reference (e.g., "December-2021", "2024", etc.)
4. If multiple dates are found, prefer the most recent publication/revision date
5. Convert any date found to YYYY-MM-DD format
6. If only a year is found, use YYYY-01-01 (January 1st as default)
7. If only month and year are found, use YYYY-MM-01 (1st day of the month as default)

Return a JSON object with:
- has_publication_date: boolean indicating if a date was found
- publication_date: the date in YYYY-MM-DD format (null if not found)
- confidence: "high" (explicit publication date), "medium" (copyright or inferred date), or "low" (uncertain)
- reasoning: brief explanation of how the date was determined or why none was found
"""

    try:
        # Use Claude Sonnet 4 model
        model = "claude-sonnet-4-20250514"
        
        # Determine response format based on model
        if model.startswith('together_ai'):
            response_format = {
                "type": "json_object",
                'schema': PublicationDateResult.model_json_schema()
            }
        else:
            response_format = PublicationDateResult
        
        # Make the API call with structured output
        response = litellm.completion_with_retries(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            temperature=0.1  # Low temperature for more consistent results
        )
        
        # Parse the response
        response_content = response.choices[0].message.content
        result = json.loads(response_content)
        
        # Handle different response formats
        if 'properties' in result:
            # Claude sometimes wraps the response in a properties key
            result = result['properties']
        
        return PublicationDateResult(**result)
    
    except Exception as e:
        Logger.error_formatted(f"Error extracting publication date for {file_name}", e)
        # Return a default result on error
        return PublicationDateResult(
            has_publication_date=False,
            publication_date=None,
            confidence="low",
            reasoning=f"Error during extraction: {str(e)}"
        )


def update_document_publication_date(document_id: int, publication_date: str):
    """Update the publication date for a document"""
    sqldb = dbs.document_db
    
    try:
        sqldb.open()
        sqldb.begin_transaction()
        
        sqldb.update(
            "UPDATE DOCUMENT SET PUBLICATION_DATE = ? WHERE ID = ?",
            (publication_date, document_id)
        )
        
        sqldb.commit()
        Logger.info(f"Updated document {document_id} with publication date: {publication_date}")
    
    except Exception as e:
        sqldb.rollback()
        Logger.error_formatted(f"Error updating document {document_id}", e)
        raise e
    finally:
        sqldb.close()


def main():
    """Main function to process all documents"""
    Logger.info("Starting publication date extraction process")
    
    # Get all documents
    documents = get_all_documents()
    Logger.info(f"Found {len(documents)} documents to process")
    
    processed = 0
    updated = 0
    errors = 0
    
    for doc in documents:
        # Skip if already has a publication date
        if doc['publication_date']:
            Logger.info(f"Skipping {doc['file_name']} - already has publication date: {doc['publication_date']}")
            continue
        
        try:
            Logger.info(f"Processing: {doc['file_name']} (ID: {doc['id']})")
            
            # Get first page chunks
            chunks_text = get_first_page_chunks(doc['id'], doc['category'])
            
            
            if not chunks_text:
                Logger.warning(f"No chunks found for document {doc['id']}")
                continue
            
            # Extract publication date
            result = extract_publication_date(chunks_text, doc['file_name'])
            
            Logger.info(f"Result: {result.model_dump()}")
            
            # Update database if date was found
            if result.has_publication_date and result.publication_date:
                update_document_publication_date(doc['id'], result.publication_date)
                updated += 1
            
            processed += 1
            
            # Add a small delay to avoid rate limiting
            if processed % 10 == 0:
                Logger.info(f"Progress: {processed}/{len(documents)} documents processed, {updated} updated")
        
        except Exception as e:
            Logger.error_formatted(f"Error processing document {doc['id']}", e)
            errors += 1
            continue
    
    # Final summary
    Logger.info(f"""
    Publication Date Extraction Complete:
    - Total documents: {len(documents)}
    - Processed: {processed}
    - Updated: {updated}
    - Errors: {errors}
    - Skipped (already had dates): {len(documents) - processed - errors}
    """)


if __name__ == "__main__":
    # The API key should be loaded from the config when we import Config
    # No need to check for environment variables explicitly
    main() 
