# app/database.py
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Импортируем Base из моделей SMARTIO DB для создания таблиц
from app.models.smartio_models import Base as SmartioBase

# Получаем строку подключения из переменных окружения
# Имя переменной соответствует тому, что мы указали в smartio.env
DATABASE_URL_SMARTIO = os.getenv("DATABASE_URL_SMARTIO")

# Проверяем, что строка подключения не пустая
if not DATABASE_URL_SMARTIO:
    raise ValueError("DATABASE_URL_SMARTIO environment variable is not set.")

# Создаем асинхронный движок SQLAlchemy для SMARTIO DB
# pool_pre_ping=True помогает поддерживать соединения активными и проверять их перед использованием
engine_smartio = create_async_engine(DATABASE_URL_SMARTIO, echo=True, pool_pre_ping=True)

# Создаем асинхронную фабрику сессий для SMARTIO DB
# autoflush=False отключает автоматический flush (commit) после каждого изменения
# bind=engine_smartio привязывает сессию к созданному движку
# class_=AsyncSession указывает, что это асинхронная сессия
# expire_on_commit=False предотвращает немедленную выгрузку объектов из сессии после коммита
AsyncSessionLocalSmartio = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine_smartio,
    class_=AsyncSession,
    expire_on_commit=False # Важно для работы с объектами после коммита в асинхронных функциях
)

# Функция для получения асинхронной сессии базы данных SMARTIO
# Используется как зависимость в FastAPI маршрутах
async def get_smartio_db():
    async with AsyncSessionLocalSmartio() as session:
        try:
            yield session
        finally:
            await session.close()

# Функция для создания всех таблиц в базе данных SMARTIO
async def create_smartio_db_tables():
    async with engine_smartio.begin() as conn:
        # SmartioBase.metadata.create_all(conn) - это синхронный метод, который не работает с асинхронным движком.
        # Вместо него используем run_sync, чтобы выполнить синхронный метод в асинхронном контексте.
        await conn.run_sync(SmartioBase.metadata.create_all)
    print("SMARTIO DB tables created successfully.")

# Важно: Здесь НЕ настраивается Client DB.
# Подключение к Client DB будет динамическим, на основе данных из SMARTIO DB.
# Логика для Client DB будет реализована позже, когда мы будем работать с авторизацией клиентов.
