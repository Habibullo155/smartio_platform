# create_admin.py
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# Загружаем переменные окружения из файла .env
load_dotenv()

# Импортируем необходимые функции и модели
from app.database import AsyncSessionLocalSmartio, create_smartio_db_tables, \
    engine_smartio  # Импортируем engine_smartio
from app.crud.smartio_crud import create_admin_user, get_admin_user_by_username
from app.schemas.smartio_schemas import AdminUserCreate
from app.core.security import get_password_hash


async def initialize_and_create_admin():
    """
    Создает таблицы БД и первого администратора, если его еще нет,
    в рамках одного асинхронного контекста.
    """
    print("Инициализация базы данных и создание первого администратора...")

    # 1. Создаем таблицы БД
    # Используем engine_smartio.begin() для создания таблиц,
    # чтобы убедиться, что это происходит в рамках активного соединения.
    async with engine_smartio.begin() as conn:
        await conn.run_sync(SmartioBase.metadata.create_all)  # Используем SmartioBase из database.py
    print("Таблицы SMARTIO DB созданы или уже существуют.")

    # 2. Создаем первого администратора
    admin_username = os.getenv("ADMIN_USERNAME", "admin")
    admin_password = os.getenv("ADMIN_PASSWORD", "adminpass")  # Используйте надежный пароль в .env!
    admin_email = os.getenv("ADMIN_EMAIL", "admin@smartio.com")

    async with AsyncSessionLocalSmartio() as db:
        existing_admin = await get_admin_user_by_username(db, admin_username)
        if existing_admin:
            print(f"Администратор с именем '{admin_username}' уже существует.")
            return

        print(f"Создание первого администратора: {admin_username}...")
        hashed_password = get_password_hash(admin_password)
        admin_data = AdminUserCreate(
            username=admin_username,
            password=admin_password,  # Пароль будет захэширован в create_admin_user
            email=admin_email,
            is_superadmin=True  # Первый админ будет суперадмином
        )
        new_admin = await create_admin_user(db, admin_data, hashed_password)
        print(f"Администратор '{new_admin.username}' успешно создан с ID: {new_admin.id}")


if __name__ == "__main__":
    # Импортируем SmartioBase здесь, чтобы избежать циклического импорта
    # если database.py импортирует модели, а модели импортируют Base.
    # Это временное решение, лучше вынести Base в отдельный файл.
    from app.models.smartio_models import Base as SmartioBase

    asyncio.run(initialize_and_create_admin())
    print("Скрипт create_admin.py завершен.")

