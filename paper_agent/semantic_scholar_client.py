"""Semantic Scholar 论文检索客户端。"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from .env_loader import load_env_file
from .models import Paper
from .text_utils import normalize_space

SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"


class SemanticScholarClient:
    """调用 Semantic Scholar Graph API 检索论文元数据。"""

    def __init__(self, user_agent: str, delay_seconds: float = 3.0, retries: int = 3) -> None:
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.retries = retries

    def search(self, topic: str, max_results: int) -> list[Paper]:
        """根据主题检索 Semantic Scholar。"""

        load_env_file()
        fields = ",".join(
            [
                "paperId",
                "title",
                "abstract",
                "authors",
                "year",
                "url",
                "openAccessPdf",
                "externalIds",
                "citationCount",
            ]
        )
        params = {"query": topic, "limit": str(max_results), "fields": fields}
        url = f"{SEMANTIC_SCHOLAR_SEARCH_URL}?{urllib.parse.urlencode(params)}"
        headers = {"User-Agent": self.user_agent}
        api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
        if api_key:
            headers["x-api-key"] = api_key
        request = urllib.request.Request(url, headers=headers)
        payload = json.loads(self._open_with_retry(request).decode("utf-8"))
        return [self._parse_item(item) for item in payload.get("data", []) if item.get("title")]

    def _open_with_retry(self, request: urllib.request.Request) -> bytes:
        """带 429 等待重试的 Semantic Scholar 请求。"""

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            if self.delay_seconds > 0:
                print(f"等待 {self.delay_seconds:g} 秒，避免 Semantic Scholar 限流...")
                time.sleep(self.delay_seconds)
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code != 429 or attempt >= self.retries:
                    raise
                wait_seconds = self._retry_wait_seconds(exc, attempt)
                print(f"Semantic Scholar 返回 429，等待 {wait_seconds:g} 秒后重试...")
                time.sleep(wait_seconds)
        raise RuntimeError(f"Semantic Scholar 请求失败：{last_error}")

    def _retry_wait_seconds(self, exc: urllib.error.HTTPError, attempt: int) -> float:
        """优先使用 Retry-After，没有则递增等待。"""

        retry_after = exc.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), self.delay_seconds)
            except ValueError:
                pass
        return max(10.0 * attempt, self.delay_seconds)

    def _parse_item(self, item: dict) -> Paper:
        """把 Semantic Scholar 返回项转换成统一 Paper 对象。"""

        external_ids = item.get("externalIds") or {}
        arxiv_id = external_ids.get("ArXiv") or f"S2:{item.get('paperId', '')}"
        authors = [author.get("name", "") for author in item.get("authors", []) if author.get("name")]
        open_access_pdf = item.get("openAccessPdf") or {}
        pdf_url = open_access_pdf.get("url") or ""
        year = item.get("year")
        published = str(year) if year else ""
        return Paper(
            arxiv_id=arxiv_id,
            title=normalize_space(item.get("title", "")),
            authors=authors,
            summary=normalize_space(item.get("abstract") or ""),
            published=published,
            updated=published,
            pdf_url=pdf_url,
            page_url=item.get("url") or "",
            source="semantic_scholar",
            citation_count=int(item.get("citationCount") or 0),
        )
