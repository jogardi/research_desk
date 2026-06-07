from pydantic import BaseModel
from .user import UserResponse

# Social login-related Pydantic models

class SocialLoginFinishResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse 