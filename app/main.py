# app/main.py
import os
from typing import Annotated, List, Optional
from datetime import datetime, timedelta
import uuid  # Импортируем uuid
import aiofiles  # Для асинхронной работы с файлами

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

# Импорт из собственных модулей
from app.database import get_smartio_db, create_smartio_db_tables
from app.crud import smartio_crud  # Используем импорт модуля, чтобы обращаться через smartio_crud.
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings  # Используем settings для конфигурации

# ИМПОРТИРУЕМ ЗАВИСИМОСТИ АУТЕНТИФИКАЦИИ ИЗ SECURITY.PY
from app.core.security import (
    get_current_client_required,
    get_current_admin_user_required
)

# Импортируем все необходимые схемы из отдельного файла
from app.schemas.smartio_schemas import (
    Token, TokenData, AdminUserCreate, AdminUserResponse, AdminLogin,
    ClientCreate, ClientResponse, ClientUpdate, ClientLogin,
    SubscriptionTypeCreate, SubscriptionTypeUpdate, SubscriptionTypeResponse,
    BlogPostCreate, BlogPostUpdate, BlogPostResponse,
    FuturePlanCreate, FuturePlanUpdate, FuturePlanResponse
)
# Импортируем модели для типизации в зависимостях
from app.models.smartio_models import Client, AdminUser

# Инициализация FastAPI приложения
app = FastAPI()

# Директория для загружаемых файлов
UPLOAD_DIRECTORY = "app/assets/uploads"

# Монтирование статических файлов (CSS, JS, Images)
app.mount("/static", StaticFiles(directory="app/assets"), name="static")
# Монтирование директории для загруженных файлов
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIRECTORY), name="uploads")

# Инициализация Jinja2Templates для рендеринга HTML-страниц
templates = Jinja2Templates(directory="app/templates")

# OAuth2PasswordBearer для получения токена из заголовка Authorization
# Эта переменная используется только в /token эндпоинтах для форм логина
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# --- Вспомогательные функции для загрузки файлов ---

async def save_upload_file(upload_file: UploadFile, subdirectory: str = "") -> str:
    """
    Сохраняет загруженный файл на диск и возвращает его относительный URL-путь.
    """
    # Создаем поддиректорию, если она указана и не существует
    full_upload_path = os.path.join(UPLOAD_DIRECTORY, subdirectory)
    os.makedirs(full_upload_path, exist_ok=True)

    # Генерируем уникальное имя файла
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{file_extension}"
    file_path = os.path.join(full_upload_path, unique_filename)

    # Асинхронно записываем файл
    async with aiofiles.open(file_path, "wb") as buffer:
        while content := await upload_file.read(1024):
            await buffer.write(content)

    # Возвращаем URL-путь, который будет использоваться в базе данных и фронтенде
    # Например, "/uploads/blogs/your_unique_file.jpg"
    return f"/uploads/{subdirectory}/{unique_filename}"


# --- Запуск приложения и создание таблиц БД ---

@app.on_event("startup")
async def on_startup():
    """
    Функция, выполняющаяся при запуске приложения.
    Создает таблицы в базе данных SMARTIO, если они еще не существуют.
    Создает директорию для загружаемых файлов.
    """
    print("Запуск приложения FastAPI...")
    await create_smartio_db_tables()
    print("Таблицы SMARTIO DB проверены/созданы.")

    # Создаем директорию для загружаемых файлов, если она не существует
    os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)
    print(f"Директория для загрузок '{UPLOAD_DIRECTORY}' проверена/создана.")

    # Здесь можно добавить создание начальных данных, если их нет
    async with get_smartio_db() as db:
        sub_types = await smartio_crud.get_all_subscription_types(db)
        if not sub_types:
            print("Создание начальных типов подписок...")
            await smartio_crud.create_subscription_type(db, SubscriptionTypeCreate(name="Базовая",
                                                                                   options=["До 100 товаров",
                                                                                            "Базовый складской учет"],
                                                                                   price=19.99))
            await smartio_crud.create_subscription_type(db, SubscriptionTypeCreate(name="Стандарт",
                                                                                   options=["До 1000 товаров",
                                                                                            "Расширенный склад",
                                                                                            "Интернет-магазин"],
                                                                                   price=49.99))
            await smartio_crud.create_subscription_type(db, SubscriptionTypeCreate(name="Премиум",
                                                                                   options=["Безлимитно товаров",
                                                                                            "Все функции",
                                                                                            "Интеграция с маркетплейсами"],
                                                                                   price=99.99))
            print("Начальные типы подписок созданы.")


# --- Функции аутентификации для логина (не дублируют security.py) ---
# Эти функции используются для проверки логина/пароля, а не для валидации токена.

async def authenticate_admin_user(db: AsyncSession, username: str, password: str) -> Optional[AdminUser]:
    """
    Аутентифицирует администратора по имени пользователя и паролю.
    Возвращает объект модели AdminUser.
    """
    admin_user = await smartio_crud.get_admin_user_by_username(db, username=username)
    if not admin_user or not verify_password(password, admin_user.hashed_password):
        return None
    return admin_user


async def authenticate_client_user(db: AsyncSession, username: str, password: str) -> Optional[Client]:
    """
    Аутентифицирует клиента по имени пользователя и паролю.
    Возвращает объект модели Client.
    """
    client_user = await smartio_crud.get_client_by_username(db, username=username)
    if not client_user or not verify_password(password, client_user.hashed_password):
        return None
    return client_user


# --- Маршруты для HTML-страниц ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит главную страницу (landing page) с типами подписок, блогами и будущими планами.
    """
    subscription_types = await smartio_crud.get_all_subscription_types(db)
    active_subscription_types = [st for st in subscription_types if st.is_active]

    # Получаем блоги и будущие планы напрямую для рендеринга Jinja2
    blog_posts = await smartio_crud.get_all_blog_posts(db, is_published=True)
    future_plans = await smartio_crud.get_all_future_plans(db, is_active=True)

    # Добавляем Jinja2 фильтр для форматирования цен
    templates.env.filters['format_price_display'] = lambda value: f"{value:.2f}"
    return templates.TemplateResponse(
        "smartio_platform_landing.html",
        {
            "request": request,
            "title": "SMARTIO - Главная",
            "subscription_types": active_subscription_types,
            "blog_posts": blog_posts,  # Передаем блоги
            "future_plans": future_plans  # Передаем будущие планы
        }
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Рендерит страницу входа для клиентов.
    """
    return templates.TemplateResponse("login.html", {"request": request, "title": "Вход в SMARTIO"})


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит страницу регистрации для клиентов, передавая доступные типы подписок.
    """
    subscription_types = await smartio_crud.get_all_subscription_types(db)
    templates.env.filters['format_price_display'] = lambda value: f"{value:.2f}"
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "title": "Регистрация в SMARTIO", "subscription_types": subscription_types}
    )


@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """
    Рендерит страницу восстановления пароля.
    """
    return templates.TemplateResponse("forgot_password.html", {"request": request, "title": "Забыли пароль?"})


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """
    Рендерит страницу дашборда для клиентов.
    Эта страница будет загружаться без прямой аутентификации на сервере,
    а данные пользователя будут загружаться AJAX-запросом.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "Панель Управления SMARTIO"})


@app.get("/admin", response_class=HTMLResponse)
async def admin_page(request: Request):
    """
    Рендерит страницу админ-панели.
    Эта страница загружается без прямой аутентификации на сервере.
    Аутентификация и загрузка данных админа происходит через AJAX на клиенте.
    """
    return templates.TemplateResponse("admin.html", {"request": request, "title": "Админ-Панель SMARTIO"})


@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    """
    Рендерит страницу входа для администраторов.
    """
    return templates.TemplateResponse("admin_login.html", {"request": request, "title": "Вход для Администраторов"})


@app.get("/blogs", response_class=HTMLResponse)
async def blogs_page(request: Request, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит страницу со всеми опубликованными статьями блога.
    """
    blog_posts = await smartio_crud.get_all_blog_posts(db, is_published=True)
    return templates.TemplateResponse("blogs.html",
                                      {"request": request, "title": "Блог SMARTIO", "blog_posts": blog_posts})


@app.get("/blogs/{post_id}", response_class=HTMLResponse)
async def blog_post_detail_page(request: Request, post_id: int, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит страницу с детальной информацией о статье блога.
    """
    blog_post = await smartio_crud.get_blog_post_by_id(db, post_id)
    if not blog_post or not blog_post.is_published:
        raise HTTPException(status_code=404, detail="Blog post not found or not published")
    # Также получаем несколько последних блогов для сайдбара
    recent_blog_posts = await smartio_crud.get_all_blog_posts(db, is_published=True, limit=5)  # Ограничиваем до 5
    return templates.TemplateResponse("blog_detail.html",
                                      {"request": request, "title": blog_post.title, "post": blog_post,
                                       "blog_posts": recent_blog_posts})


@app.get("/future-plans", response_class=HTMLResponse)
async def future_plans_page(request: Request, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит страницу со всеми активными будущими планами.
    """
    future_plans = await smartio_crud.get_all_future_plans(db, is_active=True)
    return templates.TemplateResponse("future_plans.html", {"request": request, "title": "Будущие Планы SMARTIO",
                                                            "future_plans": future_plans})


@app.get("/future-plans/{plan_id}", response_class=HTMLResponse)
async def future_plan_detail_page(request: Request, plan_id: int, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Рендерит страницу с детальной информацией о будущем плане.
    """
    future_plan = await smartio_crud.get_future_plan_by_id(db, plan_id)
    if not future_plan or not future_plan.is_active:
        raise HTTPException(status_code=404, detail="Future plan not found or not active")
    # Также получаем несколько последних планов для сайдбара
    recent_future_plans = await smartio_crud.get_all_future_plans(db, is_active=True, limit=5)  # Ограничиваем до 5
    return templates.TemplateResponse("future_plan_detail.html",
                                      {"request": request, "title": future_plan.title, "plan": future_plan,
                                       "future_plans": recent_future_plans})


# --- API маршруты для аутентификации ---

@app.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_smartio_db)]
):
    """
    Эндпоинт для входа клиента и получения JWT-токена.
    """
    client_user = await authenticate_client_user(db, form_data.username, form_data.password)
    if not client_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": client_user.username, "is_admin": False},  # Указываем, что это не админ
        expires_delta=access_token_expires
    )

    # Возвращаем токен в теле ответа
    return Token(
        access_token=access_token,
        token_type="bearer",
        client_id=client_user.id,
        client_username=client_user.username,
        client_company_name=client_user.company_name,
        client_db_id=str(client_user.client_db_id)
    )


@app.post("/admin/token", response_model=Token)
async def admin_login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        db: Annotated[AsyncSession, Depends(get_smartio_db)]
):
    """
    Эндпоинт для входа администратора и получения JWT-токена.
    """
    admin_user = await authenticate_admin_user(db, form_data.username, form_data.password)
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": admin_user.username, "is_admin": True},  # Указываем, что это админ
        expires_delta=access_token_expires
    )

    # Возвращаем токен в теле ответа
    return Token(
        access_token=access_token,
        token_type="bearer",
        client_id=admin_user.id,  # Используем id админа
        client_username=admin_user.username,
        client_company_name="SMARTIO Admin",  # Для админа можно указать фиксированное значение
        client_db_id=str(uuid.UUID('00000000-0000-0000-0000-000000000000'))  # Заглушка UUID для админа
    )


@app.post("/register", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def register_client(client_data: ClientCreate, db: Annotated[AsyncSession, Depends(get_smartio_db)]):
    """
    Регистрация нового клиента.
    """
    existing_client_username = await smartio_crud.get_client_by_username(db, client_data.username)
    if existing_client_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя уже зарегистрировано")

    existing_client_email = await smartio_crud.get_client_by_email(db, client_data.contact_email)
    if existing_client_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже зарегистрирован")

    # Проверка на существование subscription_type_id
    subscription_type = await smartio_crud.get_subscription_type_by_id(db, client_data.subscription_type_id)
    if not subscription_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный ID типа подписки")

    hashed_password = get_password_hash(client_data.password)
    db_client = await smartio_crud.create_client(db, client_data, hashed_password)
    return ClientResponse.model_validate(db_client)


# --- API маршруты для клиентов ---

@app.get("/api/client/me", response_model=ClientResponse)
async def read_client_me(current_client: Annotated[Client, Depends(get_current_client_required)]):
    """
    Получение данных текущего аутентифицированного клиента.
    """
    return ClientResponse.model_validate(current_client)


# --- API маршруты для администраторов ---

@app.get("/api/admin/me", response_model=AdminUserResponse)
async def read_admin_me(current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]):
    """
    Получение данных текущего аутентифицированного администратора.
    """
    return AdminUserResponse.model_validate(current_admin)


@app.post("/api/admin/admin_users/", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_admin_user(
        admin_user_data: AdminUserCreate,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
        # Только существующий админ может регистрировать новых
):
    """
    Создание нового пользователя-администратора (только для суперадминов).
    """
    if not current_admin.is_superadmin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Только суперадмины могут регистрировать новых администраторов")

    existing_admin_username = await smartio_crud.get_admin_user_by_username(db, username=admin_user_data.username)
    if existing_admin_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Имя пользователя администратора уже зарегистрировано")

    existing_admin_email = await smartio_crud.get_admin_user_by_email(db, email=admin_user_data.email)
    if existing_admin_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email администратора уже зарегистрирован")

    hashed_password = get_password_hash(admin_user_data.password)
    db_admin_user = await smartio_crud.create_admin_user(db, admin_user_data, hashed_password)
    return AdminUserResponse.model_validate(db_admin_user)


@app.post("/api/admin/clients/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client_by_admin(
        client_data: ClientCreate,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Создание нового клиента администратором.
    """
    # Проверка на существование имени пользователя или email
    existing_client_username = await smartio_crud.get_client_by_username(db, client_data.username)
    if existing_client_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Имя пользователя клиента уже зарегистрировано")

    existing_client_email = await smartio_crud.get_client_by_email(db, client_data.contact_email)
    if existing_client_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email клиента уже зарегистрирован")

    # Проверка на существование subscription_type_id
    subscription_type = await smartio_crud.get_subscription_type_by_id(db, client_data.subscription_type_id)
    if not subscription_type:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Неверный ID типа подписки")

    hashed_password = get_password_hash(client_data.password)
    db_client = await smartio_crud.create_client(db, client_data, hashed_password)
    return ClientResponse.model_validate(db_client)


# --- API для SubscriptionType (Админ) ---

@app.get("/api/admin/subscription_types/", response_model=List[SubscriptionTypeResponse])
async def get_all_subscription_types_api(
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение всех типов подписок (для администраторов).
    """
    sub_types = await smartio_crud.get_all_subscription_types(db)
    return [SubscriptionTypeResponse.model_validate(st) for st in sub_types]


@app.get("/api/admin/subscription_types/{sub_type_id}", response_model=SubscriptionTypeResponse)
async def get_subscription_type_by_id_api(
        sub_type_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение типа подписки по ID (для администраторов).
    """
    sub_type = await smartio_crud.get_subscription_type_by_id(db, sub_type_id)
    if not sub_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип подписки не найден")
    return SubscriptionTypeResponse.model_validate(sub_type)


@app.post("/api/admin/subscription_types/", response_model=SubscriptionTypeResponse,
          status_code=status.HTTP_201_CREATED)
async def create_new_subscription_type_api(
        sub_type_data: SubscriptionTypeCreate,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Создание нового типа подписки (для администраторов).
    """
    db_sub_type = await smartio_crud.create_subscription_type(db, sub_type_data)
    return SubscriptionTypeResponse.model_validate(db_sub_type)


@app.put("/api/admin/subscription_types/{sub_type_id}", response_model=SubscriptionTypeResponse)
async def update_existing_subscription_type_api(
        sub_type_id: int,
        sub_type_update: SubscriptionTypeUpdate,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Обновление существующего типа подписки (для администраторов).
    """
    db_sub_type = await smartio_crud.get_subscription_type_by_id(db, sub_type_id)
    if not db_sub_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип подписки не найден")

    updated_sub_type = await smartio_crud.update_subscription_type(db, db_sub_type, sub_type_update)
    return SubscriptionTypeResponse.model_validate(updated_sub_type)


@app.delete("/api/admin/subscription_types/{sub_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_subscription_type_api(
        sub_type_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Удаление типа подписки (для администраторов).
    """
    db_sub_type = await smartio_crud.get_subscription_type_by_id(db, sub_type_id)
    if not db_sub_type:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип подписки не найден")
    await smartio_crud.delete_subscription_type(db, db_sub_type)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- API для Clients (Админ) ---

@app.get("/api/admin/clients/", response_model=List[ClientResponse])
async def get_all_clients_api(
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение всех клиентов (для администраторов).
    """
    clients = await smartio_crud.get_all_clients(db)
    return [ClientResponse.model_validate(client) for client in clients]


@app.get("/api/admin/clients/{client_id}", response_model=ClientResponse)
async def get_client_by_id_api(
        client_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение клиента по ID (для администраторов).
    """
    client = await smartio_crud.get_client_by_id(db, client_id)
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
    return ClientResponse.model_validate(client)


@app.put("/api/admin/clients/{client_id}", response_model=ClientResponse)
async def update_existing_client_api(
        client_id: int,
        client_update: ClientUpdate,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Обновление данных существующего клиента (для администраторов).
    """
    db_client = await smartio_crud.get_client_by_id(db, client_id)
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")

    updated_client = await smartio_crud.update_client(db, db_client, client_update)
    return ClientResponse.model_validate(updated_client)


@app.delete("/api/admin/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_client_api(
        client_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Удаление клиента (для администраторов).
    """
    db_client = await smartio_crud.get_client_by_id(db, client_id)
    if not db_client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Клиент не найден")
    await smartio_crud.delete_client(db, db_client)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- API для Blog Posts (Админ) ---

@app.post("/api/admin/blogs/", response_model=BlogPostResponse, status_code=status.HTTP_201_CREATED)
async def create_new_blog_post_api(
        title: str = Form(...),
        content: str = Form(...),
        short_description: Optional[str] = Form(None),
        image_file: Optional[UploadFile] = File(None),  # Для загрузки файла изображения
        video_file: Optional[UploadFile] = File(None),  # Для загрузки файла видео
        tags: str = Form(""),  # Теги как строка, разделенная запятыми
        is_published: bool = Form(False),
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Создание новой статьи блога (для администраторов) с возможностью загрузки файлов.
    """
    image_url = None
    if image_file and image_file.filename:
        image_url = await save_upload_file(image_file, "blogs")

    video_url = None
    if video_file and video_file.filename:
        video_url = await save_upload_file(video_file, "blogs")

    # Преобразуем строку тегов в список
    parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

    blog_post_data = BlogPostCreate(
        title=title,
        short_description=short_description,
        content=content,
        image_url=image_url,
        video_url=video_url,
        tags=parsed_tags,
        is_published=is_published
    )
    db_post = await smartio_crud.create_blog_post(db, blog_post_data, current_admin.id)
    return BlogPostResponse.model_validate(db_post)


@app.get("/api/admin/blogs/", response_model=List[BlogPostResponse])
async def get_all_blog_posts_api(
        is_published: Optional[bool] = None,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение всех статей блога (для администраторов).
    Можно фильтровать по статусу публикации.
    """
    posts = await smartio_crud.get_all_blog_posts(db, is_published=is_published)
    return [BlogPostResponse.model_validate(post) for post in posts]


@app.get("/api/admin/blogs/{post_id}", response_model=BlogPostResponse)
async def get_blog_post_by_id_api(
        post_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение статьи блога по ID (для администраторов).
    """
    post = await smartio_crud.get_blog_post_by_id(db, post_id)
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья блога не найдена")
    return BlogPostResponse.model_validate(post)


@app.put("/api/admin/blogs/{post_id}", response_model=BlogPostResponse)
async def update_existing_blog_post_api(
        post_id: int,
        title: Optional[str] = Form(None),
        content: Optional[str] = Form(None),
        short_description: Optional[str] = Form(None),
        image_file: Optional[UploadFile] = File(None),
        video_file: Optional[UploadFile] = File(None),
        tags: Optional[str] = Form(None),
        is_published: Optional[bool] = Form(None),
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Обновление существующей статьи блога (для администраторов) с возможностью загрузки файлов.
    """
    db_post = await smartio_crud.get_blog_post_by_id(db, post_id)
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья блога не найдена")

    update_data = {}
    if title is not None: update_data["title"] = title
    if content is not None: update_data["content"] = content
    if short_description is not None: update_data["short_description"] = short_description
    if is_published is not None: update_data["is_published"] = is_published

    if tags is not None:
        update_data["tags"] = [tag.strip() for tag in tags.split(',') if tag.strip()]

    if image_file and image_file.filename:
        update_data["image_url"] = await save_upload_file(image_file, "blogs")
    elif image_file is not None and not image_file.filename:  # Если поле файла пустое, но было отправлено (для очистки)
        update_data["image_url"] = None  # Очищаем URL, если файл не выбран

    if video_file and video_file.filename:
        update_data["video_url"] = await save_upload_file(video_file, "blogs")
    elif video_file is not None and not video_file.filename:  # Если поле файла пустое, но было отправлено (для очистки)
        update_data["video_url"] = None  # Очищаем URL, если файл не выбран

    # Создаем объект BlogPostUpdate из собранных данных
    post_update_schema = BlogPostUpdate(**update_data)

    updated_post = await smartio_crud.update_blog_post(db, db_post, post_update_schema)
    return BlogPostResponse.model_validate(updated_post)


@app.delete("/api/admin/blogs/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_blog_post_api(
        post_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Удаление статьи блога (для администраторов).
    """
    db_post = await smartio_crud.get_blog_post_by_id(db, post_id)
    if not db_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Статья блога не найдена")
    await smartio_crud.delete_blog_post(db, db_post)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- API для Future Plans (Админ) ---

@app.post("/api/admin/future_plans/", response_model=FuturePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_new_future_plan_api(
        title: str = Form(...),
        description: Optional[str] = Form(None),  # Описание теперь может быть Form
        category: Optional[str] = Form(None),
        is_active: bool = Form(True),
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Создание нового будущего плана (для администраторов).
    """
    plan_data = FuturePlanCreate(
        title=title,
        description=description,
        category=category,
        is_active=is_active
    )
    db_plan = await smartio_crud.create_future_plan(db, plan_data)
    return FuturePlanResponse.model_validate(db_plan)


@app.get("/api/admin/future_plans/", response_model=List[FuturePlanResponse])
async def get_all_future_plans_api(
        is_active: Optional[bool] = None,
        limit: Optional[int] = None,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение всех будущих планов (для администраторов).
    Можно фильтровать по активности и ограничивать количество.
    """
    plans = await smartio_crud.get_all_future_plans(db, is_active=is_active, limit=limit)
    return [FuturePlanResponse.model_validate(plan) for plan in plans]


@app.get("/api/admin/future_plans/{plan_id}", response_model=FuturePlanResponse)
async def get_future_plan_by_id_api(
        plan_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Получение будущего плана по ID (для администраторов).
    """
    plan = await smartio_crud.get_future_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Будущий план не найден")
    return FuturePlanResponse.model_validate(plan)


@app.put("/api/admin/future_plans/{plan_id}", response_model=FuturePlanResponse)
async def update_existing_future_plan_api(
        plan_id: int,
        title: Optional[str] = Form(None),
        description: Optional[str] = Form(None),  # Описание теперь может быть Form
        category: Optional[str] = Form(None),
        is_active: Optional[bool] = Form(None),
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Обновление существующего будущего плана (для администраторов).
    """
    db_plan = await smartio_crud.get_future_plan_by_id(db, plan_id)
    if not db_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Будущий план не найден")

    update_data = {}
    if title is not None: update_data["title"] = title
    if description is not None: update_data["description"] = description
    if category is not None: update_data["category"] = category
    if is_active is not None: update_data["is_active"] = is_active

    plan_update_schema = FuturePlanUpdate(**update_data)

    updated_plan = await smartio_crud.update_future_plan(db, db_plan, plan_update_schema)
    return FuturePlanResponse.model_validate(updated_plan)


@app.delete("/api/admin/future_plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_future_plan_api(
        plan_id: int,
        db: Annotated[AsyncSession, Depends(get_smartio_db)],
        current_admin: Annotated[AdminUser, Depends(get_current_admin_user_required)]
):
    """
    Удаление будущего плана (для администраторов).
    """
    db_plan = await smartio_crud.get_future_plan_by_id(db, plan_id)
    if not db_plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Будущий план не найден")
    await smartio_crud.delete_future_plan(db, db_plan)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
