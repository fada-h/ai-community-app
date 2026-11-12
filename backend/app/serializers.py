"""ORM 对象 → 响应字典 的转换函数。"""
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .ai.knowledge import CATEGORY_MAP
from .models import Comment, Post, PostLike, User


def user_out(user: User | None) -> dict:
    if user is None:
        return {
            "id": 0, "username": "deleted", "nickname": "已注销用户", "avatar": "👤",
            "color": "#94a3b8", "major": "", "grade": "", "bio": "", "tags": [],
            "is_admin": False, "created_at": datetime.utcnow(),
        }
    return {
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname or user.username,
        "avatar": user.avatar or "🌱",
        "color": user.color or "#0f766e",
        "major": user.major or "",
        "grade": user.grade or "",
        "bio": user.bio or "",
        "tags": user.tags or [],
        "is_admin": bool(user.is_admin),
        "created_at": user.created_at,
    }


def _age_hours(created_at: datetime) -> float:
    return max(0.0, (datetime.utcnow() - created_at).total_seconds() / 3600)


def counts_for(post: Post, db: Session) -> tuple[int, int]:
    likes = db.scalar(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)
    ) or 0
    comments = db.scalar(
        select(func.count()).select_from(Comment).where(Comment.post_id == post.id)
    ) or 0
    return int(likes), int(comments)


def post_out(post: Post, db: Session, current_user: User | None = None) -> dict:
    like_count, comment_count = counts_for(post, db)
    category = CATEGORY_MAP.get(post.category, CATEGORY_MAP["life"])
    liked = False
    if current_user is not None:
        liked = db.scalar(
            select(PostLike.id).where(
                PostLike.post_id == post.id, PostLike.user_id == current_user.id
            )
        ) is not None
    heat = round(
        like_count * 6 + comment_count * 4 + post.views * 0.3 - _age_hours(post.created_at) * 0.8
    )
    author = db.get(User, post.author_id)
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "category": post.category,
        "category_name": category["name"],
        "category_icon": category["icon"],
        "tags": post.tags or [],
        "author": user_out(author),
        "views": post.views,
        "like_count": like_count,
        "comment_count": comment_count,
        "liked": liked,
        "heat": heat,
        "summary": " ".join((post.content or "").split())[:80],
        "created_at": post.created_at,
    }


def comment_out(comment: Comment, db: Session) -> dict:
    return {
        "id": comment.id,
        "content": comment.content,
        "author": user_out(db.get(User, comment.author_id)),
        "created_at": comment.created_at,
    }
