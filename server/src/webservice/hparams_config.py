from functools import lru_cache
from shared.config import Config
from types import SimpleNamespace as Sn

@lru_cache()
def hpc():
    from shared.utils import dict2obj
    default_hparams = dict(
        
        RERANK_TOGETHER_MODEL=Config.RERANK_TOGETHER_MODEL,
        RERANK_METHOD=Config.RERANK_METHOD,  # Options: "together", "flashrank"
        SENTENCE_BEFORE_OFFSET=Config.SENTENCE_BEFORE_OFFSET,
        SENTENCE_AFTER_OFFSET=Config.SENTENCE_AFTER_OFFSET,

        ENABLE_EXACT_SEARCH=Config.ENABLE_EXACT_SEARCH,

        LLM_MODEL_CONCISE=Config.LLM_MODEL_CONCISE,
        LLM_MODEL_SUMMARY=Config.LLM_MODEL_SUMMARY,
        LLM_MODEL_ANSWER=Config.LLM_MODEL_ANSWER,

        PROMPT_INSIGHTS=Config.PROMPT_INSIGHTS,
        PROMPT_CONCEPTS=Config.PROMPT_CONCEPTS,
        PROMPT_QUESTIONS=Config.PROMPT_QUESTIONS,
        PROMPT_SEARCH_QUERIES=Config.PROMPT_SEARCH_QUERIES,
        PROMPT_SUGGEST_QUERIES=Config.PROMPT_SUGGEST_QUERIES,
        EXCLUDE_LLM_TRAINING_DATA_INSTRUCTIONS=Config.EXCLUDE_LLM_TRAINING_DATA_INSTRUCTIONS,
    
        BM25_WEIGHT=Config.BM25_WEIGHT,
        
        USE_QUERY_FOR_TITLE=Config.USE_QUERY_FOR_TITLE,
        
        SEMANTIC_SEARCH_SCORE_THRESHOLD=Config.SEMANTIC_SEARCH_SCORE_THRESHOLD,  # this prevents the before and after sentences from coming back but at the same it brings back chunks with low scores
        ENABLE_LUCENE=Config.ENABLE_LUCENE,
               
     
        BEFORE_SENTENCE_WEIGHT=Config.BEFORE_SENTENCE_WEIGHT,
        AFTER_SENTENCE_WEIGHT=Config.AFTER_SENTENCE_WEIGHT,
        ENABLE_SEMANTIC=Config.ENABLE_SEMANTIC,
        INCLUDE_ENTIRE_BLOCK_OF_ADJ_SENTENCES=Config.INCLUDE_ENTIRE_BLOCK_OF_ADJ_SENTENCES,
        REMOVE_LINEBREAKS=Config.REMOVE_LINEBREAKS,
        REMOVE_LI_TAGS=Config.REMOVE_LI_TAGS
    )

    return dict2obj(default_hparams)
