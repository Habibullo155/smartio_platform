from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None # Для user_id в JWT sub
    user_type: Optional[str] = None # 'admin' или 'client'

class AdminLogin(BaseModel):
    email: EmailStr
    password: str

class ClientLogin(BaseModel):
    username: str
    password: str