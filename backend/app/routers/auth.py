"""注册 / 登录 / 当前用户。"""
import random
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, RegisterIn, TokenOut, UserOut
from ..security import create_token, hash_password, verify_password
from ..serializers import user_out

router = APIRouter(prefix="/api/auth", tags=["认证"])

AVATARS = ["🌱", "🍀", "🌊", "🌙", "☀️", "🪴", "🐳", "🦊", "🐼", "🦉"]
PALETTE = ["#6366f1", "#ec4899", "#10b981", "#f59e0b", "#0ea5e9", "#8b5cf6", "#ef4444", "#14b8a6"]


@router.post("/register", response_model=TokenOut, status_code=201)
def register(body: RegisterIn, db: Session = Depends(get_db)):
    username = body.username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_]{3,20}", username):
        raise HTTPException(status_code=400, detail="用户名只能包含字母、数字和下划线，长度 3–20")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")
    if db.scalar(select(User).where(User.username == username)):
        raise HTTPException(status_code=400, detail="用户名已被注册")

    user = User(
        username=username,
        password_hash=hash_password(body.password),
        nickname=(body.nickname or username).strip()[:20],
        avatar=random.choice(AVATARS),
        color=random.choice(PALETTE),
        tags=[],
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_token(user.id), "user": user_out(user)}


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username.strip()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"token": create_token(user.id), "user": user_out(user)}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user_out(user)
