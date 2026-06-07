from pydantic import BaseModel

# Common Pydantic models used across different modules

class MessageResponse(BaseModel):
    message: str

class ErrorResponse(BaseModel):
    error: str

 