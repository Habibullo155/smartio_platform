from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base
from app.models.subscriptions import SubscriptionType # Для связи

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    company_type = Column(String, nullable=False) # Например: "ИП", "ООО"
    inn = Column(String, unique=True, index=True, nullable=True) # ИНН
    contact_email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=True)
    subscription_type_id = Column(Integer, ForeignKey("subscription_types.id"), nullable=True) # Опциональная подписка
    is_active = Column(Boolean, default=True)
    subscription_start_date = Column(DateTime(timezone=True), nullable=True)
    subscription_end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subscription_type = relationship("SubscriptionType", back_populates="clients")