from pydantic import BaseModel

# LLM Role-related Pydantic models

class LLMRoleItem(BaseModel):
    id: str
    role: str
    ownerId: str

class CreateLLMRoleRequest(BaseModel):
    role: str
