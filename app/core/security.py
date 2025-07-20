import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.config import settings
from app.database import get_db
from app.models.users import User # Будет создана позже
from app.models.clients import Client # Будет создана позже

# --- Хеширование паролей ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# --- JWT токены ---
oauth2_scheme_admin = OAuth2PasswordBearer(tokenUrl="admin/token") # Для админов
oauth2_scheme_client = OAuth2PasswordBearer(tokenUrl="client/token") # Для клиентов

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30) # Стандартно 30 минут
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Зависимости для получения текущего пользователя/клиента ---

# Для Админа
async def get_current_admin_user(token: str = Depends(oauth2_scheme_admin), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("sub")
        user_role: str = payload.get("role")
        if user_id is None or user_role != "admin":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.id == user_id, User.role == "admin"))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

# Для Клиента
async def get_current_client_user(token: str = Depends(oauth2_scheme_client), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        client_id: int = payload.get("sub")
        user_type: str = payload.get("type") # Добавляем тип, чтобы различать юзеров и клиентов
        if client_id is None or user_type != "client":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(Client).filter(Client.id == client_id))
    client = result.scalars().first()
    if client is None:
        raise credentials_exception
    return client