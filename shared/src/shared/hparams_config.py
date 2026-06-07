from functools import lru_cache
from shared.config import Config


@lru_cache()
def hpc():
    from shared.utils import dict2obj
    
    kb=Config.knowledgebases[0]
    default_hparams = dict(
        #both
        EMBED_MODEL=kb.EMBED_MODEL,
        HNSWLIB_MAX_ELEMENTS=kb.HNSWLIB_MAX_ELEMENTS,
        HNSWLIB_EF_CONSTRUCTION=kb.HNSWLIB_EF_CONSTRUCTION,
        HNSWLIB_M=kb.HNSWLIB_M,
        
        #kbblsder
        MAX_TOKENS_IN_CHUNK=kb.MAX_TOKENS_IN_CHUNK,
        IS_LATE_CHUNKING=kb.IS_LATE_CHUNKING,
        LATE_CHUNKING_BATCH_SIZE=kb.LATE_CHUNKING_BATCH_SIZE,
        PDF_RESOLUTION=kb.PDF_RESOLUTION
    )
            
    return dict2obj(default_hparams)
