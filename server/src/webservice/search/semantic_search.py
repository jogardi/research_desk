import os
import random
import re
import json
import torch
os.environ["HF_HUB_DISABLE_TQDM"] = "1"

import numpy as np
# Load the SentenceTransformer model first to initialize PyTorch/CUDA environment
# This is critical for the FlagEmbedding model to work properly
from sentence_transformers import SentenceTransformer

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Dict
from pathlib import Path
from functools import lru_cache
from datetime import datetime
from bs4 import BeautifulSoup

from shared.kb_folders import DB_FOLDER

# Create a persistent process pool to avoid overhead of creating processes each time
_process_pool = None

def get_process_pool():
    """Get or create a persistent process pool"""
    global _process_pool
    if _process_pool is None:
        _process_pool = ThreadPoolExecutor(max_workers=1)
    return _process_pool

@lru_cache()
def highlighter_process_pool():
    return ProcessPoolExecutor(max_workers=2)

@lru_cache()
def minilm():
    print("loading sentence transformer model")
    #return SentenceTransformer("all-MiniLM-L6-v2", device='mps')
    #Use MPS if available, otherwise fall back to CPU
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    return SentenceTransformer("all-MiniLM-L6-v2", device=device)

from shared.logger import Logger
from shared.embedding.sentence_transformer import  sentence_transformer_model
from webservice.hparams_config import hpc
from webservice.categoryDBFilePaths import CategoryDBFilePaths
from shared.config import Config
from shared.sqlite import SQLite
from shared.config import Config
from shared.utils import timing
from shared.keyword_search import nltk_remove_stopwords

from webservice.llm.together.rerank import Reranker
from webservice.search.semantic_nouns import get_query_embedding, get_nouns, get_semantic_nouns_batch
from webservice.persistence.app_sqlite import AppSqlite
from webservice.search.search_util import numeric_tokens_percentage
from webservice.search.vector_db.hnswlib import HnswlibVectorDB
# from webservice.llm.together.title_chat import generate_title
from webservice.persistence.document_sqlite import DocumentSqlite
from webservice.search.search_util import fill_adjacent_numbers, fix_sup_tags
from webservice.search.math_processor import process_math_in_documents

line_breaks_pattern = r'\r\n|\r|\n|<br\s*/?>|<br>|</?p\s*>' 

def remove_linebreaks_and_list_tags(text: str) -> str:
    """
    Removes all types of line breaks and HTML list tags from text.
    
    Parameters:
    - text: the input text string
    
    Returns: the text with line breaks and list tags removed
    """
    if text is None:
        return None
    
    if not text:
        return text
    
    # Remove all types of line breaks and replace with spaces
    # This includes \n, \r, \r\n, and any HTML line break tags
    text = re.sub(line_breaks_pattern, ' ', text)
    
    # Remove extra whitespace (multiple spaces, tabs)
    # text = re.sub(r'\s+', ' ', text)
    
    # Strip leading and trailing whitespace
    return text

@lru_cache()
def get_lucene_analyzer():
    from pyserini.analysis import Analyzer, get_lucene_analyzer
    return Analyzer(get_lucene_analyzer(stemming=False))


def _is_CSV(text: str) -> bool:
    """
    Detect if text is in CSV format where rows are separated by '<br>' or '<br/>'.
    
    Args:
        text: The text to analyze
        
    Returns:
        bool: True if the text appears to be CSV format, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    # Try both <br> and <br/> as row separators
    rows = []
    if '<br/>' in text:
        rows = text.split('<br/>')
    elif '<br>' in text:
        rows = text.split('<br>')
    else:
        # No br tags found, check if it's regular CSV with newlines
        rows = text.split('\n')
    
    # Need at least 2 rows to be considered CSV
    if len(rows) < 2:
        return False
    
    # Remove empty rows and strip whitespace
    non_empty_rows = [row.strip() for row in rows if row.strip()]
    
    if len(non_empty_rows) < 2:
        return False
    
    # Check if rows have consistent comma-separated structure
    comma_counts = []
    for row in non_empty_rows:
        # Count commas in each row
        comma_count = row.count(',')
        comma_counts.append(comma_count)
    
    # For CSV, most rows should have the same number of commas (columns - 1)
    # Allow for some variation (e.g., header row might be different)
    if len(set(comma_counts)) == 1 and comma_counts[0] > 0:
        # All rows have same number of commas and at least one comma
        return True
    elif len(set(comma_counts)) <= 2 and max(comma_counts) > 0:
        # At most 2 different comma counts (e.g., header + data rows) and at least one comma
        # Check if the majority of rows have the same comma count
        from collections import Counter
        count_freq = Counter(comma_counts)
        most_common_count, most_common_freq = count_freq.most_common(1)[0]
        
        # If most rows have the same comma count and it's > 0, likely CSV
        if most_common_freq >= len(non_empty_rows) * 0.7 and most_common_count > 0:
            return True
    
    return False


def bm25_search(categoryDBFilePaths: CategoryDBFilePaths, user_query: str, top_k: int = 5):
    from pyserini.search.lucene import LuceneSearcher
    lucene_bm25_searcher = LuceneSearcher(categoryDBFilePaths.lucene_dir_path)
    hits = lucene_bm25_searcher.search(nltk_remove_stopwords(user_query), k=top_k)
    scores = np.array([hit.score for hit in hits])
    return [int(hit.docid) for hit in hits], scores.tolist()

def merge_search_results(docids1, scores1, docids2, scores2, weight2, top_k) -> Dict[str, float]:
    """
    if same doc id is in both, average the scores
    """
    print("bm25 scores: ", scores2, docids2)
    print("semantic scores", docids1)
    merged_scores = {}
    for docid, score in zip(docids1, scores1):
        merged_scores[docid] = (1-weight2) * score
    for docid, score in zip(docids2, scores2):
        if docid in merged_scores:
            print("merging scores", docid, merged_scores[docid], score)
            merged_scores[docid] = ((1-weight2) * merged_scores[docid] + weight2 * score)
        else:
            merged_scores[docid] = weight2 * score
    
    # take top k
    top_docs = sorted(merged_scores.keys(), key=lambda x: merged_scores[x], reverse=True)[:top_k]
    return {docid: merged_scores[docid] for docid in top_docs}

@lru_cache()
def load_vector_db(path):
    try:
        # Try FlagEmbedding first (SentenceTransformer initialization above should allow this to work)
        embedding_model = sentence_transformer_model()
        dim = embedding_model.dim() # get the dimensionality of the embeddings
    except Exception as e:
        print(f"FlagEmbedding failed, using SentenceTransformer: {e}")
        # Fallback to SentenceTransformer
        embedding_model = minilm()
        embedding_model.embed = embedding_model.encode
        embedding_model.dim = lambda: len(embedding_model.encode("test"))
        dim = embedding_model.dim()
    
    vector_db = HnswlibVectorDB(path, dim) 
    print("vector_db", path)
    # load the hnswlib index
    vector_db.load()
    return embedding_model, vector_db


def semantic_search(categoryDBFilePaths: CategoryDBFilePaths, user_query: str, kb_name: str, top_k: int = 5, query_embedding=None):
    # initialize the embedding model

    # initialize the vector DB index
    embedding_model, vector_db = load_vector_db(categoryDBFilePaths.hnswlib_file_path)
    Logger.info(f"Loaded vector database: {categoryDBFilePaths.hnswlib_file_path}\n")

    # generate text embedding for the user query (only if not provided)
    if query_embedding is None:
        query_embedding = embedding_model.embed(user_query)

    # retrieve nearest neighbors for user query:
    if hpc().ENABLE_SEMANTIC:
        ids, similarity_scores = vector_db.retrieve(query_embedding, k=top_k)
    else:
        ids = []
        similarity_scores = []
    vector_ids = ids
    print("num results", len(ids), top_k)
    if hpc().ENABLE_LUCENE:
        scores = merge_search_results(ids, similarity_scores, *bm25_search(categoryDBFilePaths, user_query, top_k), hpc().BM25_WEIGHT, top_k)
    else:
        scores = {}
        for id, score in zip(ids, similarity_scores):
            scores[id] = score

    
    ids = list(scores.keys())
    if len(ids) == 0:
        return []
    comma_separated_string = ", ".join(map(str, ids))
    
    # Get adjacent numbers for the full expanded search
    in_clause = fill_adjacent_numbers(comma_separated_string, hpc().SENTENCE_BEFORE_OFFSET, hpc().SENTENCE_AFTER_OFFSET)

    sqldb = SQLite(categoryDBFilePaths.sqlite_file_path)  

    try:
        sqldb.open() 

        Logger.info(f"Opened database: {categoryDBFilePaths.hnswlib_file_path}\n")

        sqldb.select(f"select ROWID as ID, CONTENT, DOCUMENT_ID, TITLE, CONCISE_CONTENT, REGION from CHUNK where ROWID in ({in_clause})")
        unfiltered_rows = sqldb.fetchall()
        
        rows = []
        for row in unfiltered_rows:
            if re.sub(line_breaks_pattern + r'|</?li>', '', row[1]).strip() != '':
                rows.append(row)

        Logger.info(f"Retrieved {len(rows)} chunks from the database\n"   )
        
        # First pass: collect regions from original search results
        original_regions = set()
        for row in rows:
            row_id = row[0]
            should_add = row_id in scores
            if hpc().INCLUDE_ENTIRE_BLOCK_OF_ADJ_SENTENCES:
                should_add = should_add or row_id - 1 in scores or row_id + 1 in scores

            if should_add:  # This is an original search result
                original_regions.add(row[5])  # row[5] is the REGION column
        
        chunks = []

        for row in rows:
            if DocumentSqlite.is_flagged_document(row[2], kb_name): 
                Logger.debug(f"Document {row[2]} is flagged, skipping ...")
                continue
            
            row_id = row[0]
            row_region = row[5]

            # Only include this chunk if:
            # 1. It's an original search result, OR
            # 2. It's an adjacent chunk with a region that matches one of the original results
            if row_id not in scores and row_region not in original_regions:
                continue
                 
            # content = ' '.join(row[1].split())  # Remove extra spaces from the content
            content = row[1]
            is_csv = _is_CSV(content)

            # Fix escaped sup tags
            content = fix_sup_tags(content)



            # Generate title 
            title = row[3]  
            
            used_marker = True
            id = row[0]
            # Create a dictionary for the chunk
            region = json.loads(row[5])
            if scores.get(id) is None:
                if region.get('vertical_position') == None:
                    used_marker = False
                    dist_to_nearest_neighbor = min(abs(id - hit_id) for hit_id in scores.keys())
                    if dist_to_nearest_neighbor > 1:
                        continue
                score = 2
            else:
                score = scores[id]

            # Remove line breaks and list tags if enabled
            if hpc().REMOVE_LI_TAGS:
                content = re.sub(r'</?li>', ' ', content)
            if used_marker and hpc().REMOVE_LINEBREAKS and not is_csv:
                print("+++ removing linebreaks +++")
                content = remove_linebreaks_and_list_tags(content)

            
            # If there's an image URL, clear the text content (which is the description)
            if region.get('image_url'):
                content = ""
            
            chunk_text = content
            if (not is_csv):
                print("***removing linebreaks***")
                chunk_text = content if hpc().REMOVE_LINEBREAKS else content.replace('\n', '<br/>')

            chunk = { 
                "id": id, 
                "title": title, 
                "text": chunk_text, 
                "concise_text": row[4], 
                "documentID": row[2],
                "region": region,
                "search": "Semantic", 
                "score": score, 
                "status": "O", 
                "checked": False,
                "vector": id in vector_ids
                }
            chunks.append(chunk)
    except Exception as e:
        print(f"An error occurred when retrieving the chunks from the SQL database:\n {e}")
        raise e
    finally:
        sqldb.close() # Close the database for the category
    print("num chunks", len(chunks))

    # put more weight on adjacent chunks
    sorted_chunks = sorted(chunks, key=lambda x: x['id'])
    sorted_chunk_scores = [chunk['score'] for chunk in sorted_chunks]
    for i in range(len(sorted_chunks) - 1):
        chunk = sorted_chunks[i]
        next_chunk = sorted_chunks[i + 1]
        if next_chunk['id'] - chunk['id'] == 1:
            chunk['score'] +=  hpc().BEFORE_SENTENCE_WEIGHT * sorted_chunk_scores[i + 1]
            next_chunk['score'] +=  hpc().BEFORE_SENTENCE_WEIGHT * sorted_chunk_scores[i]
            # if the region of next_chunk is different from the region of the current chunk put a line break at the end of the current chunk
            # but don't add a br tag if the previous chunk ends with '</li>' because that creates 2 line breaks
            if next_chunk['region'] != chunk['region'] and not chunk['text'].strip().endswith('</li>') and len(chunk['text'].strip()) > 0:
                chunk['text'] += '<br/>'

    return chunks


def _search_category(args):
    """Helper function to perform semantic search for a single category"""
    category, user_query, top_k, query_embedding, kb_name = args
    categoryDBFilePaths = CategoryDBFilePaths(kb_name)
    categoryDBFilePaths.generate_file_paths(category)
    try:
        return semantic_search(categoryDBFilePaths, user_query, kb_name, top_k, query_embedding)
    except Exception as e:
        Logger.error("Failed to perform semantic search.", exception=e, report=True)
        return None


def _perform_semantic_search_and_filter(categories_str: str, user_query: str, top_k: int, kb_name: str, is_for_ui=True):
    """
    Performs the semantic search (for given categories and query) and applies 
    filtering rules. Returns a tuple of (chunks_list, error_response_or_None, status_code)
    where chunks_list is the processed list of chunks if successful,
    and error_response_or_None is either None (if no error) or a Flask response.

    Parameters:
    - categories_str: a comma-separated string of category names
    - user_query: the query string
    - top_k: the number of top chunks to return

    Returns: 
    - chunks_list: the list of chunks if successful
    - error_response_or_None: either None (if no error) or a Flask response
    - status_code: the HTTP status code. 200 if successful, otherwise an error code.
    """
    if not categories_str:
        return ([], ({ 'error': 'No categories provided.' }), 400)
    if not user_query:
        return ([], ({ 'error': 'No query provided.' }), 400)
    

    
    categories = categories_str.split(',')

    # Compute query embedding once for all categories
    try:
        # Try FlagEmbedding first (SentenceTransformer initialization above should allow this to work)
        embedding_model = sentence_transformer_model()
        query_embedding = embedding_model.embed(user_query)
    except Exception as e:
        print(f"FlagEmbedding failed, using SentenceTransformer: {e}")
        # Fallback to SentenceTransformer
        embedding_model = minilm()
        query_embedding = embedding_model.encode(user_query)

    all_chunks = []
    
    # Process categories sequentially to avoid threading issues
    # for category in categories:
    #     categoryDBFilePaths = CategoryDBFilePaths()
    #     categoryDBFilePaths.generate_file_paths(category)
        
    #     try:
    #         chunks = semantic_search(categoryDBFilePaths, user_query, top_k)
    #         all_chunks.extend(chunks)
    #     except Exception as e:
    #         Logger.error("Failed to perform semantic search.", exception=e, report=True)
    #         return (
    #             [],
    #             ({'error': 'Failed to perform semantic search.'}),
    #             500
    #         )
    # TODO: re-enable parallel processing
    with timing('parallel_search'):
        with ThreadPoolExecutor(max_workers=16) as executor:
            # Create args list for each category, now including the pre-computed query embedding and kb_name
            search_args = [(category, user_query, top_k, query_embedding, kb_name) for category in categories]

            # Execute searches in parallel
            futures = list(executor.map(_search_category, search_args))

            # Process results
            for chunks in futures:
                if chunks is None:  # Error occurred
                    return (
                        [],
                        ({'error': 'Failed to perform semantic search.'}),
                        500
                    )
                all_chunks.extend(chunks)

    if len(all_chunks) == 0:
        # No chunks found, return empty list
        return ([], None, 200)

    # Filter out chunks with score below the threshold
    all_chunks = [ chunk for chunk in all_chunks if chunk['score'] > hpc().SEMANTIC_SEARCH_SCORE_THRESHOLD ]

    # remove chunks with numeric token percentage above the threshold
    all_chunks = [ chunk for chunk in all_chunks if numeric_tokens_percentage(chunk['text']) < 30 ]
    all_chunks = [ chunk for chunk in all_chunks if '(cid:' not in chunk ]
    # all_chunks = [ chunk for chunk in all_chunks if len(chunk['text']) > 450 ]
    
    # Filter out chunks that are just list item numbers (e.g., <li>3. </li>)
    all_chunks = [ 
        chunk for chunk in all_chunks 
        if not re.match(r'^<li>\d+\.?\s*(?:</li>)?$', chunk['text'].strip())
    ]

    # Log the query
    AppSqlite.log_ss_query(','.join(categories), user_query, kb_name)

    return (all_chunks, None, 200)


def _group_chunks_by_document(chunks, kb_name: str):
    """
    Groups chunks by documentID and returns a list of documents, where each document
    contains the following fields:
    - documentID: the document ID
    - documentName: the document file name
    - documentCategory: the document category path
    - chunks: a list of chunks for the document
    - excerpts: a list of excerpts, where each excerpt is a list of two integers
        representing the start and end indices of the chunk list for the excerpt.

    Filter out excerpts that are just a single number and nothing else.

    Returns something like:
    [
        {
            'documentID': '123',
            'documentName': 'documentName',
            'documentCategory': 'documentCategory',
            'chunks': [
                {
                    'id': '123',
                    'title': 'title',
                    'text': 'text',
                    'concise_text': 'concise_text',
                    'documentID': '123',
                    'search': 'Semantic',
                    'score': 0.5,
                    'status': 'O',
                    'checked': False
                }
            ],
            'excerpts': [[0, 1]]
        }
    ]

    Parameters:
    - chunks: a list of chunks, where each chunk 

    Returns: a list of documents

    """
    # group chunks by documentID
    from collections import defaultdict
    doc_map = defaultdict(list)
    for c in chunks:
        doc_map[c['documentID']].append(c)

    # get FILE_NAME for each documentID from DOCUMENT table
    doc_ids = list(map(str, doc_map.keys()))
    sqldb = SQLite(f'{DB_FOLDER(kb_name)}/document.db')
    sqldb.open()
    sqldb.select(f"select ID, CATEGORY, FILE_NAME, PUBLICATION_DATE, DOC_TYPE from DOCUMENT where ID in ({','.join(doc_ids)})")
    rows = sqldb.fetchall()
    doc_name_map = {row[0]: {'category': row[1], 'file_name': row[2], 'publication_date': row[3], 'doc_type': row[4]} for row in rows}

    # sort each doc's chunks by 'id' ascending
    #   convert chunk['id'] to int if needed
    for doc_id, doc_chunks in doc_map.items():
        doc_chunks.sort(key=lambda x: int(x['id']))

    # build response structure
    response = []
    #  for each doc, find consecutive blocks of chunks
    for doc_id, doc_chunks in doc_map.items():
        consecutive_blocks = []
        block_start_idx = 0
        for i in range(1, len(doc_chunks)):
            if doc_chunks[i]['id'] - doc_chunks[i-1]['id'] == 1:
                continue
            consecutive_blocks.append([block_start_idx, i-1])
            block_start_idx = i
        consecutive_blocks.append([block_start_idx, len(doc_chunks) - 1])

        # Filter out excerpts that are just numbers and nothing else
        def is_excerpt_just_number(start_idx, end_idx):
            """Check if an excerpt contains only chunks with numeric-only text content"""
            for i in range(start_idx, end_idx + 1):
                chunk_text = doc_chunks[i].get('text', '').strip()
                # Remove HTML tags for checking
                import re
                clean_text = re.sub(r'<[^>]*>', '', chunk_text).strip()
                # If any chunk in the excerpt has non-numeric content, keep the excerpt
                if clean_text and not re.match(r'^\d+\.?\s*$', clean_text):
                    return False
            return True
        
        # Filter out number-only excerpts
        filtered_consecutive_blocks = [
            block for block in consecutive_blocks 
            if not is_excerpt_just_number(block[0], block[1])
        ]

        if (doc_name_map[doc_id]['publication_date'] is None):
            # if publication date is None, set it to today's date
            publication_date = datetime.now().strftime("%Y-%m-%d")
        else:
            publication_date = doc_name_map[doc_id]['publication_date']

        doc_type = doc_name_map[doc_id]['doc_type']

        response.append({
            'documentID': doc_id,
            'documentName': doc_name_map[doc_id]['file_name'],
            'documentCategory': doc_name_map[doc_id]['category'],
            'publicationDate': publication_date,
            'docType': doc_type,
            'chunks': doc_chunks,
            'excerpts': filtered_consecutive_blocks
        })

    return response


def _rerank(documents, user_query):
    """
    Reranks the documents based on the user query using the Together model.
    Returns a list of scores in the same order as the input documents.

    Parameters:
    - documents: a list of documents, where each document is a dictionary
    - user_query: the user query string

    Returns: List[float] - scores for each document in the same order as input

    """
    if True:
        for doc in documents:
            doc['score'] = random.random()
        return [doc['score'] for doc in documents]
    
    reranker = Reranker(hpc().RERANK_TOGETHER_MODEL)
    
    # Choose reranking method based on configuration
    rerank_method = hpc().RERANK_METHOD
    
    if rerank_method == 'flashrank':
        # Use FlashRank for local, fast reranking
        print("*** RERANK: Using FlashRank for document reranking")
        
        # Extract document text for reranking
        # TODO this is not the right way to get document_texts
        document_texts = []
        for doc in documents:
            # Combine document name and chunk texts for better reranking
            doc_text = f"{doc.get('documentName', '')} "
            for chunk in doc.get('chunks', []):
                # Use concise_text if available, otherwise use regular text
                chunk_text = chunk.get('concise_text') or chunk.get('text', '')
                # Remove HTML tags for cleaner text
                import re
                chunk_text = re.sub(r'<[^>]+>', ' ', chunk_text)
                doc_text += chunk_text + " "
            document_texts.append(doc_text.strip())
        
        ranking = reranker.flashrank(user_query, document_texts)
        
    else:
        # Use Together API for reranking (default behavior)
        print(f"*** RERANK: Using Together API ({hpc().RERANK_TOGETHER_MODEL}) for document reranking")
        ranking = reranker.rerank(user_query, documents)

    if ranking is None: # error occurred
        print("*** RERANK: Error occurred during reranking, using original scores")
        for doc in documents:
            doc['score'] = 1.0
        return [1.0] * len(documents)

    # Create a list to store scores in original document order
    scores = [0.0] * len(documents)
    
    # Map reranked scores back to original document positions
    for rank in ranking:
        original_index = rank['index']
        score = rank['score']
        # Convert numpy types to regular Python floats for consistency
        if hasattr(score, 'item'):  # numpy scalar
            scores[original_index] = float(score.item())
        else:
            scores[original_index] = float(score)

    print(f"*** RERANK: Successfully reranked {len(documents)} documents using {rerank_method}")
    return scores

def searchSemanticByDoc(categories: str, user_query: str, kb_name: str, top_k: int = 5, is_for_ui=True):
    """
    Performs semantic search grouped by document with results sorted by score.
    Within each document, the chunks are sorted by id (from lowest to highest).

    Parameters:
    - categories: comma-separated string of category names
    - user_query: the search query string
    - top_k: number of top results to return per category (default=5)

    Returns:
    - tuple (documents, error_msg, status_code) where:
        - documents: list of document results with chunks and scores
        - error_msg: error message if any, None if successful
        - status_code: HTTP status code (200 for success)
    """
    Logger.info(f'Categories: {categories}')
    with timing('searchSemanticByDoc'):

        chunks, error_msg, status_code = _perform_semantic_search_and_filter(
            categories, user_query, top_k, kb_name, is_for_ui
        )

        if error_msg is not None:
            return None, error_msg, status_code

        if len(chunks) == 0:
            return [], None, 200

        documents = _group_chunks_by_document(chunks, kb_name)
        
        if is_for_ui:
            # Run both reranking and noun highlighting in parallel
            def run_rerank(documents, user_query):
                return _rerank(documents, user_query)
            
            def run_noun_highlighting():
                with timing('get_semantic_nouns_batch'):
                    query_embedding = get_query_embedding(user_query, minilm())
                    
                    # Extract all chunks from all documents for batch processing
                    all_chunks = []
                    for doc in documents:
                        all_chunks.extend(doc['chunks'])
                    
                    # Process all chunks at once (much faster)
                    return get_semantic_nouns_batch(user_query, query_embedding, all_chunks, minilm())
            
            with timing('parallel_rerank_and_highlighting'):
                executor = get_process_pool()
                # Submit both tasks to run in parallel
                rerank_future = executor.submit(_rerank, documents, user_query)
                # highlighting_future = executor.submit(run_noun_highlighting)
                
                # Wait for both to complete
                highlighted_chunks = run_noun_highlighting()
                rerank_scores = rerank_future.result()
            
            # Apply reranking scores to documents
            for i, doc in enumerate(documents):
                doc['score'] = rerank_scores[i]
            
            # Sort documents by their reranked scores (descending order)
            documents.sort(key=lambda doc: doc['score'], reverse=True)
            
            # Update chunks in documents with highlighted versions
            # Create a mapping from chunk id to highlighted chunk
            highlighted_chunk_map = {chunk['id']: chunk for chunk in highlighted_chunks}
            
            # Update chunks in each document with highlighted versions
            for doc in documents:
                for i, chunk in enumerate(doc['chunks']):
                    if chunk['id'] in highlighted_chunk_map:
                        doc['chunks'][i] = highlighted_chunk_map[chunk['id']]
        
        if is_for_ui:
            documents = [doc for doc in documents if doc['score'] == -1.0 or doc['score'] > hpc().SEMANTIC_SEARCH_SCORE_THRESHOLD]
        else:
            for doc in documents:
                doc['score'] = 1.0

    # Process math equations in chunks before returning
    documents = process_math_in_documents(documents)

    # update the score of each chunk by adding to the score of chunks that are adjacent get more weight

    return documents, None, 200

def suggest_category(user_query: str, kb_name: str) -> List[str]:
    try:
        # Try FlagEmbedding first
        embedding_model = sentence_transformer_model()
        query_embedding = embedding_model.embed(user_query)
    except Exception as e:
        print(f"FlagEmbedding failed in suggest_category, using SentenceTransformer: {e}")
        # Fallback to SentenceTransformer
        query_embedding = minilm().encode(user_query)
    
    db_path = str(Path(DB_FOLDER(kb_name)) / 'vector_db/categories.bin')
    vector_db = HnswlibVectorDB(db_path, query_embedding.shape[0])
    vector_db.load()

    ids, similarity_scores = vector_db.retrieve(query_embedding, k=1)
    return DocumentSqlite.get_categories_by_ids(ids, kb_name)

if __name__ == '__main__':
    input_string = "101,109,120,128"
    result = fill_adjacent_numbers(input_string,2,2)
    print(result)
