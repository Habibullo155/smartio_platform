from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.future_plans import FuturePlan
from app.schemas.future_plans import FuturePlanCreate, FuturePlanUpdate, FuturePlanResponse
from app.core.security import get_current_admin_user
from typing import List

router = APIRouter(
    prefix="/admin/future-plans",
    tags=["Admin Future Plans Management"],
    dependencies=[Depends(get_current_admin_user)]
)

@router.post("/", response_model=FuturePlanResponse, status_code=status.HTTP_201_CREATED)
async def create_future_plan(
    plan_data: FuturePlanCreate,
    db: AsyncSession = Depends(get_db)
):
    db_plan = FuturePlan(**plan_data.model_dump())
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    return db_plan

@router.get("/", response_model=List[FuturePlanResponse])
async def get_all_future_plans(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FuturePlan))
    return result.scalars().all()

@router.get("/{plan_id}", response_model=FuturePlanResponse)
async def get_future_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FuturePlan).filter(FuturePlan.id == plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Future plan not found")
    return plan

@router.put("/{plan_id}", response_model=FuturePlanResponse)
async def update_future_plan(
    plan_id: int,
    plan_data: FuturePlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FuturePlan).filter(FuturePlan.id == plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Future plan not found")

    for field, value in plan_data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    await db.commit()
    await db.refresh(plan)
    return plan

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_future_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(FuturePlan).filter(FuturePlan.id == plan_id))
    plan = result.scalars().first()
    if not plan:
        raise HTTPException(status_code=404, detail="Future plan not found")

    await db.delete(plan)
    await db.commit()