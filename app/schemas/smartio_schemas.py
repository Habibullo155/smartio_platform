# app/schemas/smartio_schemas.py

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# --- Схемы для AdminUser (понадобятся для аутентификации) ---
class AdminUserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserUpdate(AdminUserBase):
    password: Optional[str] = None # Пароль при обновлении может быть необязательным

class AdminUserInDB(AdminUserBase):
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # В старых версиях Pydantic было orm_mode = True

class AdminUser(AdminUserBase): # Схема для ответа (без хеша пароля)
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Схемы для аутентификации ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Схемы для SubscriptionType ---
class SubscriptionTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_usd: int # Пока int, потом можно Decimal
    features: Optional[str] = None # Пока строка, можно потом JSON
    is_active: Optional[bool] = True

class SubscriptionTypeCreate(SubscriptionTypeBase):
    # При создании все поля из Base обязательны (кроме Optional)
    pass

class SubscriptionTypeUpdate(SubscriptionTypeBase):
    # При обновлении все поля опциональны
    name: Optional[str] = None
    price_usd: Optional[int] = None

class SubscriptionType(SubscriptionTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True # Это позволяет Pydantic читать данные из ORM-моделей SQLAlchemy