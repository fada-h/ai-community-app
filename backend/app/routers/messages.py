"""私信：会话列表、历史消息、发送（实时推送见 app/ws.py）。"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import get_current_user
from ..models import Message, User
from ..schemas import MessageIn, MessageOut
from ..serializers import user_out
from ..ws import manager

router = APIRouter(prefix="/api/messages", tags=["私信"])


@router.get("/conversations")
def conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    messages = db.scalars(
        select(Message)
        .where(or_(Message.sender_id == user.id, Message.receiver_id == user.id))
        .order_by(Message.id.desc())
    ).all()

    latest: dict[int, Message] = {}
    unread: dict[int, int] = {}
    for message in messages:
        peer = message.receiver_id if message.sender_id == user.id else message.sender_id
        latest.setdefault(peer, message)
        if message.receiver_id == user.id and not message.is_read:
            unread[peer] = unread.get(peer, 0) + 1

    result = []
    for peer_id, message in latest.items():
        peer = db.get(User, peer_id)
        if peer is None:
            continue
        result.append(
            {
                "user": user_out(peer),
                "last_message": message.content,
                "last_at": message.created_at,
                "unread": unread.get(peer_id, 0),
                "online": manager.online(peer_id),
            }
        )
    result.sort(key=lambda item: item["last_at"], reverse=True)
    return result


@router.get("/{peer_id}", response_model=list[MessageOut])
def history(
    peer_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    messages = db.scalars(
        select(Message)
        .where(
            or_(
                (Message.sender_id == user.id) & (Message.receiver_id == peer_id),
                (Message.sender_id == peer_id) & (Message.receiver_id == user.id),
            )
        )
        .order_by(Message.id)
        .limit(200)
    ).all()

    changed = False
    for message in messages:
        if message.receiver_id == user.id and not message.is_read:
            message.is_read = True
            changed = True
    if changed:
        db.commit()

    return messages


@router.post("/{peer_id}", response_model=MessageOut, status_code=201)
async def send_message(
    peer_id: int,
    body: MessageIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    peer = db.get(User, peer_id)
    if peer is None:
        raise HTTPException(status_code=404, detail="对方不存在")
    if peer_id == user.id:
        raise HTTPException(status_code=400, detail="不能给自己发消息")

    message = Message(
        sender_id=user.id,
        receiver_id=peer_id,
        content=body.content.strip()[:1000],
        created_at=datetime.utcnow(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    payload = {
        "type": "message",
        "id": message.id,
        "sender_id": message.sender_id,
        "receiver_id": message.receiver_id,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
        "sender_name": user.nickname or user.username,
        "sender_avatar": user.avatar,
    }
    await manager.send_to(peer_id, payload)
    await manager.send_to(user.id, payload)
    return message
