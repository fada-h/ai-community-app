"""Pydantic 请求 / 响应模型。"""
from datetime import datetime

from pydantic import BaseModel, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=64)
    nickname: str = ""


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nickname: str
    avatar: str
    color: str
    major: str
    grade: str
    bio: str
    tags: list[str]
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdateIn(BaseModel):
    nickname: str | None = None
    avatar: str | None = None
    major: str | None = None
    grade: str | None = None
    bio: str | None = None
    tags: list[str] | None = None


class TokenOut(BaseModel):
    token: str
    user: UserOut


class PostIn(BaseModel):
    title: str = Field(min_length=2, max_length=80)
    content: str = Field(min_length=5, max_length=4000)
    category: str = "life"
    tags: list[str] = []


class PostOut(BaseModel):
    id: int
    title: str
    content: str
    category: str
    category_name: str
    category_icon: str
    tags: list[str]
    author: UserOut
    views: int
    like_count: int
    comment_count: int
    liked: bool
    heat: int
    summary: str
    created_at: datetime


class CommentIn(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentOut(BaseModel):
    id: int
    content: str
    author: UserOut
    created_at: datetime


class AiTextIn(BaseModel):
    text: str


class AiWriteOut(BaseModel):
    title: str
    content: str
    category: str
    category_name: str
    category_confidence: float
    tags: list[str]
    summary: str
    issues: list[str]
    tips: list[str]
    safety: dict
    changed: bool
    mode: str


class MatchItem(BaseModel):
    user: UserOut
    score: float
    reason: str


class MatchOut(BaseModel):
    matches: list[MatchItem]
    message: str
    mode: str


class ChatTurn(BaseModel):
    role: str
    content: str


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    history: list[ChatTurn] = []


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=1000)


class MessageOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    user: UserOut
    last_message: str
    last_at: datetime
    unread: int


class StatsOut(BaseModel):
    users: int
    posts: int
    comments: int
    ai_calls: int
    posts_today: int
    active_users: int
    categories: list[dict]
