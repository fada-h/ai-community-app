"""FastAPI 通用依赖：解析 Bearer Token 得到当前用户。"""
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .db import get_db
from .models import User
from .security import parse_token


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    payload = parse_token(authorization[7:].strip())
    if not payload:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    user = db.get(User, int(payload["uid"]))
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def get_optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """可选登录：用于公开列表接口返回 liked 状态。"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    payload = parse_token(authorization[7:].strip())
    if not payload:
        return None
    return db.get(User, int(payload["uid"]))


def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
