from fastapi import APIRouter, Depends, HTTPException, status, Form, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.users import User
from app.schemas.auth import Token, AdminLogin
from app.core.security import verify_password, create_access_token, get_current_admin_user, oauth2_scheme_admin
from app.config import settings
from datetime import timedelta

router = APIRouter(
    prefix="/admin",
    tags=["Admin Authentication & UI"]
)

templates = Jinja2Templates(directory="templates")

@router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request})

@router.post("/token", response_model=Token)
async def admin_login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user_result = await db.execute(select(User).filter(User.email == form_data.username))
    user = user_result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password) or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES_ADMIN) # Добавь в config
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role, "type": "admin"},
        expires_delta=access_token_expires
    )
    # Сохраняем токен в куки для удобства фронтенда (если Jinja2)
    response.set_cookie(key="admin_access_token", value=access_token, httponly=True, samesite="Lax")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, current_user: User = Depends(get_current_admin_user)):
    # Это пример защищенной страницы админа
    return templates.TemplateResponse("admin_dashboard.html", {"request": request, "user": current_user})

# Добавь маршруты для CRUD операций (блог, подписки, клиенты, планы)
# в отдельные файлы (blog_admin_routes.py, subscriptions_admin_routes.py и т.д.)
# и включи их в main.py или здесь, если они очень простые.
# Для лучшей структуры, лучше создать отдельные роутеры, как я покажу ниже.