from webservice.search.semantic_search import suggest_category, searchSemanticByDoc
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from webservice.schemas.search import (
    TitleRequest, TitleResponse, FTSResponse, ConciseRequest, ConciseResponse,
    ChunkContentResponse, ExcerptResponse, CategoriesResponse
)
from shared.logger import Logger
from shared.config import Config
from shared.utils import timing
from webservice.hparams_config import hpc
from webservice.llm.together.chunk_concise import generate_concise
from webservice.categoryDBFilePaths import CategoryDBFilePaths
import time

from webservice.search.fts_search import fts_search
from webservice.search.search_util import clean_query, get_excerpt_content
from webservice.search.search_util import get_chunk_content
from webservice.search.search_util import numeric_tokens_percentage
from webservice.keywords import getKeywords

from webservice.persistence.app_sqlite import AppSqlite

# from webservice.llm.title_generator import TitleGenerator
from webservice.llm.together.title_chat import generate_title
from concurrent.futures import as_completed
from webservice.session_manager import protected, protected_user_kb_name
from webservice.search.semantic_search import _perform_semantic_search_and_filter
from webservice.search.semantic_search import _group_chunks_by_document
from webservice.search.math_processor import process_math_in_chunks, process_math_in_documents

import os
import re
import json
import time
os.environ["HF_HUB_DISABLE_TQDM"] = "1"

# FastAPI Router for all search routes
router = APIRouter(tags=["search"], dependencies=[Depends(protected)])

def _perform_FTS_search(categories_str: str, user_query: str, kb_name: str):
    """
    Performs the Full Text Search (for given categories and query) and applies 
    filtering rules. Returns a tuple of (chunks_list, error_message_or_None, status_code)
    where chunks_list is the processed list of chunks if successful,
    and error_message_or_None is either None (if no error) or a string error message.

    Parameters:
    - categories_str: a comma-separated string of category names
    - user_query: the query string

    Returns: 
    - chunks_list & total: the list of chunks and total count if successful
    - error_message_or_None: either None (if no error) or a string error message
    - status_code: the HTTP status code. 200 if successful, otherwise an error code.
    """
    if not categories_str:
        return ([], 'No categories provided.', 400)
    if not user_query:
        return ([], 'No query provided.', 400)
    
    keywords = getKeywords(user_query)

    categories = categories_str.split(',')
    
    # Remove special characters from the user query:

    user_query = clean_query(user_query)
    
    user_query = user_query.upper() # uppercase to align with "OR", "AND", etc.

    all_chunks = [] 
    for category in categories:
        categoryDBFilePaths = CategoryDBFilePaths(kb_name)
        categoryDBFilePaths.generate_file_paths(category)
        try:
            chunks = fts_search(categoryDBFilePaths, user_query, kb_name)
        except Exception as e:
            Logger.error("Failed to perform FTS search.", exception=e, report=True)
            return (
                [],
                'Failed to perform FTS search.', 
                500
            )

        all_chunks.extend(chunks)
    
    if len(all_chunks) == 0:
        return ({ "chunks": [], "total": 0 }, None, 200)
    
    #calc min and max score:
    # scores = [chunk['score'] for chunk in all_chunks]
    # min_score = min(scores)
    # max_score = max(scores)

    for chunk in all_chunks:
        for keyword in keywords:
            # Replace the keyword in the text with bold version
            chunk['text'] = chunk['text'].replace(f' {keyword}', f' <b>{keyword}</b>')
  
        # Normalize the scores to the range [0, 1]
        # if max_score != min_score: 
        #     chunk['score'] = (chunk['score'] - min_score) / (max_score - min_score)
        # else: 
        #     chunk['score'] = 1.0 

    total_chunks = len(all_chunks)

    # remove chunks with numeric token percentage above the threshold
    all_chunks = [ chunk for chunk in all_chunks if numeric_tokens_percentage(chunk['text']) < 30 ]

    # Sort the chunks by score in descending order
    all_chunks = sorted(all_chunks, key=lambda x: x['score'], reverse=True)

    # Process math equations in chunks before returning
    all_chunks = process_math_in_chunks(all_chunks)

    AppSqlite.log_fts_query(','.join(categories), user_query, kb_name)
            
    return { "chunks": all_chunks, "total": total_chunks }, None, 200



@router.get("/api/search/semantic_by_doc", response_model=List[dict])
def search_semantic_by_doc(categories: str, query: str, topK: int, kb_name: str = Depends(protected_user_kb_name)):
    """Route handler for semantic search grouped by document."""
    Logger.info(f"search_semantic_by_doc: categories: {categories}, query: {query}, topK: {topK}")
    
    documents, error_msg, status_code = searchSemanticByDoc(categories, query, kb_name, topK, is_for_ui=True)  # Enable highlighting for UI
    
    if error_msg is not None:
        raise HTTPException(status_code=status_code, detail=error_msg)
    Logger.info(f"search_semantic_by_doc: documents retrived: {len(documents)}")
    return documents

#
# Routes
#
@router.get("/api/search/semantic", response_model=List[dict])
def search_semantic(categories: str, query: str, topK: int = 5, kb_name: str = Depends(protected_user_kb_name)):
    """Route handler for semantic search."""
    with timing(f"searchSemantic total") as total_timer:
        print(f"[TIMING] Starting semantic search for categories: {categories}, query: {query[:50]}...")

        with timing("Search phase") as search_timer:
            chunks, error_response, status_code = _perform_semantic_search_and_filter(
                categories, query, topK, kb_name, is_for_ui=True  # Enable highlighting for UI
            )
        
        if error_response is not None:
            # If the helper returned a Flask response, return it here
            return error_response, status_code
        
        # If no chunks were found but returned with code 200 
        if len(chunks) == 0:
            print(f"[TIMING] No chunks found")
            return []
        
        with timing(f"Sort {len(chunks)} chunks") as sort_timer:
            chunks.sort(key=lambda x: int(x['id'])) # sort by 'id' ascending
        
        # Process math equations in chunks before returning
        chunks = process_math_in_chunks(chunks)
        
        print(f"[TIMING] searchSemantic breakdown: search: {search_timer.elapsed:.3f}s, sort: {sort_timer.elapsed:.3f}s, chunks: {len(chunks)}")

        return chunks

@router.get("/api/search/fts", response_model=FTSResponse)
def search_fts(categories: str, query: str, kb_name: str = Depends(protected_user_kb_name)):
    """Route handler for full-text search."""
    result, error_message, status_code = _perform_FTS_search(categories, query, kb_name)

    if error_message is not None:
        raise HTTPException(status_code=status_code, detail=error_message)
    
    if len(result['chunks']) == 0:
        return FTSResponse(chunks=[], total=0)
            
    return FTSResponse(chunks=result['chunks'], total=result['total'])

@router.get("/api/search/fts_by_doc", response_model=List[dict])
def search_fts_by_doc(categories: str, query: str, kb_name: str = Depends(protected_user_kb_name)):
    """Perform full-text search and group results by document."""
    try:
        result, error_message, status_code = _perform_FTS_search(categories, query, kb_name)

        if error_message is not None:
            raise HTTPException(status_code=status_code, detail=error_message)
        
        if len(result['chunks']) == 0:
            return []
        
        documents = _group_chunks_by_document(result['chunks'], kb_name)
        
        # Process math equations in documents before returning
        documents = process_math_in_documents(documents)
        
        # documents = _rerank(documents, query) # rerank is not needed for FTS

        # sort documents by publication date so newer documents are at the top
        documents.sort(key=lambda x: x['publicationDate'], reverse=True) 

        # limit the total number of excerpts to Config.MAX_FTS_RESULTS
        total_excerpts = 0
        limited_documents = []
        
        for doc in documents:
            doc_excerpts_count = len(doc['excerpts'])
            if total_excerpts + doc_excerpts_count <= Config.MAX_FTS_RESULTS:
                # Add the entire document
                limited_documents.append(doc)
                total_excerpts += doc_excerpts_count
            else:
                break # stop adding documents if reached the limit of Config.MAX_FTS_RESULTS excerpts
        
        documents = limited_documents
        print(f"********* count of documents: {len(documents)}")
        
        return documents
        
    except HTTPException:
        raise  # Re-raise HTTPException as-is
    except Exception as e:
        Logger.error("Failed to perform FTS search by document", exception=e, report=True)
        raise HTTPException(status_code=500, detail="Failed to perform FTS search by document")

@router.post("/api/search/title", response_model=TitleResponse)
def generate_doc_title(request: TitleRequest):
    """Generate a title for the given content.

    Optionally uses the user's query to tailor the title to explain relevance.
    """
    print("generate_doc_title", request)
    # title_generatore = TitleGenerator()
    # title = title_generatore.generate_title(request.content)
    title, error_response = generate_title(request.content, getattr(request, 'user_query', None))
    if error_response is not None:
        title = "Untitled"
    return TitleResponse(title=title)

@router.post("/api/search/excerpt/concise", response_model=ConciseResponse)
def chunk_concise(request: ConciseRequest):
    """Generate concise version of content."""
    concise_content = generate_concise(request.content)  
    if concise_content is None:
        raise HTTPException(status_code=404, detail="Concise failed")
    
    return ConciseResponse(concise=concise_content)

@router.get("/api/search/chunk/content/{document_id}/{chunk_id}", response_model=ChunkContentResponse)
def chunk_content(document_id: str, chunk_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get content for a specific chunk."""
    content = get_chunk_content(document_id, chunk_id, kb_name) 
    if content is None:
        raise HTTPException(status_code=404, detail="Chunk not found")
    
    return ChunkContentResponse(content=content)

@router.get("/api/search/excerpt/chunks/{document_id}", response_model=ExcerptResponse)
def excerpt_content(document_id: str, first_chunk_id: int, last_chunk_id: int, kb_name: str = Depends(protected_user_kb_name)):
    """Get excerpt content for a range of chunks."""
    content = get_excerpt_content(document_id, first_chunk_id, last_chunk_id, kb_name) 

    if content is None:
        raise HTTPException(status_code=404, detail="Excerpt not found")
    
    return ExcerptResponse(excerpt=content)

@router.get("/api/search/category/for_query", response_model=CategoriesResponse)
def find_category_for_query(query: str, kb_name: str = Depends(protected_user_kb_name)):
    """Find related categories for a given query."""
    categories = suggest_category(query, kb_name)
    return CategoriesResponse(categories=categories)
