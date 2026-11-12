"""用户资料与列表。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user
from ..models import Post, User
from ..schemas import UserOut, UserUpdateIn
from ..serializers import post_out, user_out

router = APIRouter(prefix="/api/users", tags=["用户"])


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.scalars(select(User).order_by(User.id)).all()
    return [user_out(user) for user in users]


@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), current: User | None = Depends(get_optional_user)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    posts = db.scalars(
        select(Post).where(Post.author_id == user_id).order_by(Post.id.desc())
    ).all()
    return {
        "user": user_out(user),
        "posts": [post_out(post, db, current) for post in posts],
    }


@router.put("/me", response_model=UserOut)
def update_me(
    body: UserUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.nickname is not None:
        user.nickname = body.nickname.strip()[:20] or user.nickname
    if body.avatar is not None and body.avatar.strip():
        user.avatar = body.avatar.strip()[:4]
    if body.major is not None:
        user.major = body.major.strip()[:50]
    if body.grade is not None:
        user.grade = body.grade.strip()[:16]
    if body.bio is not None:
        user.bio = body.bio.strip()[:300]
    if body.tags is not None:
        user.tags = [tag.strip() for tag in body.tags if tag.strip()][:8]
    db.commit()
    db.refresh(user)
    return user_out(user)
