from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

class FuturePlanBase(BaseModel):
    title: str
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    target_date: Optional[datetime] = None
    category: Optional[str] = None
    tags: List[Any] = [] # List[str]
    is_active: Optional[bool] = True

class FuturePlanCreate(FuturePlanBase):
    pass

class FuturePlanUpdate(FuturePlanBase):
    title: Optional[str] = None
    short_description: Optional[str] = None
    full_description: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    target_date: Optional[datetime] = None
    category: Optional[str] = None
    tags: Optional[List[Any]] = None
    is_active: Optional[bool] = None

class FuturePlanResponse(FuturePlanBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True