"""AI 编排：DeepSeek 优先，失败自动降级到本地引擎。"""
import logging

import httpx

from ..config import settings
from . import engine
from .knowledge import KNOWLEDGE

logger = logging.getLogger("qinghe.ai")


def ai_status() -> dict:
    available = bool(settings.deepseek_api_key)
    return {
        "mode": "cloud" if available else "local",
        "provider": "DeepSeek" if available else "青禾本地引擎",
        "model": settings.deepseek_model if available else "tf-idf",
    }


def _chat(messages: list[dict], temperature: float = 0.6, max_tokens: int = 800) -> str | None:
    """调用 DeepSeek Chat Completions；未配置 Key 或失败时返回 None。"""
    if not settings.deepseek_api_key:
        return None
    url = settings.deepseek_base_url.rstrip("/") + "/chat/completions"
    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                url,
                headers={
                    "Authorization": "Bearer " + settings.deepseek_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.deepseek_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                },
            )
            response.raise_for_status()
            data = response.json()
            return (data["choices"][0]["message"]["content"] or "").strip() or None
    except Exception as error:  # noqa: BLE001 - 任何异常都降级
        logger.warning("DeepSeek 调用失败，已降级到本地引擎：%s", error)
        return None


def _knowledge_context(question: str, limit: int = 4) -> str:
    local = engine.answer_question(question)
    picked = [item for item in KNOWLEDGE if item["topic"] == local.get("topic")]
    for item in KNOWLEDGE:
        if len(picked) >= limit:
            break
        if item not in picked:
            picked.append(item)
    return "\n".join(f"【{item['topic']}】{item['content']}" for item in picked[:limit])


def answer(question: str) -> dict:
    """校园问答：云端优先，失败降级本地。"""
    local = engine.answer_question(question)

    if settings.deepseek_api_key and local["kind"] not in ("greeting", "capability"):
        reply = _chat(
            [
                {
                    "role": "system",
                    "content": "你是校园社区「青禾」的 AI 助手。只依据下面给出的校园资料回答；"
                    "资料不足时明确说不知道，并建议用户去社区求助。回答不超过 120 字，语气友好。\n\n"
                    "校园资料：\n" + _knowledge_context(question),
                },
                {"role": "user", "content": question},
            ]
        )
        if reply:
            local = {
                **local,
                "answer": reply,
                "sources": local["sources"] or ["青禾 AI 助手"],
                "mode": "cloud",
            }
            return local

    local["mode"] = "local"
    return local


def write(text: str) -> dict:
    """发帖助手：云端润色，失败降级本地。"""
    local = engine.writing_assistant(text)
    local["mode"] = "local"

    if settings.deepseek_api_key:
        reply = _chat(
            [
                {
                    "role": "system",
                    "content": "你是校园社区的发帖助手。请把用户的一段话改写为适合校园社区发布的帖子正文："
                    "保留原意，补全标点，分 1–3 段，不超过 300 字，只输出正文，不要标题和解释。",
                },
                {"role": "user", "content": text},
            ]
        )
        if reply:
            local["content"] = reply
            local["mode"] = "cloud"

    return local


def match(me: dict, users: list[dict]) -> dict:
    """搭子匹配：云端补写理由，失败使用本地理由。"""
    local = engine.match_buddies(me, users)
    local["mode"] = "local"

    if settings.deepseek_api_key and local["matches"]:
        lines = [
            f"{index + 1}. {item['user']['nickname']}："
            + "、".join(item["user"].get("tags") or [])
            for index, item in enumerate(local["matches"])
        ]
        reply = _chat(
            [
                {
                    "role": "system",
                    "content": "你是校园搭子匹配助手。为下面每位同学写一句不超过 40 字的匹配理由，"
                    "语气友好具体，不要编造信息。每行一条，格式：序号. 理由",
                },
                {
                    "role": "user",
                    "content": "我的兴趣：" + "、".join(me.get("tags") or []) + "\n" + "\n".join(lines),
                },
            ]
        )
        if reply:
            parts = [line for line in reply.split("\n") if line.strip()]
            for index, item in enumerate(local["matches"]):
                if index < len(parts):
                    import re

                    cleaned = re.sub(r"^\s*\d+[.、)]\s*", "", parts[index]).strip()
                    if cleaned:
                        item["reason"] = cleaned
            local["mode"] = "cloud"

    return local
