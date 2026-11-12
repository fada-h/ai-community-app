"""应用元信息与社区统计。"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai.knowledge import CATEGORIES
from ..ai.service import ai_status
from ..config import settings
from ..db import get_db
from ..models import AiLog, Comment, Post, User

router = APIRouter(tags=["系统"])


def _stats(db: Session) -> dict:
    total_users = db.scalar(select(func.count()).select_from(User)) or 0
    total_posts = db.scalar(select(func.count()).select_from(Post)) or 0
    total_comments = db.scalar(select(func.count()).select_from(Comment)) or 0
    total_ai = db.scalar(select(func.count()).select_from(AiLog)) or 0

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    posts_today = db.scalar(
        select(func.count()).select_from(Post).where(Post.created_at >= today)
    ) or 0

    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db.scalar(
        select(func.count(func.distinct(Post.author_id))).where(Post.created_at >= week_ago)
    ) or 0

    return {
        "users": int(total_users),
        "posts": int(total_posts),
        "comments": int(total_comments),
        "ai_calls": int(total_ai),
        "posts_today": int(posts_today),
        "active_users": int(active_users),
        "categories": [
            {
                **category,
                "count": int(
                    db.scalar(
                        select(func.count()).select_from(Post).where(Post.category == category["id"])
                    )
                    or 0
                ),
            }
            for category in CATEGORIES
        ],
    }


@router.get("/api/meta")
def meta(db: Session = Depends(get_db)):
    return {
        "app": {
            "name": settings.app_name,
            "subtitle": settings.app_subtitle,
            "version": "2.0.0",
        },
        "categories": CATEGORIES,
        "ai": ai_status(),
        "demo_account": {"username": "linxiaoman", "password": "123456"},
        "stats": _stats(db),
        "database": "sqlite" if settings.is_sqlite else "mysql",
    }


@router.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    return _stats(db)
