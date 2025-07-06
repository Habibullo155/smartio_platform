# app/schemas/smartio_schemas.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional
from datetime import datetime, date
import uuid # Импортируем uuid

# --- Общие схемы ---

class Token(BaseModel):
    access_token: str
    token_type: str
    client_id: int
    client_username: str
    client_company_name: str
    client_db_id: str

    model_config = ConfigDict(
        json_encoders={uuid.UUID: str}
    )


class TokenData(BaseModel):
    username: Optional[str] = None
    client_id: Optional[int] = None
    client_company_name: Optional[str] = None
    client_db_id: Optional[str] = None


# --- Схемы для Client ---

class ClientBase(BaseModel):
    username: str
    company_name: str
    company_type: str
    inn: Optional[str] = None
    contact_email: EmailStr
    phone_number: Optional[str] = None
    subscription_type_id: int
    is_active: bool = True

class ClientCreate(ClientBase):
    password: str

class ClientUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    company_name: Optional[str] = None
    company_type: Optional[str] = None
    inn: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    subscription_type_id: Optional[int] = None
    purchase_date: Optional[datetime] = None
    renewal_date: Optional[datetime] = None
    is_active: Optional[bool] = None

class ClientLogin(BaseModel):
    username: str
    password: str


class SubscriptionTypeResponse(BaseModel):
    id: int
    name: str
    options: List[str]
    price: float
    discount: float
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )


class ClientResponse(ClientBase):
    id: int
    client_db_id: uuid.UUID # Это поле остается UUID, так как оно приходит из БД как UUID
    purchase_date: datetime
    renewal_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    subscription_type: Optional[SubscriptionTypeResponse] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat(), uuid.UUID: str} # Кодировщик все еще нужен
    )


# --- Схемы для SubscriptionType ---

class SubscriptionTypeCreate(BaseModel):
    name: str
    options: List[str] = Field(default_factory=list, max_length=10)
    price: float = Field(ge=0)
    discount: float = Field(ge=0, le=100)
    is_active: bool = True

class SubscriptionTypeUpdate(BaseModel):
    name: Optional[str] = None
    options: Optional[List[str]] = Field(default=None, max_length=10)
    price: Optional[float] = Field(default=None, ge=0)
    discount: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None


# --- Схемы для AdminUser ---

class AdminUserBase(BaseModel):
    username: str
    email: EmailStr
    is_superadmin: bool = False
    is_active: bool = True

class AdminUserCreate(AdminUserBase):
    password: str

class AdminUserResponse(AdminUserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

class AdminLogin(BaseModel):
    username: str
    password: str


# --- Схемы для SocialAccount ---

class SocialAccountBase(BaseModel):
    provider: str
    social_id: str
    email: Optional[EmailStr] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class SocialAccountCreate(SocialAccountBase):
    pass

class SocialAccountResponse(SocialAccountBase):
    id: int
    client_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )


# --- Схемы для PaymentTransaction ---

class PaymentTransactionBase(BaseModel):
    client_id: int
    subscription_type_id: int
    amount: float = Field(ge=0)
    currency: str = "USD"
    status: str = Field(pattern="^(pending|completed|failed|refunded)$")
    transaction_date: datetime
    payment_gateway_id: Optional[str] = None
    payment_method: Optional[str] = None
    description: Optional[str] = None

class PaymentTransactionCreate(PaymentTransactionBase):
    pass

class PaymentTransactionResponse(PaymentTransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    subscription_type: Optional[SubscriptionTypeResponse] = None

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

# --- Схемы для BlogPost ---

class BlogPostBase(BaseModel):
    title: str
    short_description: Optional[str] = None
    content: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    is_published: bool = False

class BlogPostCreate(BlogPostBase):
    pass # Все поля уже определены в BlogPostBase

class BlogPostUpdate(BaseModel):
    title: Optional[str] = None
    short_description: Optional[str] = None
    content: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None

class BlogPostResponse(BlogPostBase):
    id: int
    author_id: int
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    author: Optional[AdminUserResponse] = None # Добавлено для связи с автором

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )

# --- Схемы для FuturePlan ---

class FuturePlanBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True

class FuturePlanCreate(FuturePlanBase):
    pass # Все поля уже определены в FuturePlanBase

class FuturePlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None

class FuturePlanResponse(FuturePlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda dt: dt.isoformat()}
    )
