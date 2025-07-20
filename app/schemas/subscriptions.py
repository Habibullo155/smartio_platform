from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class SubscriptionTypeBase(BaseModel):
    name: str
    options: List[Any] = [] # List[str] или List[dict] в зависимости от использования
    price: float
    discount: float = 0.0
    is_active: bool = True

class SubscriptionTypeCreate(SubscriptionTypeBase):
    pass

class SubscriptionTypeUpdate(SubscriptionTypeBase):
    name: Optional[str] = None
    options: Optional[List[Any]] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    is_active: Optional[bool] = None

class SubscriptionTypeResponse(SubscriptionTypeBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True