# app/crud/smartio_crud.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func # Для агрегатных функций, если понадобятся

from app.models.smartio_models import SubscriptionType, AdminUser
from app.schemas.smartio_schemas import SubscriptionTypeCreate, SubscriptionTypeUpdate, AdminUserCreate, AdminUserUpdate
from app.core.security import get_password_hash, verify_password


# --- CRUD для AdminUser (пока только создание и чтение по юзернейму) ---
async def get_admin_user_by_username(db: AsyncSession, username: str):
    """Получает администратора по имени пользователя."""
    result = await db.execute(select(AdminUser).filter(AdminUser.username == username))
    return result.scalar_one_or_none()

async def create_admin_user(db: AsyncSession, admin_user: AdminUserCreate):
    """Создает нового администратора."""
    hashed_password = get_password_hash(admin_user.password)
    db_admin = AdminUser(
        username=admin_user.username,
        email=admin_user.email,
        full_name=admin_user.full_name,
        hashed_password=hashed_password,
        is_active=admin_user.is_active,
        is_superuser=admin_user.is_superuser
    )
    db.add(db_admin)
    await db.commit()
    await db.refresh(db_admin)
    return db_admin


# --- CRUD для SubscriptionType ---
async def get_subscription_type(db: AsyncSession, subscription_type_id: int):
    """Получает тип подписки по ID."""
    result = await db.execute(
        select(SubscriptionType).filter(SubscriptionType.id == subscription_type_id)
    )
    return result.scalar_one_or_none() # Возвращает один объект или None

async def get_subscription_type_by_name(db: AsyncSession, name: str):
    """Получает тип подписки по названию."""
    result = await db.execute(
        select(SubscriptionType).filter(SubscriptionType.name == name)
    )
    return result.scalar_one_or_none()

async def get_subscription_types(db: AsyncSession, skip: int = 0, limit: int = 100):
    """Получает список всех типов подписок."""
    result = await db.execute(
        select(SubscriptionType).offset(skip).limit(limit)
    )
    return result.scalars().all() # Возвращает список объектов

async def create_subscription_type(db: AsyncSession, subscription_type: SubscriptionTypeCreate):
    """Создает новый тип подписки."""
    db_subscription_type = SubscriptionType(
        name=subscription_type.name,
        description=subscription_type.description,
        price_usd=subscription_type.price_usd,
        features=subscription_type.features,
        is_active=subscription_type.is_active
    )
    db.add(db_subscription_type) # Добавляем объект в сессию
    await db.commit() # Сохраняем изменения в БД
    await db.refresh(db_subscription_type) # Обновляем объект, чтобы получить ID и другие данные
    return db_subscription_type

async def update_subscription_type(db: AsyncSession, subscription_type_id: int, subscription_type_update: SubscriptionTypeUpdate):
    """Обновляет существующий тип подписки."""
    db_subscription_type = await get_subscription_type(db, subscription_type_id)
    if not db_subscription_type:
        return None

    # Обновляем только те поля, которые переданы в update-схеме
    update_data = subscription_type_update.model_dump(exclude_unset=True) # Исключаем поля, которые не были установлены
    for key, value in update_data.items():
        setattr(db_subscription_type, key, value)

    await db.add(db_subscription_type) # Добавляем объект обратно в сессию (для отслеживания изменений)
    await db.commit()
    await db.refresh(db_subscription_type)
    return db_subscription_type

async def delete_subscription_type(db: AsyncSession, subscription_type_id: int):
    """Удаляет тип подписки по ID."""
    db_subscription_type = await get_subscription_type(db, subscription_type_id)
    if not db_subscription_type:
        return None
    await db.delete(db_subscription_type) # Удаляем объект из сессии
    await db.commit() # Сохраняем изменения
    return db_subscription_type