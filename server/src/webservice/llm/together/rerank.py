from collections.abc import Sequence
from dataclasses import dataclass
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from shared.logger import Logger

from webservice.llm.prepare_prompts import document_to_text
from functools import lru_cache

@lru_cache()
def load_flashranker():
    print("loading flashranker")
    from flashrank import Ranker, RerankRequest
    return Ranker(model_name="ms-marco-MiniLM-L-12-v2", cache_dir="/tmp/flashrankcache")

@dataclass
class Reranker:
    model: str

    def _rerank_single_document(self, query: str, document_text: str, doc_index: int) -> dict:
        """
        Rerank a single document excerpt using the Together API.
        Returns a dict with index and score.
        """
        import requests

        url = "https://api.together.xyz/v1/rerank"

        payload = { 
            "model": self.model,
            "query": query,
            "documents": [document_text]  # Single document
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response_json = response.json()
            
            if 'error' in response_json:
                print(f"*** RANKER Error for doc {doc_index}: {response_json['error']['message']}")
                return {'index': doc_index, 'score': -1.0}
            
            # Extract the score for the single document
            if response_json.get('results') and len(response_json['results']) > 0:
                score = response_json['results'][0]['relevance_score']
                return {'index': doc_index, 'score': score}
            else:
                return {'index': doc_index, 'score': -1.0}
                
        except Exception as e:
            print(f"*** RANKER Exception for doc {doc_index}: {e}")
            return {'index': doc_index, 'score': -1.0}

    def rerank_strs_parallel(self, query: str, document_excerpts: Sequence[str], max_workers: int = 4) -> Sequence[dict]:
        """
        Rerank document excerpts in parallel using threading.
        Each document is processed in a separate thread for faster processing.
        
        Args:
            query: The search query
            document_excerpts: List of document text excerpts
            max_workers: Maximum number of concurrent threads (default: 4)
            
        Returns:
            List of dicts with 'index' and 'score' keys, sorted by score descending
        """
        if not document_excerpts:
            return []
            
        start_time = time.time()
        results = []
        
        # Process documents in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(self._rerank_single_document, query, doc_text, idx): idx
                for idx, doc_text in enumerate(document_excerpts)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    doc_index = future_to_index[future]
                    print(f"*** RANKER Thread Exception for doc {doc_index}: {e}")
                    results.append({'index': doc_index, 'score': -1.0})
        
        # Sort by score descending
        results.sort(key=lambda x: x['score'], reverse=True)
        
        elapsed = time.time() - start_time
        print(f"*** RANKER: Processed {len(document_excerpts)} documents in {elapsed:.3f}s using {max_workers} threads")
        
        return results

    def rerank_strs(self, query: str, document_excerpts: Sequence[str]) -> Sequence[int]:
        """
        Original batch reranking method (fallback for when parallel fails or for small batches).
        """
        import requests
        from litellm.utils import trim_messages

        url = "https://api.together.xyz/v1/rerank"
        max_tokens = 7_600//len(document_excerpts)

        payload = { 
            "model": self.model ,
            "query": query,
            "documents": [trim_messages([{'role': 'user', 'content': x}], max_tokens=max_tokens)[0]['content'] for x in document_excerpts]
            }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {os.getenv('TOGETHER_API_KEY')}"
        }

        try:
            response = requests.post(url, json=payload, headers=headers).json()
            if ('error' in response):  
                #  This model's maximum context length is 8192 tokens. However, you requested 25851 tokens (25850 in the messages, 1 in the completion). Please reduce the length of the messages or completion.
                Logger.error(f"*** RANKER Error:\n {response['error']['message']}", report=True)
                return None
            
            return [
                {'index': result['index'], 'score': result['relevance_score']}
                for result in response['results']
            ]
        except Exception as e:
            Logger.error(f"*** RANKER Exception", exception=e, report=True)
            return None

    def rerank(self, query: str, documents: Sequence, use_parallel: bool = False, max_workers: int = 256) -> Sequence[int]:
        """
        Rerank documents using either parallel or batch processing.
        
        Args:
            query: The search query
            documents: List of document objects
            use_parallel: Whether to use parallel processing (default: True)
            max_workers: Maximum number of concurrent threads for parallel processing (default: 4)
            
        Returns:
            List of dicts with 'index' and 'score' keys, sorted by score descending
        """
        document_texts = [document_to_text(document) for document in documents]
        
        if use_parallel and len(documents) > 1:
            print("rerank parallel")
            # Use parallel processing for multiple documents
            return self.rerank_strs_parallel(query, document_texts, max_workers)
        else:
            # Use batch processing for single document or when parallel is disabled
            return self.rerank_strs(query, document_texts)

    def flashrank(self, query: str, document_excerpts: Sequence[str]) -> Sequence[dict]:
        """
        Rerank document excerpts using FlashRank (local CPU-based reranking).
        This is a fast, lightweight alternative to API-based reranking.
        
        Args:
            query: The search query
            document_excerpts: List of document text excerpts
            
        Returns:
            List of dicts with 'index' and 'score' keys, sorted by score descending
        """
        try:
            from flashrank import Ranker, RerankRequest
        except ImportError:
            print("*** RANKER Error: FlashRank not installed. Install with: pip install flashrank")
            return [{'index': i, 'score': -1.0} for i in range(len(document_excerpts))]
        
        if not document_excerpts:
            return []
        
        try:
            # Initialize FlashRank with default model (ms-marco-TinyBERT-L-2-v2)
            ranker = load_flashranker()
            
            # Prepare passages in FlashRank format
            passages = [
                {
                    "id": i,
                    "text": doc_text,
                    "meta": {"index": i}
                }
                for i, doc_text in enumerate(document_excerpts)
            ]
            
            # Create rerank request
            rerank_request = RerankRequest(query=query, passages=passages)
            
            # Get reranked results
            results = ranker.rerank(rerank_request)
            
            # Convert FlashRank results to our standard format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'index': result['id'],
                    'score': result['score']
                })
            
            return formatted_results
            
        except Exception as e:
            print(f"*** RANKER FlashRank Exception: {e}")
            # Return original order with negative scores on error
            return [{'index': i, 'score': -1.0} for i in range(len(document_excerpts))]

