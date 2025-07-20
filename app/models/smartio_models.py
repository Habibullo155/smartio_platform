import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base # Импортируем наш базовый класс

class AdminUser(Base):
    """
    Модель для администраторов платформы SMARTIO.
    """
    __tablename__ = "admin_users" # Имя таблицы в БД

    id = Column(Integer, primary_key=True, index=True) # Первичный ключ
    username = Column(String, unique=True, index=True, nullable=False) # Логин, должен быть уникальным
    hashed_password = Column(String, nullable=False) # Хеш пароля
    email = Column(String, unique=True, index=True, nullable=True) # Email, опционально
    full_name = Column(String, nullable=True) # Полное имя админа
    is_active = Column(Boolean, default=True) # Активен ли пользователь
    is_superuser = Column(Boolean, default=False) # Является ли суперпользователем
    created_at = Column(DateTime, default=datetime.datetime.now) # Время создания записи
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now) # Время последнего обновления

    # Отношение к Client (если админ может быть привязан к клиенту, например, в будущем)
    # clients = relationship("Client", back_populates="admin_user_creator")


class Client(Base):
    """
    Модель для клиентов платформы (тех, кто покупает подписки и имеет свою БД).
    """
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String, unique=True, index=True, nullable=False) # Название компании клиента
    contact_person = Column(String, nullable=False) # Контактное лицо
    email = Column(String, unique=True, index=True, nullable=False) # Email клиента
    phone_number = Column(String, nullable=True) # Телефон клиента
    hashed_password = Column(String, nullable=False) # Хеш пароля для входа в личный кабинет
    is_active = Column(Boolean, default=True)
    subscription_type_id = Column(Integer, ForeignKey("subscription_types.id"), nullable=False) # Тип подписки
    # Здесь мы будем хранить данные для подключения к ИХ отдельной БД
    client_db_url = Column(String, nullable=True) # Строка подключения к отдельной БД клиента
    client_db_name = Column(String, nullable=True) # Имя БД клиента
    client_db_user = Column(String, nullable=True) # Пользователь БД клиента
    client_db_password = Column(String, nullable=True) # Пароль БД клиента

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Отношение к SubscriptionType
    subscription_type = relationship("SubscriptionType", back_populates="clients")


class SubscriptionType(Base):
    """
    Модель для типов подписок (Базовая, Профессиональная, Корпоративная).
    """
    __tablename__ = "subscription_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False) # Название подписки (например, "Базовая", "Премиум")
    description = Column(Text, nullable=True) # Описание подписки
    price_usd = Column(Integer, nullable=False) # Цена в USD (можно Decimal, но пока Integer для простоты)
    features = Column(Text, nullable=True) # Описание функций, включенных в подписку (например, JSON-строка)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Отношение к Client
    clients = relationship("Client", back_populates="subscription_type")


class BlogPost(Base):
    """
    Модель для записей блога.
    """
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False) # Заголовок поста
    slug = Column(String, unique=True, index=True, nullable=False) # ЧПУ-ссылка (например, "kak-vybrat-luchshiy-planshet")
    content = Column(Text, nullable=False) # Содержание поста
    author = Column(String, nullable=True, default="SMARTIO Team") # Автор поста
    published = Column(Boolean, default=False) # Опубликован ли пост
    published_at = Column(DateTime, nullable=True) # Дата публикации
    image_url = Column(String, nullable=True) # URL изображения для поста

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class FuturePlan(Base):
    """
    Модель для будущих планов/фич платформы.
    """
    __tablename__ = "future_plans"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False) # Название плана
    description = Column(Text, nullable=False) # Подробное описание
    expected_release = Column(DateTime, nullable=True) # Ожидаемая дата релиза
    is_completed = Column(Boolean, default=False) # Выполнено ли
    priority = Column(Integer, default=0) # Приоритет (например, 0 - низкий, 1 - средний, 2 - высокий)

    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)