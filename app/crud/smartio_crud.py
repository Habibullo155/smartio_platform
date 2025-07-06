# app/crud/smartio_crud.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, joinedload
import uuid
from typing import List, Optional

from app.models.smartio_models import Client, SubscriptionType, PaymentTransaction, AdminUser, SocialAccount, SubscriptionPeriod, BlogPost, FuturePlan
from app.schemas.smartio_schemas import (
    ClientCreate, ClientUpdate,
    SubscriptionTypeCreate, SubscriptionTypeUpdate,
    AdminUserCreate, AdminUserResponse,
    SocialAccountCreate,
    SubscriptionPeriodCreate, SubscriptionPeriodUpdate,
    PaymentTransactionBase,
    BlogPostCreate, BlogPostUpdate,
    FuturePlanCreate, FuturePlanUpdate
)

# --- CRUD операции для Client ---

async def get_client_by_username(db: AsyncSession, username: str) -> Optional[Client]:
    """
    Получает клиента по его имени пользователя.
    """
    result = await db.execute(select(Client).where(Client.username == username).options(selectinload(Client.subscription_type)))
    return result.scalars().first()

async def get_client_by_email(db: AsyncSession, email: str) -> Optional[Client]:
    """
    Получает клиента по его контактному email.
    """
    result = await db.execute(select(Client).where(Client.contact_email == email).options(selectinload(Client.subscription_type)))
    return result.scalars().first()

async def get_client_by_id(db: AsyncSession, client_id: int) -> Optional[Client]:
    """
    Получает клиента по его ID, включая информацию о подписке и платежах.
    """
    result = await db.execute(
        select(Client)
        .where(Client.id == client_id)
        .options(
            selectinload(Client.subscription_type),
            selectinload(Client.payment_transactions)
        )
    )
    return result.scalars().first()

async def get_all_clients(db: AsyncSession) -> List[Client]:
    """
    Получает всех клиентов, включая информацию о подписке.
    """
    result = await db.execute(select(Client).options(selectinload(Client.subscription_type)))
    return result.scalars().all()

async def create_client(db: AsyncSession, client: ClientCreate, hashed_password: str) -> Client:
    """
    Создает нового клиента в базе данных SMARTIO.
    client_db_id генерируется автоматически.
    """
    db_client = Client(
        username=client.username,
        hashed_password=hashed_password,
        company_name=client.company_name,
        company_type=client.company_type,
        inn=client.inn,
        contact_email=client.contact_email,
        phone_number=client.phone_number,
        subscription_type_id=client.subscription_type_id,
        client_db_id=uuid.uuid4()
    )
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    return db_client

async def update_client(db: AsyncSession, client: Client, client_update: ClientUpdate) -> Client:
    """
    Обновляет информацию о клиенте.
    """
    update_data = client_update.model_dump(exclude_unset=True)
    # Если пароль обновляется, хэшируем его
    if "password" in update_data and update_data["password"] is not None:
        from app.core.security import get_password_hash # Импортируем здесь, чтобы избежать циклической зависимости
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    for key, value in update_data.items():
        setattr(client, key, value)
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client

async def delete_client(db: AsyncSession, client: Client):
    """
    Удаляет клиента из базы данных SMARTIO.
    """
    await db.delete(client)
    await db.commit()

# --- CRUD операции для SubscriptionType ---

async def get_subscription_type_by_id(db: AsyncSession, sub_type_id: int) -> Optional[SubscriptionType]:
    """
    Получает тип подписки по ID, включая связанные периоды.
    """
    result = await db.execute(
        select(SubscriptionType)
        .where(SubscriptionType.id == sub_type_id)
        .options(selectinload(SubscriptionType.periods)) # Eager load periods
    )
    return result.scalars().first()

async def get_all_subscription_types(db: AsyncSession) -> List[SubscriptionType]:
    """
    Получает все доступные типы подписок, включая связанные периоды.
    """
    result = await db.execute(
        select(SubscriptionType)
        .options(selectinload(SubscriptionType.periods)) # Eager load periods
    )
    return result.scalars().all()

async def create_subscription_type(db: AsyncSession, sub_type: SubscriptionTypeCreate) -> SubscriptionType:
    """
    Создает новый тип подписки.
    """
    db_sub_type = SubscriptionType(
        name=sub_type.name,
        options=sub_type.options,
        price=sub_type.price,
        discount=sub_type.discount,
        is_active=sub_type.is_active
    )
    db.add(db_sub_type)
    await db.commit()
    await db.refresh(db_sub_type)
    return db_sub_type

async def update_subscription_type(db: AsyncSession, sub_type: SubscriptionType, sub_type_update: SubscriptionTypeUpdate) -> SubscriptionType:
    """
    Обновляет информацию о типе подписки.
    """
    update_data = sub_type_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sub_type, key, value)
    db.add(sub_type)
    await db.commit()
    await db.refresh(sub_type)
    return sub_type

async def delete_subscription_type(db: AsyncSession, sub_type: SubscriptionType):
    """
    Удаляет тип подписки.
    """
    await db.delete(sub_type)
    await db.commit()

# --- CRUD операции для SubscriptionPeriod ---

async def get_subscription_period_by_id(db: AsyncSession, period_id: int) -> Optional[SubscriptionPeriod]:
    """
    Получает период подписки по ID.
    """
    result = await db.execute(select(SubscriptionPeriod).where(SubscriptionPeriod.id == period_id))
    return result.scalars().first()

async def get_subscription_periods_for_type(db: AsyncSession, sub_type_id: int) -> List[SubscriptionPeriod]:
    """
    Получает все периоды подписки для конкретного типа подписки.
    """
    result = await db.execute(select(SubscriptionPeriod).where(SubscriptionPeriod.subscription_type_id == sub_type_id))
    return result.scalars().all()

async def create_subscription_period(db: AsyncSession, period_data: SubscriptionPeriodCreate, subscription_type_id: int) -> SubscriptionPeriod:
    """
    Создает новый период подписки для указанного типа подписки.
    """
    db_period = SubscriptionPeriod(
        subscription_type_id=subscription_type_id,
        months=period_data.months,
        discount_percentage=period_data.discount_percentage,
        is_active=period_data.is_active
    )
    db.add(db_period)
    await db.commit()
    await db.refresh(db_period)
    return db_period

async def update_subscription_period(db: AsyncSession, period: SubscriptionPeriod, period_update: SubscriptionPeriodUpdate) -> SubscriptionPeriod:
    """
    Обновляет информацию о периоде подписки.
    """
    update_data = period_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(period, key, value)
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return period

async def delete_subscription_period(db: AsyncSession, period: SubscriptionPeriod):
    """
    Удаляет период подписки.
    """
    await db.delete(period)
    await db.commit()

# --- CRUD операции для AdminUser ---

async def get_admin_user_by_username(db: AsyncSession, username: str) -> Optional[AdminUser]:
    """
    Получает администратора по имени пользователя.
    """
    result = await db.execute(select(AdminUser).where(AdminUser.username == username))
    return result.scalars().first()

async def get_admin_user_by_email(db: AsyncSession, email: str) -> Optional[AdminUser]:
    """
    Получает администратора по email.
    """
    result = await db.execute(select(AdminUser).where(AdminUser.email == email))
    return result.scalars().first()

async def get_admin_user_by_id(db: AsyncSession, admin_id: int) -> Optional[AdminUser]:
    """
    Получает администратора по ID.
    """
    result = await db.execute(select(AdminUser).where(AdminUser.id == admin_id))
    return result.scalars().first()

async def create_admin_user(db: AsyncSession, admin_user: AdminUserCreate, hashed_password: str) -> AdminUser:
    """
    Создает нового администратора.
    """
    db_admin_user = AdminUser(
        username=admin_user.username,
        hashed_password=hashed_password,
        email=admin_user.email,
        is_superadmin=admin_user.is_superadmin
    )
    db.add(db_admin_user)
    await db.commit()
    await db.refresh(db_admin_user)
    return db_admin_user

# --- CRUD операции для PaymentTransaction ---
async def create_payment_transaction(db: AsyncSession, transaction_data: PaymentTransactionBase) -> PaymentTransaction:
    """
    Создает новую платежную транзакцию.
    """
    db_transaction = PaymentTransaction(**transaction_data.model_dump())
    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)
    return db_transaction

async def get_payment_transaction_by_id(db: AsyncSession, transaction_id: int) -> Optional[PaymentTransaction]:
    """
    Получает платежную транзакцию по ID.
    """
    result = await db.execute(select(PaymentTransaction).where(PaymentTransaction.id == transaction_id))
    return result.scalars().first()

async def get_payment_transactions_for_client(db: AsyncSession, client_id: int) -> List[PaymentTransaction]:
    """
    Получает все платежные транзакции для конкретного клиента.
    """
    result = await db.execute(
        select(PaymentTransaction)
        .where(PaymentTransaction.client_id == client_id)
        .options(selectinload(PaymentTransaction.subscription_type)) # Загружаем тип подписки
    )
    return result.scalars().all()

# --- CRUD операции для SocialAccount ---

async def get_social_account(db: AsyncSession, provider: str, social_id: str) -> Optional[SocialAccount]:
    """
    Получает социальный аккаунт по провайдеру и социальному ID.
    """
    result = await db.execute(
        select(SocialAccount)
        .where(SocialAccount.provider == provider, SocialAccount.social_id == social_id)
    )
    return result.scalars().first()

async def create_social_account(db: AsyncSession, social_account: SocialAccountCreate, client_id: int) -> SocialAccount:
    """
    Создает новый социальный аккаунт и привязывает его к клиенту.
    """
    db_social_account = SocialAccount(
        client_id=client_id,
        provider=social_account.provider,
        social_id=social_account.social_id,
        email=social_account.email
    )
    db.add(db_social_account)
    await db.commit()
    await db.refresh(db_social_account)
    return db_social_account

# --- CRUD операции для BlogPost ---

async def get_blog_post_by_id(db: AsyncSession, post_id: int) -> Optional[BlogPost]:
    """
    Получает статью блога по ID, включая информацию об авторе.
    """
    result = await db.execute(
        select(BlogPost)
        .where(BlogPost.id == post_id)
        .options(selectinload(BlogPost.author))
    )
    return result.scalars().first()

async def get_all_blog_posts(db: AsyncSession, is_published: Optional[bool] = None) -> List[BlogPost]:
    """
    Получает все статьи блога. Можно фильтровать по статусу публикации.
    """
    query = select(BlogPost).options(selectinload(BlogPost.author))
    if is_published is not None:
        query = query.where(BlogPost.is_published == is_published)
    result = await db.execute(query)
    return result.scalars().all()

async def create_blog_post(db: AsyncSession, post_data: BlogPostCreate, author_id: int) -> BlogPost:
    """
    Создает новую статью блога.
    """
    db_blog_post = BlogPost(
        title=post_data.title,
        short_description=post_data.short_description,
        content=post_data.content,
        image_url=post_data.image_url,
        video_url=post_data.video_url, # Добавлено video_url
        author_id=author_id,
        is_published=post_data.is_published
    )
    db.add(db_blog_post)
    await db.commit()
    await db.refresh(db_blog_post)
    return db_blog_post

async def update_blog_post(db: AsyncSession, blog_post: BlogPost, post_update: BlogPostUpdate) -> BlogPost:
    """
    Обновляет информацию о статье блога.
    """
    update_data = post_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(blog_post, key, value)
    db.add(blog_post)
    await db.commit()
    await db.refresh(blog_post)
    return blog_post

async def delete_blog_post(db: AsyncSession, blog_post: BlogPost):
    """
    Удаляет статью блога.
    """
    await db.delete(blog_post)
    await db.commit()

# --- CRUD операции для FuturePlan ---

async def get_future_plan_by_id(db: AsyncSession, plan_id: int) -> Optional[FuturePlan]:
    """
    Получает план по ID.
    """
    result = await db.execute(select(FuturePlan).where(FuturePlan.id == plan_id))
    return result.scalars().first()

async def get_all_future_plans(db: AsyncSession, is_active: Optional[bool] = None, category: Optional[str] = None) -> List[FuturePlan]:
    """
    Получает все будущие планы. Можно фильтровать по статусу активности и категории.
    """
    query = select(FuturePlan)
    if is_active is not None:
        query = query.where(FuturePlan.is_active == is_active)
    if category:
        query = query.where(FuturePlan.category == category) # Добавлена фильтрация по категории
    result = await db.execute(query)
    return result.scalars().all()

async def create_future_plan(db: AsyncSession, plan_data: FuturePlanCreate) -> FuturePlan:
    """
    Создает новый будущий план.
    """
    db_future_plan = FuturePlan(
        title=plan_data.title,
        short_description=plan_data.short_description,
        full_description=plan_data.full_description,
        image_url=plan_data.image_url,
        video_url=plan_data.video_url,
        target_date=plan_data.target_date,
        category=plan_data.category, # Добавлено category
        is_active=plan_data.is_active
    )
    db.add(db_future_plan)
    await db.commit()
    await db.refresh(db_future_plan)
    return db_future_plan

async def update_future_plan(db: AsyncSession, future_plan: FuturePlan, plan_update: FuturePlanUpdate) -> FuturePlan:
    """
    Обновляет информацию о будущем плане.
    """
    update_data = plan_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(future_plan, key, value)
    db.add(future_plan)
    await db.commit()
    await db.refresh(future_plan)
    return future_plan

async def delete_future_plan(db: AsyncSession, future_plan: FuturePlan):
    """
    Удаляет будущий план.
    """
    await db.delete(future_plan)
    await db.commit()

