import uuid
from datetime import datetime, timedelta

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, Enum, JSON, UniqueConstraint # Добавлен UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

# Базовый класс для всех декларативных моделей SQLAlchemy для SMARTIO DB
Base = declarative_base()

class SubscriptionType(Base):
    """
    Модель типа подписки на платформе SMARTIO.
    """
    __tablename__ = 'subscription_types'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    # Название типа подписки (например, 'Склад', 'Склад и интернет-магазин', 'Премиум')
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    # Детальное описание подписки
    options: Mapped[list[str]] = mapped_column(JSON, default=[], nullable=False) # Опции подписки
    price: Mapped[float] = mapped_column(Float, nullable=True) # Базовая стоимость подписки (за 1 месяц)
    discount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False) # Общая скидка (если есть)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношение к клиентам
    clients: Mapped[list["Client"]] = relationship("Client", back_populates="subscription_type")
    # Отношение к платежным транзакциям
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="subscription_type")
    # Отношение к периодам подписки
    periods: Mapped[list["SubscriptionPeriod"]] = relationship("SubscriptionPeriod", back_populates="subscription_type", cascade="all, delete-orphan")


    def __repr__(self):
        return f"<SubscriptionType(id={self.id}, name='{self.name}', is_active={self.is_active})>"


class SubscriptionPeriod(Base):
    """
    Модель для определения доступных периодов подписки и их скидок
    для конкретного типа подписки.
    """
    __tablename__ = 'subscription_periods'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subscription_type_id: Mapped[int] = mapped_column(ForeignKey('subscription_types.id'), nullable=False)
    # Количество месяцев в данном периоде (например, 1, 3, 6, 12)
    months: Mapped[int] = mapped_column(Integer, nullable=False)
    # Процент скидки для данного периода (например, 0.1 для 10%)
    discount_percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношение к типу подписки
    subscription_type: Mapped["SubscriptionType"] = relationship("SubscriptionType", back_populates="periods")

    __table_args__ = (
        UniqueConstraint('subscription_type_id', 'months', name='_subscription_type_months_uc'),
    )

    def __repr__(self):
        return f"<SubscriptionPeriod(id={self.id}, sub_type_id={self.subscription_type_id}, months={self.months}, discount={self.discount_percentage})>"


class Client(Base):
    """
    Модель клиента SMARTIO (наш "smart_buyer").
    Этот клиент является "директором" своего бизнеса в Client DB.
    """
    __tablename__ = 'clients'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    company_name: Mapped[str] = mapped_column(String, nullable=False)
    # Новые поля для типа компании и ИНН
    company_type: Mapped[str] = mapped_column(Enum('ИП', 'ООО', 'Другое', name='company_type_enum'), nullable=False, default='Другое')
    inn: Mapped[str] = mapped_column(String, unique=True, nullable=True) # ИНН может быть уникальным и необязательным
    contact_email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    phone_number: Mapped[str] = mapped_column(String, nullable=True)
    client_db_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)

    subscription_type_id: Mapped[int] = mapped_column(ForeignKey('subscription_types.id'), nullable=False)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    renewal_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscription_type: Mapped["SubscriptionType"] = relationship("SubscriptionType", back_populates="clients")
    payment_transactions: Mapped[list["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="client")
    social_accounts: Mapped[list["SocialAccount"]] = relationship("SocialAccount", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Client(id={self.id}, company_name='{self.company_name}', username='{self.username}')>"


class PaymentTransaction(Base):
    """
    Модель для отслеживания платежных транзакций по подпискам.
    """
    __tablename__ = 'payment_transactions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'), nullable=False)
    subscription_type_id: Mapped[int] = mapped_column(ForeignKey('subscription_types.id'), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='USD', nullable=False)
    status: Mapped[str] = mapped_column(Enum('pending', 'completed', 'failed', 'refunded', name='payment_status_types'), default='pending', nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payment_gateway_id: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    payment_method: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship("Client", back_populates="payment_transactions")
    subscription_type: Mapped["SubscriptionType"] = relationship("SubscriptionType", back_populates="payment_transactions")

    def __repr__(self):
        return f"<PaymentTransaction(id={self.id}, client_id={self.client_id}, amount={self.amount}, status='{self.status}')>"


class AdminUser(Base):
    """
    Модель пользователя-администратора платформы SMARTIO.
    Отдельная модель для администраторов, чтобы отделить их от обычных клиентов.
    """
    __tablename__ = 'admin_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Новое отношение для блогов, созданных этим администратором
    blog_posts: Mapped[list["BlogPost"]] = relationship("BlogPost", back_populates="author")

    def __repr__(self):
        return f"<AdminUser(id={self.id}, username='{self.username}', is_superadmin={self.is_superadmin})>"


class SocialAccount(Base):
    """
    Модель для привязки социальных аккаунтов к клиентам.
    """
    __tablename__ = 'social_accounts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    social_id: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=True)
    access_token: Mapped[str] = mapped_column(String, nullable=True)
    refresh_token: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship("Client", back_populates="social_accounts")

    __table_args__ = (
        UniqueConstraint('provider', 'social_id', name='_provider_social_id_uc'),
    )

    def __repr__(self):
        return f"<SocialAccount(id={self.id}, client_id={self.client_id}, provider='{self.provider}', social_id='{self.social_id}')>"


class BlogPost(Base):
    """
    Модель для статей блога.
    """
    __tablename__ = 'blog_posts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    short_description: Mapped[str] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String, nullable=True) # URL для обложки блога
    video_url: Mapped[str] = mapped_column(String, nullable=True) # Добавлено поле video_url
    author_id: Mapped[int] = mapped_column(ForeignKey('admin_users.id'), nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author: Mapped["AdminUser"] = relationship("AdminUser", back_populates="blog_posts")

    def __repr__(self):
        return f"<BlogPost(id={self.id}, title='{self.title}', is_published={self.is_published})>"


class FuturePlan(Base):
    """
    Модель для описания будущих планов/проектов компании.
    """
    __tablename__ = 'future_plans'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_description: Mapped[str] = mapped_column(Text, nullable=True)
    image_url: Mapped[str] = mapped_column(String, nullable=True) # URL для изображения плана
    video_url: Mapped[str] = mapped_column(String, nullable=True) # URL для видео (опционально)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=True) # Целевая дата реализации
    category: Mapped[str] = mapped_column(String, nullable=True) # Добавлено поле category для фильтрации
    is_active: Mapped[bool] = mapped_column(Boolean, default=True) # Активен ли план (отображается ли на сайте)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FuturePlan(id={self.id}, title='{self.title}', is_active={self.is_active})>"

