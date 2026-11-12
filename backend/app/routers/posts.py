"""帖子：列表、发布、详情、点赞、评论。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user, get_optional_user
from ..models import Comment, Post, PostLike, User
from ..schemas import CommentIn, CommentOut, PostIn, PostOut
from ..serializers import comment_out, post_out

router = APIRouter(prefix="/api/posts", tags=["帖子"])

CATEGORY_IDS = {"study", "club", "market", "lost", "life"}


@router.get("")
def list_posts(
    category: str = "",
    q: str = "",
    sort: str = "latest",
    author: int = 0,
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    query = select(Post)
    if category and category != "all":
        query = query.where(Post.category == category)
    if author:
        query = query.where(Post.author_id == author)
    if q:
        keyword = "%" + q.strip() + "%"
        query = query.where(or_(Post.title.like(keyword), Post.content.like(keyword)))

    posts = list(db.scalars(query).all())
    items = [post_out(post, db, current) for post in posts]
    if sort == "hot":
        items.sort(key=lambda item: item["heat"], reverse=True)
    else:
        items.sort(key=lambda item: item["id"], reverse=True)
    return {"total": len(items), "items": items[:limit]}


@router.post("", response_model=PostOut, status_code=201)
def create_post(
    body: PostIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.category not in CATEGORY_IDS:
        raise HTTPException(status_code=400, detail="分类不合法")
    post = Post(
        author_id=user.id,
        category=body.category,
        title=body.title.strip()[:80],
        content=body.content.strip()[:4000],
        tags=[tag.strip() for tag in body.tags if tag.strip()][:6],
        views=0,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post_out(post, db, user)


@router.get("/{post_id}")
def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    post.views += 1
    db.commit()

    comments = db.scalars(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.id)
    ).all()
    related = db.scalars(
        select(Post)
        .where(Post.category == post.category, Post.id != post.id)
        .order_by(Post.id.desc())
        .limit(3)
    ).all()

    return {
        "post": post_out(post, db, current),
        "comments": [comment_out(comment, db) for comment in comments],
        "related": [post_out(item, db, current) for item in related],
    }


@router.post("/{post_id}/like")
def toggle_like(
    post_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")

    existing = db.scalar(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user.id)
    )
    if existing:
        db.delete(existing)
        liked = False
    else:
        db.add(PostLike(post_id=post_id, user_id=user.id))
        liked = True
    db.commit()

    count = db.scalar(
        select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
    ) or 0
    return {"liked": liked, "like_count": int(count)}


@router.get("/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    comments = db.scalars(
        select(Comment).where(Comment.post_id == post_id).order_by(Comment.id)
    ).all()
    return [comment_out(comment, db) for comment in comments]


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(
    post_id: int,
    body: CommentIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    comment = Comment(
        post_id=post_id,
        author_id=user.id,
        content=body.content.strip()[:500],
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment_out(comment, db)
