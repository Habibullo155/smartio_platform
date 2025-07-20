from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Form
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.blog import Blog, BlogCategory
from app.models.users import User
from app.schemas.blog import BlogCreate, BlogUpdate, BlogResponse, BlogCategoryCreate, BlogCategoryUpdate, BlogCategoryResponse
from app.core.security import get_current_admin_user
from typing import List, Optional
import os

router = APIRouter(
    prefix="/admin/blog",
    tags=["Admin Blog Management"]
)

# --- Вспомогательная функция для сохранения изображения ---
async def save_image(file: UploadFile) -> str:
    # Здесь должна быть логика сохранения файла на диск/облако
    # Для примера сохраняем в папку static/uploads
    upload_dir = "static/uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    return f"/static/uploads/{file.filename}" # Путь для доступа через URL

# --- CRUD для категорий блога ---
@router.post("/categories/", response_model=BlogCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_category(
    category_data: BlogCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    db_category = BlogCategory(**category_data.model_dump())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

@router.get("/categories/", response_model=List[BlogCategoryResponse])
async def get_blog_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogCategory))
    return result.scalars().all()

# --- CRUD для записей блога ---
@router.post("/", response_model=BlogResponse, status_code=status.HTTP_201_CREATED)
async def create_blog_post(
    title: str = Form(...),
    full_description: str = Form(...),
    short_description: Optional[str] = Form(None),
    category_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None), # Для загрузки файла
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    image_url = None
    if image:
        image_url = await save_image(image)

    blog_data = BlogCreate(
        title=title,
        short_description=short_description,
        full_description=full_description,
        image_url=image_url,
        category_id=category_id
    )
    db_blog = Blog(**blog_data.model_dump())
    db.add(db_blog)
    await db.commit()
    await db.refresh(db_blog)

    # После создания загрузим с категорией для ответа
    result = await db.execute(select(Blog).options(selectinload(Blog.category)).filter(Blog.id == db_blog.id))
    db_blog_with_category = result.scalars().first()
    return db_blog_with_category

@router.get("/", response_model=List[BlogResponse])
async def get_all_blog_posts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).options(selectinload(Blog.category)))
    return result.scalars().all()

@router.get("/{blog_id}", response_model=BlogResponse)
async def get_blog_post(blog_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).options(selectinload(Blog.category)).filter(Blog.id == blog_id))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    return blog

@router.put("/{blog_id}", response_model=BlogResponse)
async def update_blog_post(
    blog_id: int,
    blog_data: BlogUpdate, # Используем ProductUpdate для частичного обновления
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Blog).filter(Blog.id == blog_id))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    for field, value in blog_data.model_dump(exclude_unset=True).items():
        setattr(blog, field, value)

    await db.commit()
    await db.refresh(blog)
    result = await db.execute(select(Blog).options(selectinload(Blog.category)).filter(Blog.id == blog.id))
    updated_blog = result.scalars().first()
    return updated_blog

@router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blog_post(
    blog_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(Blog).filter(Blog.id == blog_id))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")

    await db.delete(blog)
    await db.commit()