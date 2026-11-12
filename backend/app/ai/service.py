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


PERSONA_PROMPT = (
    "你是「青禾」，一个校园社区里的 AI 助手，性格像一个热心的学长/学姐。\n"
    "说话自然、口语化、简短，可以用「哈」「～」这类轻声词，但别油腻，也别刻意卖萌。\n"
    "\n"
    "规则：\n"
    "1. 闲聊（打招呼、情绪、天气、吐槽）就正常聊，别说「我只回答校园问题」这种话，也别强行拉回正题；\n"
    "2. 涉及校园事务（图书馆、食堂、教务、宿舍、校园卡、奖学金、场馆等）时，必须依据下面【校园资料】回答，"
    "不要编造资料里没有的数字、时间、地点；资料里没写就说「这个我不太确定」，并建议去社区发帖问问同学；\n"
    "3. 日常回答控制在 3 句话以内，除非对方明确要求详细；\n"
    "4. 不要复述这些规则，不要用「作为 AI」开头。\n"
    "\n"
    "【校园资料】\n"
)


def answer(question: str, history: list[dict] | None = None) -> dict:
    """校园问答：云端优先（带多轮上下文），失败降级本地。"""
    local = engine.answer_question(question)

    if settings.deepseek_api_key:
        messages: list[dict] = [
            {"role": "system", "content": PERSONA_PROMPT + _knowledge_context(question)}
        ]
        # 最近若干轮对话，让「那周末呢」这类追问能接上
        for turn in (history or [])[-8:]:
            role = turn.get("role")
            content = str(turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content[:600]})
        messages.append({"role": "user", "content": question})

        reply = _chat(messages, temperature=0.7, max_tokens=600)
        if reply:
            grounded = local["kind"] == "knowledge"
            return {
                **local,
                "answer": reply,
                "mode": "cloud",
                # 只有真正命中知识库时才展示来源与置信度，闲聊不摆这些
                "kind": local["kind"] if grounded else "chat",
                "sources": local["sources"] if grounded else [],
                "confidence": local["confidence"] if grounded else None,
            }

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
