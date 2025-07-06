# app/core/security.py
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid

# Импорт моделей и схем
from app.models.smartio_models import Client, AdminUser
from app.schemas.smartio_schemas import TokenData
from app.database import get_smartio_db

# Настройки для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Загрузка секретного ключа из переменных окружения
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set.")

# Схема OAuth2 для получения токена из заголовка Authorization
oauth2_scheme_client = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="admin/token")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверяет соответствие обычного пароля хешированному.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Генерирует хеш пароля.
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен доступа.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def _get_current_client_from_token(
        token: str,
        db: AsyncSession
) -> Optional[Client]:
    """
    Вспомогательная функция для получения клиента из токена.
    Возвращает Client или None, не вызывая исключений.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        client_db_id: str = payload.get("client_db_id")
        if username is None or client_db_id is None:
            return None  # Недостаточно данных в токене
        token_data = TokenData(username=username, client_db_id=uuid.UUID(client_db_id))
    except JWTError:
        return None  # Недействительный токен

    client = await db.execute(select(Client).where(Client.username == token_data.username))
    current_client = client.scalars().first()

    if current_client is None or not current_client.is_active:
        return None  # Клиент не найден или неактивен

    return current_client


async def get_current_client_optional(
        token: Optional[str] = Depends(oauth2_scheme_client),
        db: AsyncSession = Depends(get_smartio_db)
) -> Optional[Client]:
    """
    Зависимость, которая возвращает объект Client, если пользователь аутентифицирован,
    или None, если токена нет или он недействителен.
    Используется для HTML-страниц, где возможен редирект.
    """
    if token is None:
        return None
    return await _get_current_client_from_token(token, db)


async def get_current_client_required(
        token: str = Depends(oauth2_scheme_client),
        db: AsyncSession = Depends(get_smartio_db)
) -> Client:
    """
    Зависимость, которая возвращает объект Client, если пользователь аутентифицирован,
    или вызывает HTTPException(401) в противном случае.
    Используется для API-эндпоинтов, где требуется аутентификация.
    """
    client = await _get_current_client_from_token(token, db)
    if client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return client


async def _get_current_admin_user_from_token(
        token: str,
        db: AsyncSession
) -> Optional[AdminUser]:
    """
    Вспомогательная функция для получения администратора из токена.
    Возвращает AdminUser или None, не вызывая исключений.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None  # Недостаточно данных в токене
        token_data = TokenData(username=username)
    except JWTError:
        return None  # Недействительный токен

    admin_user = await db.execute(select(AdminUser).where(AdminUser.username == token_data.username))
    current_admin_user = admin_user.scalars().first()

    if current_admin_user is None or not current_admin_user.is_active:
        return None  # Администратор не найден или неактивен

    return current_admin_user


async def get_current_admin_user_optional(
        token: Optional[str] = Depends(oauth2_scheme_admin),
        db: AsyncSession = Depends(get_smartio_db)
) -> Optional[AdminUser]:
    """
    Зависимость, которая возвращает объект AdminUser, если администратор аутентифицирован,
    или None, если токена нет или он недействителен.
    Используется для HTML-страниц админки, где возможен редирект.
    """
    if token is None:
        return None
    return await _get_current_admin_user_from_token(token, db)


async def get_current_admin_user_required(
        token: str = Depends(oauth2_scheme_admin),
        db: AsyncSession = Depends(get_smartio_db)
) -> AdminUser:
    """
    Зависимость, которая возвращает объект AdminUser, если администратор аутентифицирован,
    или вызывает HTTPException(401) в противном случае.
    Используется для API-эндпоинтов админки, где требуется аутентификация.
    """
    admin_user = await _get_current_admin_user_from_token(token, db)
    if admin_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate admin credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return admin_user

