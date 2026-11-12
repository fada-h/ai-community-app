"""本地 AI 引擎（纯 Python，无第三方依赖）。

提供三种能力：
  1. 校园问答：TF-IDF + 余弦相似度检索知识库（RAG 思路）
  2. 发帖助手：分类 / 标签 / 润色 / 摘要 / 安全检测
  3. 搭子匹配：兴趣标签 Jaccard + 文本相似度
"""
import math
import re
from collections import Counter

from .knowledge import CATEGORY_MAP, KNOWLEDGE, SECURITY_WORDS

STOP_WORDS = {
    "的", "了", "和", "是", "在", "我", "有", "就", "不", "人", "都", "一", "一个",
    "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好",
    "自己", "这", "那", "这个", "那个", "什么", "怎么", "可以", "我们", "他们",
    "但是", "因为", "所以", "如果", "然后", "现在", "今天",
    "the", "a", "an", "and", "or", "to", "of", "in", "is", "it", "for", "on", "with",
}

GENERIC_BIGRAMS = {
    "想找", "找人", "一起", "有没", "没有", "想和", "和的", "我的", "你的", "他的",
    "这个", "那个", "什么", "怎么", "可以", "我们", "你们", "他们", "就是", "觉得",
    "知道", "如果", "因为", "所以", "但是", "然后", "现在", "今天", "明天", "昨天",
    "时候", "一个", "一些", "不是", "还是", "已经", "正在", "希望", "想要", "需要",
    "比较", "非常", "特别", "真的", "应该", "可能", "或者", "而且", "不过", "虽然",
    "于是", "因此", "这样", "那样", "这里", "那里", "上面", "下面", "东西", "事情",
}

DOMAIN_TERMS = [
    "考研", "保研", "自习", "图书馆", "食堂", "宿舍", "社团", "志愿", "公益",
    "摄影", "篮球", "羽毛球", "跑步", "健身", "咖啡", "读书", "写作", "吉他",
    "编程", "前端", "后端", "算法", "竞赛", "蓝桥杯", "实习", "校招", "简历",
    "快递", "失物", "二手", "显示器", "教材", "约拍", "骑行", "游戏", "设计",
    "插画", "英语", "翻译", "留学", "实验室", "嵌入式", "烘焙", "招新", "组队",
]

CJK = re.compile(r"[\u4e00-\u9fa5]")


def normalize(text: str) -> str:
    """保留中英文数字，其余替换为空格并转小写。"""
    return re.sub(r"[^\u4e00-\u9fa5a-z0-9]+", " ", str(text or "").lower()).strip()


def tokenize(text: str) -> list[tuple[str, float]]:
    """中文 bigram（权重 1）+ 单字（权重 0.5），英文数字整词。"""
    tokens: list[tuple[str, float]] = []
    for run in normalize(text).split():
        if CJK.search(run):
            chars = list(run)
            for i, ch in enumerate(chars):
                if ch in STOP_WORDS:
                    continue
                tokens.append((ch, 0.5))
                if i + 1 < len(chars):
                    bigram = ch + chars[i + 1]
                    if bigram not in STOP_WORDS:
                        tokens.append((bigram, 1.0))
        else:
            tokens.append((run, 1.0))
    return tokens


def _vector(tokens: list[tuple[str, float]], idf: dict[str, float]) -> dict[str, float]:
    vec: dict[str, float] = {}
    for term, weight in tokens:
        vec[term] = vec.get(term, 0.0) + weight * idf.get(term, 1.0)
    norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
    return {k: v / norm for k, v in vec.items()}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(value * b.get(term, 0.0) for term, value in a.items())


# ---------------- 知识库索引（模块加载时构建一次） ----------------
_DOCS = [
    {
        "item": item,
        "tokens": tokenize(
            item["topic"] + " " + " ".join(item["keywords"]) + " " + item["content"]
        ),
    }
    for item in KNOWLEDGE
]

_DF: Counter = Counter()
for _doc in _DOCS:
    _DF.update(set(term for term, _ in _doc["tokens"]))

_Idf: dict[str, float] = {
    term: math.log((len(_DOCS) + 1) / (df + 0.5)) + 1.0 for term, df in _DF.items()
}

for _doc in _DOCS:
    _doc["vector"] = _vector(_doc["tokens"], _Idf)


# ---------------- 1. 校园问答 ----------------
def answer_question(question: str) -> dict:
    text = str(question or "").strip()
    if not text:
        return {
            "answer": "把你想问的事情告诉我吧，比如“图书馆几点关门？”“校园卡丢了怎么办？”",
            "sources": [],
            "confidence": 0.0,
            "kind": "empty",
            "suggestions": ["图书馆开放时间", "校园卡挂失", "奖学金怎么申请"],
        }

    if re.match(r"^(你好|hi|hello|嗨|在吗)", text, re.I):
        return {
            "answer": "你好呀，我是青禾 AI 助手 🌱 我可以帮你查校园事务、润色帖子、找搭子。想先了解点什么？",
            "sources": [],
            "confidence": 1.0,
            "kind": "greeting",
            "suggestions": ["图书馆几点关门？", "帮我找一起自习的搭子", "校园网连不上怎么办"],
        }

    if re.search(r"(你是谁|能做什么|有什么功能|介绍一下自己)", text):
        return {
            "answer": "我是「青禾」——校园社区里的 AI 助手，主要有三种能力：\n"
            "1) 校园事务问答：图书馆、食堂、教务、宿舍、奖学金等 26 类问题；\n"
            "2) 发帖助手：润色文字、推荐分类和标签、生成摘要、检测敏感内容；\n"
            "3) 搭子匹配：根据兴趣标签和描述，帮你找到同频的同学。",
            "sources": ["青禾 AI 能力说明"],
            "confidence": 1.0,
            "kind": "capability",
            "suggestions": ["图书馆开放时间", "怎么申请奖学金", "帮我找考研搭子"],
        }

    query = _vector(tokenize(text), _Idf)
    ranked = sorted(
        ((doc, _cosine(query, doc["vector"])) for doc in _DOCS),
        key=lambda pair: pair[1],
        reverse=True,
    )
    best_doc, best_score = ranked[0]

    if best_score < 0.06:
        return {
            "answer": "这个问题我暂时没有在校园知识库里找到可靠答案。你可以换个说法，或者直接问辅导员；"
            "也可以把问题发到社区「学习互助」板块，让同学帮你。",
            "sources": [],
            "confidence": round(best_score, 3),
            "kind": "no-answer",
            "suggestions": ["图书馆开放时间", "校园卡怎么补办", "奖学金申请时间"],
        }

    related = [doc["item"] for doc, score in ranked[1:2] if score > best_score * 0.6]
    return {
        "answer": best_doc["item"]["content"],
        "sources": [best_doc["item"]["source"]] + [item["source"] for item in related],
        "confidence": round(min(0.99, best_score * 1.6 + 0.15), 3),
        "kind": "knowledge",
        "topic": best_doc["item"]["topic"],
        "suggestions": [item["topic"] for item in related[:2]],
    }


# ---------------- 2. 发帖助手 ----------------
CATEGORY_RULES = {
    "study": ["作业", "高数", "期末", "复习", "题", "笔记", "组队", "竞赛", "考研", "保研",
              "实验室", "课程", "自习", "论文", "答辩"],
    "club": ["社团", "招新", "活动", "演出", "比赛", "志愿", "讲座", "晚会", "报名", "乐队", "篮球赛"],
    "market": ["出", "收", "二手", "闲置", "转", "便宜", "卖", "买", "价", "甩", "求购", "九成新"],
    "lost": ["丢", "捡到", "失物", "招领", "校园卡", "钥匙", "钱包", "身份证", "耳机", "水杯"],
    "life": ["食堂", "宿舍", "天气", "吐槽", "推荐", "求助", "表白", "校园", "饭", "快递", "心情", "emo"],
}


def classify(text: str) -> dict:
    normalized = normalize(text)
    scores = {}
    for cid, words in CATEGORY_RULES.items():
        scores[cid] = sum(1 for word in words if normalize(word) in normalized)
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    total = sum(score for _, score in ranked)
    cid, score = ranked[0]
    return {
        "category": cid if score > 0 else "life",
        "confidence": round(score / total, 2) if total > 0 else 0.3,
        "scores": scores,
    }


def extract_tags(text: str, limit: int = 5) -> list[str]:
    normalized = normalize(text)
    found: list[str] = []
    for term in DOMAIN_TERMS:
        if normalize(term) in normalized and term not in found:
            found.append(term)

    counter = Counter(
        term for term, weight in tokenize(text) if weight == 1.0 and term not in STOP_WORDS
    )
    merged = list(found)
    for term, _ in counter.most_common():
        if len(merged) >= limit:
            break
        if term in GENERIC_BIGRAMS:
            continue
        if any(term in item or item in term for item in merged):
            continue
        merged.append(term)
    return merged[:limit]


def summarize(text: str, max_length: int = 90) -> str:
    sentences = [s.strip() for s in re.split(r"(?<=[。！？!?；;])", str(text or "")) if s.strip()]
    if not sentences:
        return ""
    summary = sentences[0]
    if len(sentences) > 1 and len(summary) < max_length:
        summary += max(sentences[1:], key=len)
    return summary[:max_length] + ("…" if len(summary) > max_length else "")


def safety_check(text: str) -> dict:
    normalized = normalize(text)
    hits = [word for word in SECURITY_WORDS if normalize(word) in normalized]
    return {
        "safe": not hits,
        "hits": hits,
        "message": (
            "检测到可能违反社区规范的内容：" + "、".join(hits) + "。请修改后再发布。"
            if hits
            else "未发现明显违规内容，可以放心发布。"
        ),
    }


def suggest_title(text: str) -> str:
    clean = re.sub(r"\s+", " ", str(text or "").strip())
    if not clean:
        return ""
    first = re.split(r"[。！？!?\n，,；;]", clean)[0] or clean
    title = first[:26] + ("…" if len(first) > 26 else "")
    return title.lstrip("，,、 ")


def polish_content(text: str) -> dict:
    raw = str(text or "")
    issues: list[str] = []
    trimmed = raw.strip()

    if len(trimmed) < 20:
        issues.append("内容偏短，建议补充背景信息，方便同学理解。")
    if trimmed and not re.search(r"[。！？!?…]$", trimmed):
        issues.append("结尾缺少标点，已补全句号。")
    if re.match(r"^[^。！？!?\n]{80,}$", trimmed):
        issues.append("整段太长，已按语义拆分为多段。")
    if re.search(r"(.)\1{3,}", trimmed):
        issues.append("存在连续重复字符，已压缩为一次。")
    if re.search(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f]", raw):
        issues.append("包含不可见控制字符，已清理。")

    text2 = re.sub(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f]", "", raw)
    text2 = re.sub(r"\s+", " ", text2).strip()
    text2 = re.sub(r"(.)\1{3,}", r"\1", text2)
    if text2 and not re.search(r"[。！？!?…]$", text2):
        text2 += "。"

    sentences = [s for s in re.split(r"(?<=[。！？!?；;])", text2) if s]
    paragraphs: list[str] = []
    buffer = ""
    for sentence in sentences:
        buffer += sentence
        if len(buffer) >= 70:
            paragraphs.append(buffer.strip())
            buffer = ""
    if buffer.strip():
        paragraphs.append(buffer.strip())

    content = "\n\n".join(paragraphs)
    return {"content": content, "issues": issues, "changed": content != raw.strip()}


def writing_assistant(text: str) -> dict:
    polished = polish_content(text)
    classification = classify(text)
    tags = extract_tags(text)
    safety = safety_check(text)
    category = CATEGORY_MAP.get(classification["category"], CATEGORY_MAP["life"])

    tips: list[str] = []
    if len(tags) < 2:
        tips.append("建议补充更具体的关键词（如课程名、地点、时间），方便被搜到。")
    if not safety["safe"]:
        tips.append("请删除违规词后再发布。")
    if not polished["issues"]:
        tips.append("文字表达清晰，可以直接发布。")

    return {
        "title": suggest_title(polished["content"]) or suggest_title(text),
        "content": polished["content"],
        "category": category["id"],
        "category_name": category["name"],
        "category_confidence": classification["confidence"],
        "tags": tags or ["校园", "互助"],
        "summary": summarize(polished["content"]),
        "issues": polished["issues"],
        "tips": tips,
        "safety": safety,
        "changed": polished["changed"],
    }


# ---------------- 3. 搭子匹配 ----------------
def jaccard(a: list[str] | None, b: list[str] | None) -> float:
    set_a = {normalize(x) for x in (a or []) if normalize(x)}
    set_b = {normalize(x) for x in (b or []) if normalize(x)}
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def match_buddies(me: dict, users: list[dict]) -> dict:
    my_tags = me.get("tags") or []
    my_bio = _vector(tokenize(me.get("bio") or ""), _Idf)

    results = []
    for user in users:
        if user["id"] == me["id"]:
            continue
        tag_score = jaccard(my_tags, user.get("tags") or [])
        bio_score = _cosine(my_bio, _vector(tokenize(user.get("bio") or ""), _Idf))
        score = tag_score * 0.75 + bio_score * 0.25
        if score <= 0:
            continue
        common = [
            tag
            for tag in my_tags
            if any(normalize(tag) == normalize(other) for other in (user.get("tags") or []))
        ]
        results.append({"user": user, "score": score, "common": common})

    results.sort(key=lambda item: item["score"], reverse=True)
    results = results[:3]

    if not results:
        return {
            "matches": [],
            "message": "暂时没有找到兴趣高度重合的同学。试试在个人资料里多填几个标签"
            "（如“考研”“摄影”“羽毛球”），匹配会更准。",
        }

    matches = []
    for item in results:
        reasons = []
        if item["common"]:
            reasons.append("你们都喜欢「" + "」「".join(item["common"]) + "」")
        if item["user"].get("major") and me.get("major") and item["user"]["major"] == me["major"]:
            reasons.append("同专业，课程节奏相近")
        if item["score"] > 0.5:
            reasons.append("兴趣重合度很高，容易聊到一起")
        elif item["score"] > 0.2:
            reasons.append("有不少共同话题，值得认识一下")
        else:
            reasons.append("兴趣有一定交集，可以先从校园话题聊起")
        matches.append(
            {
                "user": item["user"],
                "score": round(item["score"], 3),
                "reason": "；".join(reasons) + "。",
            }
        )

    return {
        "matches": matches,
        "message": "根据兴趣标签与自我介绍，为你挑出了 " + str(len(matches)) + " 位同频同学。",
    }


def chunk_text(text: str, size: int = 3):
    """把回答切成小块，用于 SSE 流式输出。"""
    for index in range(0, len(text), size):
        yield text[index : index + size]
