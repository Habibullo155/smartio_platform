from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class BlogCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class BlogCategoryCreate(BlogCategoryBase):
    pass

class BlogCategoryUpdate(BlogCategoryBase):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class BlogCategoryResponse(BlogCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BlogBase(BaseModel):
    title: str
    short_description: Optional[str] = None
    full_description: str
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_published: Optional[bool] = True

class BlogCreate(BlogBase):
    pass

class BlogUpdate(BlogBase):
    title: Optional[str] = None
    full_description: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None

class BlogResponse(BlogBase):
    id: int
    category: Optional[BlogCategoryResponse] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True