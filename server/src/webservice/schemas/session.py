from pydantic import BaseModel

# Session-related Pydantic models

class SessionItem(BaseModel):
    id: str | int  # Handle both string and int IDs from database
    name: str
    description: str

class CreateSessionRequest(BaseModel):
    name: str
    description: str

class CreateSessionResponse(BaseModel):
    sessionItem: SessionItem
    sessionDetail: dict

class UpdateSessionRequest(BaseModel):
    name: str
    description: str
    detail: dict

class DeleteSessionResponse(BaseModel):
    message: str

class UpdateSessionResponse(BaseModel):
    message: str 