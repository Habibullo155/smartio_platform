from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.blog import Blog, BlogCategory
from app.models.future_plans import FuturePlan

router = APIRouter(
    tags=["Frontend Pages"]
)

templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    # Здесь можно загрузить последние блоги или какие-то промо-материалы
    result = await db.execute(select(Blog).filter(Blog.is_published == True).order_by(Blog.created_at.desc()).limit(3))
    latest_blogs = result.scalars().all()
    return templates.TemplateResponse("index.html", {"request": request, "latest_blogs": latest_blogs})

@router.get("/blogs", response_class=HTMLResponse)
async def read_blogs(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).options(selectinload(Blog.category)).filter(Blog.is_published == True).order_by(Blog.created_at.desc()))
    blogs = result.scalars().all()
    categories_result = await db.execute(select(BlogCategory).filter(BlogCategory.is_active == True))
    categories = categories_result.scalars().all()
    return templates.TemplateResponse("blogs.html", {"request": request, "blogs": blogs, "categories": categories})

@router.get("/blogs/{blog_id}", response_class=HTMLResponse)
async def read_blog_post(blog_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Blog).options(selectinload(Blog.category)).filter(Blog.id == blog_id, Blog.is_published == True))
    blog = result.scalars().first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found or not published")
    return templates.TemplateResponse("blog_detail.html", {"request": request, "blog": blog})

@router.get("/future-plans", response_class=HTMLResponse)
async def read_future_plans(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FuturePlan).filter(FuturePlan.is_active == True).order_by(FuturePlan.target_date.asc()))
    plans = result.scalars().all()
    return templates.TemplateResponse("future_plans.html", {"request": request, "plans": plans})