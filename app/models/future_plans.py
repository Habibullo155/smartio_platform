from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from app.models.base import Base

class FuturePlan(Base):
    __tablename__ = "future_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    short_description = Column(String, nullable=True)
    full_description = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    target_date = Column(DateTime(timezone=True), nullable=True)
    category = Column(String, nullable=True) # Например: "AI", "Blockchain"
    tags = Column(JSON, nullable=False, default=[]) # Список тегов
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())