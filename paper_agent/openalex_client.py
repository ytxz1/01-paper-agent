"""OpenAlex 论文检索客户端。"""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from .env_loader import load_env_file
from .models import Paper
from .text_utils import normalize_space

OPENALEX_WORKS_URL = "https://api.openalex.org/works"


class OpenAlexClient:
    """调用 OpenAlex Works API 检索论文元数据。"""

    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent

    def search(self, topic: str, max_results: int) -> list[Paper]:
        """根据主题检索 OpenAlex Works。"""

        load_env_file()
        params = {
            "search": topic,
            "per-page": str(max_results),
            "select": ",".join(
                [
                    "id",
                    "title",
                    "display_name",
                    "authorships",
                    "publication_date",
                    "abstract_inverted_index",
                    "primary_location",
                    "doi",
                    "cited_by_count",
                ]
            ),
        }
        api_key = os.getenv("OPENALEX_API_KEY", "").strip()
        if api_key:
            params["api_key"] = api_key
        url = f"{OPENALEX_WORKS_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(request, timeout=90) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [self._parse_item(item) for item in payload.get("results", []) if item.get("title") or item.get("display_name")]

    def _parse_item(self, item: dict) -> Paper:
        """把 OpenAlex 返回项转换成统一 Paper 对象。"""

        location = item.get("primary_location") or {}
        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author") or {}
            name = author.get("display_name")
            if name:
                authors.append(name)
        title = item.get("title") or item.get("display_name") or ""
        page_url = location.get("landing_page_url") or item.get("id") or ""
        return Paper(
            arxiv_id=self._work_id(item),
            title=normalize_space(title),
            authors=authors,
            summary=normalize_space(self._abstract(item.get("abstract_inverted_index") or {})),
            published=item.get("publication_date") or "",
            updated=item.get("publication_date") or "",
            pdf_url=location.get("pdf_url") or "",
            page_url=page_url,
            source="openalex",
            citation_count=int(item.get("cited_by_count") or 0),
        )

    def _work_id(self, item: dict) -> str:
        """生成 OpenAlex 论文标识。"""

        raw_id = item.get("id") or ""
        return raw_id.rstrip("/").split("/")[-1] or "openalex-work"

    def _abstract(self, inverted_index: dict[str, list[int]]) -> str:
        """把 OpenAlex 的 inverted index 摘要还原成文本。"""

        words: list[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for position in positions:
                words.append((position, word))
        return " ".join(word for _, word in sorted(words))
