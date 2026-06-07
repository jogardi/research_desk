from fastapi import APIRouter, HTTPException, Depends
from webservice.excerpts.db_operations import get_excerpt_chunks_with_category
from webservice.session_manager import protected
from webservice.schemas.excerpt import ExcerptResponse
from shared.logger import Logger
from webservice.session_manager import protected_user_kb_name

router = APIRouter(tags=["excerpt"], dependencies=[Depends(protected)])

@router.get("/api/excerpt/{hash_id}", response_model=ExcerptResponse)
def get_excerpt(hash_id: str, kb_name: str = Depends(protected_user_kb_name)):
    """Get excerpt information including chunks and PDF regions by hash
    
    Parameters
    ----------
    hash_id : str
        The 4-character hash of the excerpt
        
    Returns
    -------
    JSON response with excerpt data or error
    """
    result, error_msg, status_code = get_excerpt_chunks_with_category(hash_id, kb_name)
    
    if error_msg:
        Logger.error(f"Excerpt retrieval failed: {error_msg}", report=True)
        raise HTTPException(status_code=status_code, detail=error_msg)
    
    return result 