from pydantic import BaseModel
from .common import MessageResponse, ErrorResponse

# User-related Pydantic models

class LoginRequest(BaseModel):
    login: str
    password: str

class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str
    account_type: str
    opted_in: bool
    is_closed: bool
    kb_list: list[dict]
    kb_name: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class ProfileRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    account_type: str | None = None
    opted_in: bool | None = None
    # Add other profile fields as needed

class ContactRequest(BaseModel):
    email: str
    func_area: str
    query_type: str
    message: str

class ShareRequest(BaseModel):
    categories: list[str]
    emails: str

class AllUsersResponse(BaseModel):
    users: list[dict]  # List of user objects

class ChangePasswordRequest(BaseModel):
    new_password: str

# MessageResponse and ErrorResponse imported from common.py 