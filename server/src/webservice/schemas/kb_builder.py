from pydantic import BaseModel
from typing import Dict, Any

# KB Builder-related Pydantic models

class KBBuilderResponse(BaseModel):
    """Response model for knowledge base builder status"""
    status: str | bool
