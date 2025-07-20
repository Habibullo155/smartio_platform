import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, Base, AsyncSessionLocal
from app.models.smartio_models import AdminUser
from app.core.security import get_password_hash # Мы добавим эту функцию позже в security.py
import os
from dotenv import load_dotenv

# Загружаем переменные окружения, чтобы скрипт мог подключиться к БД
load_dotenv(os.path.join(os.path.dirname(__file__), 'smartio.env'))

async def init_db():
    """
    Создает все таблицы в базе данных, если их нет.
    ОСТОРОЖНО: Это удалит и пересоздаст таблицы, если они существуют,
    если не использовать Alembic. Для первого запуска ок, но не для продакшена.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Все таблицы созданы или обновлены.")

async def create_initial_admin_user():
    """
    Создает первого администратора по умолчанию.
    """
    db: AsyncSession = AsyncSessionLocal()
    try:
        # Проверяем, существует ли уже админ с таким именем пользователя
        existing_admin = await db.get(AdminUser, 1) # Попробуем получить первого админа по ID
        if existing_admin and existing_admin.username == "admin":
            print("Администратор 'admin' уже существует.")
            return

        # Если админа нет, создаем его
        # ВАЖНО: Замени "secure_admin_password" на сильный пароль
        hashed_password = get_password_hash("secure_admin_password") # Эта функция еще не реализована, но мы скоро ее сделаем

        admin = AdminUser(
            username="admin",
            hashed_password=hashed_password,
            email="admin@smartio.com",
            full_name="Главный Администратор",
            is_active=True,
            is_superuser=True
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin) # Обновляем объект, чтобы получить id
        print(f"Администратор '{admin.username}' создан успешно с ID: {admin.id}.")
    except Exception as e:
        await db.rollback()
        print(f"Ошибка при создании администратора: {e}")
    finally:
        await db.close()

async def main():
    await init_db()
    await create_initial_admin_user()

if __name__ == "__main__":
    asyncio.run(main())