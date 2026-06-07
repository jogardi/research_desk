from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ExcerptChunk(BaseModel):
    """Individual chunk within an excerpt"""
    id: int
    text: str
    region: Optional[Dict[str, Any]] = None # optional field for region data

class ExcerptResponse(BaseModel):
    """Response model for excerpt data"""
    chunks: List[ExcerptChunk]
    document_id: int
    category: str
    docType: str 