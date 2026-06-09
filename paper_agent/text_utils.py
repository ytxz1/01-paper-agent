"""小型文本处理工具函数。"""

from __future__ import annotations

import re


# 匹配英文关键词：必须以字母开头，后面允许数字、下划线和连字符。
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


def normalize_space(text: str) -> str:
    """把连续空白压缩成单个空格。"""

    # PDF 文本经常有换行、制表符和重复空格，先统一掉能减少后续噪声。
    return re.sub(r"\s+", " ", text).strip()


def keywords(topic: str) -> list[str]:
    """从主题字符串中抽取简单的小写关键词。"""

    # seen 用于去重，result 用于保留关键词第一次出现的顺序。
    seen: set[str] = set()
    result: list[str] = []
    for match in WORD_RE.finditer(topic.lower()):
        word = match.group(0)
        # 过滤太短的词，也跳过重复词，避免一个词把证据分数刷得过高。
        if len(word) < 3 or word in seen:
            continue
        seen.add(word)
        result.append(word)
    return result


def arxiv_search_topic(topic: str) -> str:
    """把用户输入改写成更适合 arXiv 的英文检索词。"""

    return arxiv_search_topics(topic)[0]


def arxiv_search_topics(topic: str) -> list[str]:
    """生成一组适合 arXiv 的候选检索词。"""

    lowered = topic.lower()
    terms: list[str] = []

    # arXiv 主要收录英文论文，中文词需要尽量转成英文检索意图。
    if "rag" in lowered:
        terms.extend(["retrieval augmented generation", "RAG"])
    if "概念" in topic:
        terms.append("concept")
    if "综述" in topic or "文献" in topic:
        terms.extend(["survey", "review"])
    if "方法" in topic:
        terms.append("method")
    if "应用" in topic:
        terms.append("application")

    # 保留用户原本输入中的英文词，去掉中文部分。
    terms.extend(match.group(0) for match in WORD_RE.finditer(topic))

    result: list[str] = []
    seen: set[str] = set()
    for term in terms:
        cleaned = normalize_space(term)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)

    original = normalize_space(topic)
    expanded = " ".join(result)

    candidates: list[str] = []
    if expanded and expanded.lower() != original.lower():
        candidates.append(expanded)
    if original:
        candidates.append(original)
    if "rag" in lowered and "retrieval augmented generation" not in [item.lower() for item in candidates]:
        candidates.append("retrieval augmented generation")
    return _unique_texts(candidates) or [original]


def _unique_texts(values: list[str]) -> list[str]:
    """按顺序去重文本列表。"""

    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = normalize_space(value)
        key = cleaned.lower()
        if cleaned and key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def split_sentences(text: str) -> list[str]:
    """把文本粗略切成句子级片段。"""

    compact = normalize_space(text)
    if not compact:
        return []
    # 这是轻量 MVP 的句子切分方案，适合英文论文摘要和大多数 PDF 正文片段。
    parts = re.split(r"(?<=[.!?])\s+", compact)
    return [part.strip() for part in parts if part.strip()]


def score_text(text: str, terms: list[str]) -> int:
    """通过关键词出现次数给文本片段打分。"""

    lowered = text.lower()
    # 分数越高，说明这个片段和用户主题的字面匹配越强。
    return sum(lowered.count(term) for term in terms)


def safe_filename(value: str) -> str:
    """把任意字符串转换成适合做文件名的片段。"""

    # Windows 和 Unix 对某些字符都比较敏感，所以统一替换成下划线。
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value)
    return cleaned.strip("._") or "paper"
