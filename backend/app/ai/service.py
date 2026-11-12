"""AI 编排：DeepSeek 优先，失败自动降级到本地引擎。"""
import json
import logging
import re

import httpx

from ..config import settings
from . import engine
from .knowledge import CATEGORY_MAP, KNOWLEDGE

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


WRITE_PROMPT = (
    "你是校园社区的发帖助手。请把用户的一段口语化描述改写成一条适合校园社区发布的帖子。\n"
    "只输出 JSON，不要任何解释、不要代码块标记，格式：\n"
    '{"title":"不超过 26 字、语义完整的标题","content":"1-3 段正文，不超过 300 字","category":"study|club|market|lost|life","tags":["3-5 个关键词"]}\n'
    "category 含义：study=学习互助 club=社团活动 market=二手闲置 lost=失物招领 life=校园生活。\n"
    "保留用户原意，不要编造时间、地点、联系方式等未提供的信息。"
)


def _extract_json(text: str) -> dict | None:
    """从模型输出中提取第一个 JSON 对象，兼容 ```json 代码块。"""
    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except Exception:  # noqa: BLE001
        return None


def write(text: str) -> dict:
    """发帖助手：云端生成标题/正文/分类/标签，失败降级本地。"""
    local = engine.writing_assistant(text)
    local["mode"] = "local"

    if settings.deepseek_api_key:
        reply = _chat(
            [
                {"role": "system", "content": WRITE_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.5,
            max_tokens=700,
        )
        if reply:
            data = _extract_json(reply)
            if data:
                if data.get("title"):
                    local["title"] = str(data["title"])[:40]
                if data.get("content"):
                    local["content"] = str(data["content"])[:3000]
                category = data.get("category")
                if category in CATEGORY_MAP:
                    local["category"] = category
                    local["category_name"] = CATEGORY_MAP[category]["name"]
                tags = data.get("tags")
                if isinstance(tags, list) and tags:
                    local["tags"] = [str(tag)[:12] for tag in tags][:6]
            else:
                # 模型没按 JSON 返回时，至少保留润色后的正文
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
