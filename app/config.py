import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_USER: str = os.getenv("DB_USER")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD")
    DB_HOST: str = os.getenv("DB_HOST")
    DB_PORT: str = os.getenv("DB_PORT")
    DB_NAME: str = os.getenv("DB_NAME")

    DATABASE_URL: str = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD")
    ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN", 30))
    ACCESS_TOKEN_EXPIRE_MINUTES_CLIENT: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES_CLIENT", 30))

settings = Settings()