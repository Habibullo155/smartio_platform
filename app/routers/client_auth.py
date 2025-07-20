from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.clients import Client
from app.schemas.auth import Token
from app.core.security import verify_password, create_access_token, oauth2_scheme_client
from app.config import settings
from datetime import timedelta

router = APIRouter(
    prefix="/client",
    tags=["Client Authentication"]
)

@router.post("/token", response_model=Token)
async def client_login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(), # Используем стандартную форму
    db: AsyncSession = Depends(get_db)
):
    client_result = await db.execute(select(Client).filter(Client.username == form_data.username))
    client = client_result.scalars().first()

    if not client or not verify_password(form_data.password, client.hashed_password) or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES_CLIENT) # Добавь в config
    access_token = create_access_token(
        data={"sub": str(client.id), "type": "client"},
        expires_delta=access_token_expires
    )
    response.set_cookie(key="client_access_token", value=access_token, httponly=True, samesite="Lax")
    return {"access_token": access_token, "token_type": "bearer"}

# Пример защищенного маршрута для клиента
from app.core.security import get_current_client_user
from app.schemas.clients import ClientResponse

@router.get("/me", response_model=ClientResponse)
async def read_client_me(current_client: Client = Depends(get_current_client_user)):
    return current_client