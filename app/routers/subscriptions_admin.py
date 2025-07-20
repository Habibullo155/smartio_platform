from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.subscriptions import SubscriptionType
from app.schemas.subscriptions import SubscriptionTypeCreate, SubscriptionTypeUpdate, SubscriptionTypeResponse
from app.core.security import get_current_admin_user
from typing import List

router = APIRouter(
    prefix="/admin/subscriptions",
    tags=["Admin Subscription Management"],
    dependencies=[Depends(get_current_admin_user)] # Все маршруты защищены для админа
)

@router.post("/", response_model=SubscriptionTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription_type(
    sub_data: SubscriptionTypeCreate,
    db: AsyncSession = Depends(get_db)
):
    db_sub = SubscriptionType(**sub_data.model_dump())
    db.add(db_sub)
    await db.commit()
    await db.refresh(db_sub)
    return db_sub

@router.get("/", response_model=List[SubscriptionTypeResponse])
async def get_all_subscription_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionType))
    return result.scalars().all()

@router.get("/{sub_id}", response_model=SubscriptionTypeResponse)
async def get_subscription_type(sub_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SubscriptionType).filter(SubscriptionType.id == sub_id))
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription type not found")
    return sub

@router.put("/{sub_id}", response_model=SubscriptionTypeResponse)
async def update_subscription_type(
    sub_id: int,
    sub_data: SubscriptionTypeUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SubscriptionType).filter(SubscriptionType.id == sub_id))
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription type not found")

    for field, value in sub_data.model_dump(exclude_unset=True).items():
        setattr(sub, field, value)

    await db.commit()
    await db.refresh(sub)
    return sub

@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription_type(
    sub_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(SubscriptionType).filter(SubscriptionType.id == sub_id))
    sub = result.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription type not found")

    await db.delete(sub)
    await db.commit()