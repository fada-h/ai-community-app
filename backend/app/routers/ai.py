"""AI 接口：写作助手、搭子匹配、校园问答（SSE 流式）。"""
import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import service
from ..ai.engine import chunk_text
from ..config import settings
from ..db import SessionLocal, get_db
from ..deps import get_current_user, get_optional_user
from ..models import AiLog, User
from ..schemas import AiTextIn, AiWriteOut, ChatIn, MatchOut
from ..serializers import user_out

router = APIRouter(prefix="/api/ai", tags=["AI"])


def _log(db: Session, user_id: int, kind: str, text: str, mode: str, chars: int) -> None:
    db.add(
        AiLog(
            user_id=user_id,
            kind=kind,
            input=text[:200],
            mode=mode,
            chars=chars,
        )
    )
    db.commit()


@router.post("/write", response_model=AiWriteOut)
def ai_write(
    body: AiTextIn,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_optional_user),
):
    text = body.text.strip()
    result = service.write(text)
    _log(db, current.id if current else 0, "write", text, result["mode"], len(result["content"]))
    return result


@router.post("/match", response_model=MatchOut)
def ai_match(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    users = db.scalars(select(User)).all()
    payload = [
        {
            "id": item.id,
            "nickname": item.nickname or item.username,
            "avatar": item.avatar,
            "color": item.color,
            "major": item.major,
            "grade": item.grade,
            "bio": item.bio,
            "tags": item.tags or [],
        }
        for item in users
    ]
    me = {
        "id": user.id,
        "tags": user.tags or [],
        "bio": user.bio or "",
        "major": user.major or "",
    }
    result = service.match(me, payload)

    matches = []
    for item in result["matches"]:
        full = db.get(User, item["user"]["id"])
        matches.append(
            {
                "user": user_out(full),
                "score": item["score"],
                "reason": item["reason"],
            }
        )

    _log(db, user.id, "match", "、".join(me["tags"]), result["mode"], 0)
    return {"matches": matches, "message": result["message"], "mode": result["mode"]}


async def _stream_answer(message: str, history: list[dict] | None = None):
    """SSE 生成器：先推送 meta，再逐块推送 delta，最后 done。"""
    result = await asyncio.to_thread(service.answer, message, history)

    # 记录调用（独立会话，避免请求级会话在流式期间关闭）
    try:
        with SessionLocal() as log_db:
            log_db.add(
                AiLog(kind="chat", input=message[:200], mode=result["mode"], chars=len(result["answer"]))
            )
            log_db.commit()
    except Exception:  # noqa: BLE001 - 记录失败不影响回答
        pass

    meta = {
        "mode": result["mode"],
        "kind": result.get("kind", "chat"),
        "confidence": result.get("confidence"),
        "sources": result.get("sources", []),
        "topic": result.get("topic", ""),
        "suggestions": result.get("suggestions", []),
    }
    yield "event: meta\ndata: " + json.dumps(meta, ensure_ascii=False) + "\n\n"

    for chunk in chunk_text(result["answer"]):
        yield "event: delta\ndata: " + json.dumps({"text": chunk}, ensure_ascii=False) + "\n\n"
        await asyncio.sleep(0.016)

    yield "event: done\ndata: " + json.dumps({"length": len(result["answer"])}) + "\n\n"


@router.post("/chat")
def ai_chat(body: ChatIn):
    history = [{"role": turn.role, "content": turn.content} for turn in body.history]
    return StreamingResponse(
        _stream_answer(body.message.strip(), history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/logs")
def ai_logs(db: Session = Depends(get_db)):
    logs = db.scalars(select(AiLog).order_by(AiLog.id.desc()).limit(20)).all()
    return [
        {
            "id": item.id,
            "kind": item.kind,
            "input": item.input,
            "mode": item.mode,
            "chars": item.chars,
            "created_at": item.created_at,
        }
        for item in logs
    ]


@router.get("/status")
def ai_status():
    return {**service.ai_status(), "disclaimer": settings.ai_disclaimer}
