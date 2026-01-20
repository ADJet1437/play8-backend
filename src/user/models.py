from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    name: str

class User(UserBase):
    id: str

class UserResponse(BaseModel):
    user: Optional[User] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class GoogleAuthRequest(BaseModel):
    code: str

