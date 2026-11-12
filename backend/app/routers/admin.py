"""后台管理：概览、帖子管理、用户管理。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_admin_user
from ..models import AiLog, Comment, Post, User
from ..serializers import post_out, user_out

router = APIRouter(prefix="/api/admin", tags=["后台"])


@router.get("/overview")
def overview(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    recent_posts = db.scalars(select(Post).order_by(Post.id.desc()).limit(10)).all()
    top_users = db.execute(
        select(User, func.count(Post.id).label("post_count"))
        .join(Post, Post.author_id == User.id, isouter=True)
        .group_by(User.id)
        .order_by(func.count(Post.id).desc())
        .limit(8)
    ).all()

    return {
        "totals": {
            "users": int(db.scalar(select(func.count()).select_from(User)) or 0),
            "posts": int(db.scalar(select(func.count()).select_from(Post)) or 0),
            "comments": int(db.scalar(select(func.count()).select_from(Comment)) or 0),
            "ai_calls": int(db.scalar(select(func.count()).select_from(AiLog)) or 0),
        },
        "recent_posts": [post_out(post, db, admin) for post in recent_posts],
        "top_users": [
            {**user_out(user), "post_count": int(count or 0)} for user, count in top_users
        ],
    }


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    db.delete(post)
    db.commit()
    return {"ok": True, "deleted": post_id}


@router.get("/users")
def list_users(admin: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()
    counts = dict(
        db.execute(select(Post.author_id, func.count(Post.id)).group_by(Post.author_id)).all()
    )
    return [
        {**user_out(user), "post_count": int(counts.get(user.id, 0))} for user in users
    ]


@router.post("/users/{user_id}/toggle-admin")
def toggle_admin(
    user_id: int, admin: User = Depends(get_admin_user), db: Session = Depends(get_db)
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="不能修改自己的权限")
    user.is_admin = not user.is_admin
    db.commit()
    return {"id": user.id, "is_admin": user.is_admin}
