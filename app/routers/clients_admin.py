from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.clients import Client
from app.schemas.clients import ClientCreate, ClientUpdate, ClientResponse
from app.core.security import get_current_admin_user, get_password_hash
from typing import List

router = APIRouter(
    prefix="/admin/clients",
    tags=["Admin Client Management"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: AsyncSession = Depends(get_db)
):
    hashed_password = get_password_hash(client_data.password)
    db_client = Client(hashed_password=hashed_password, **client_data.model_dump(exclude={"password"}))
    db.add(db_client)
    await db.commit()
    await db.refresh(db_client)
    # Загружаем связанную подписку для ответа
    result = await db.execute(select(Client).options(selectinload(Client.subscription_type)).filter(Client.id == db_client.id))
    return result.scalars().first()

@router.get("/", response_model=List[ClientResponse])
async def get_all_clients(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).options(selectinload(Client.subscription_type)))
    return result.scalars().all()

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(client_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).options(selectinload(Client.subscription_type)).filter(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).filter(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in client_data.model_dump(exclude_unset=True).items():
        if field == "password" and value: # Если пароль обновляется
            client.hashed_password = get_password_hash(value)
        else:
            setattr(client, field, value)

    await db.commit()
    await db.refresh(client)
    result = await db.execute(select(Client).options(selectinload(Client.subscription_type)).filter(Client.id == client.id))
    return result.scalars().first()

@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Client).filter(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    await db.delete(client)
    await db.commit()