from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

from app.schemas.subscriptions import SubscriptionTypeResponse # Для связи с подпиской

class ClientBase(BaseModel):
    username: str
    company_name: str
    company_type: str
    inn: Optional[str] = None
    contact_email: EmailStr
    phone_number: Optional[str] = None
    subscription_type_id: Optional[int] = None
    is_active: bool = True
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None

class ClientCreate(ClientBase):
    password: str

class ClientUpdate(ClientBase):
    username: Optional[str] = None
    company_name: Optional[str] = None
    company_type: Optional[str] = None
    inn: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    phone_number: Optional[str] = None
    subscription_type_id: Optional[int] = None
    is_active: Optional[bool] = None
    subscription_start_date: Optional[datetime] = None
    subscription_end_date: Optional[datetime] = None
    # password: Optional[str] = None # Можно добавить для смены пароля

class ClientResponse(ClientBase):
    id: int
    subscription_type: Optional[SubscriptionTypeResponse] = None # Полная информация о подписке
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True