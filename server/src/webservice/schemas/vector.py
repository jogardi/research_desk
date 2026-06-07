from pydantic import BaseModel
from typing import List, Dict, Any

# Vector database generation-related Pydantic models

class GenerateDatabasesRequest(BaseModel):
    categoryIDs: List[str]

class GenerateDatabasesResponse(BaseModel):
    message: str

class DatabaseGenerationStatusResponse(BaseModel):
    isRunning: bool
    status: Dict[str, Any]

class IsRunningResponse(BaseModel):
    isRunning: bool

class AbortResponse(BaseModel):
    message: str 