from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import engine, get_db
from app.config import settings
from app.core.security import get_password_hash
from app.models.users import User
from app.models.base import Base# Импортируем модель User

# --- Импорты роутеров ---
from app.routers import admin
from app.routers import blog_admin
from app.routers import subscriptions_admin
from app.routers import clients_admin
from app.routers import future_plans_admin
from app.routers import client_auth # Роутер для входа клиентов
from app.routers import frontend # Роутер для публичных страниц
# --- Конец импортов роутеров ---

app = FastAPI(
    title="Мой Супер Проект",
    description="Backend для блогов, подписок, клиентов и планов",
    version="1.0.0",
)

# --- Настройка CORS Middleware ---
# В продакшене замени "*" на конкретные домены фронтенда
origins = [
    "http://localhost",
    "http://localhost:8000", # Если твой фронтенд на том же порту
    "http://localhost:3000", # Если твой фронтенд на React/Vue
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Или ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers=["*"],
)

# --- Подключение статических файлов ---
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Настройка Jinja2Templates (путь к папке templates) ---
templates = Jinja2Templates(directory="templates")

# --- Регистрация роутеров ---
app.include_router(admin.router)
app.include_router(blog_admin.router)
app.include_router(subscriptions_admin.router)
app.include_router(clients_admin.router)
app.include_router(future_plans_admin.router)
app.include_router(client_auth.router)
app.include_router(frontend.router) # Публичные страницы должны быть последними, чтобы не перехватывать другие роуты

# --- События запуска приложения ---
@app.on_event("startup")
async def startup_event():
    # Создание таблиц БД, если их нет (используй Alembic для продакшена!)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Автоматическое создание админ-пользователя при запуске
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).filter(User.email == settings.ADMIN_EMAIL))
        admin_user = result.scalars().first()
        if not admin_user:
            hashed_password = get_password_hash(settings.ADMIN_PASSWORD)
            new_admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hashed_password,
                role="admin",
                is_active=True
            )
            session.add(new_admin)
            await session.commit()
            await session.refresh(new_admin)
            print(f"Admin user '{new_admin.email}' created automatically.")
        else:
            print(f"Admin user '{admin_user.email}' already exists.")

# --- Тестовый эндпоинт для корневого пути (если нужен, или используй frontend.router) ---
# @app.get("/")
# async def root():
#     return {"message": "Welcome to the Super Project API!"}