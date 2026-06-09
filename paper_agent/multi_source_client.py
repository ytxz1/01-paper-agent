"""多源论文检索与元数据融合。"""

from __future__ import annotations

import socket
import urllib.error

from .arxiv_client import ArxivClient
from .models import Paper
from .openalex_client import OpenAlexClient
from .semantic_scholar_client import SemanticScholarClient


class MultiSourcePaperClient:
    """依次调用 arXiv、Semantic Scholar、OpenAlex，并融合结果。"""

    def __init__(
        self,
        user_agent: str,
        arxiv_delay_seconds: float,
        arxiv_retries: int,
        sources: list[str],
    ) -> None:
        self.sources = sources
        self.clients = {
            "arxiv": ArxivClient(user_agent, delay_seconds=arxiv_delay_seconds, retries=arxiv_retries),
            "semantic_scholar": SemanticScholarClient(
                user_agent,
                delay_seconds=arxiv_delay_seconds,
                retries=arxiv_retries,
            ),
            "openalex": OpenAlexClient(user_agent),
        }

    def search(self, topic: str, max_results: int) -> list[Paper]:
        """多源检索并按标题去重。"""

        all_papers: list[Paper] = []
        for source in self.sources:
            client = self.clients.get(source)
            if client is None:
                print(f"跳过未知论文源：{source}")
                continue
            try:
                print(f"开始检索论文源：{source}")
                papers = client.search(topic, max_results)
            except (TimeoutError, socket.timeout, urllib.error.URLError, RuntimeError) as exc:
                print(f"论文源 {source} 检索失败，继续尝试下一个来源：{exc}")
                continue
            print(f"论文源 {source} 返回 {len(papers)} 篇")
            all_papers.extend(papers)
            if len(self._dedupe(all_papers)) >= max_results:
                break
        return self._dedupe(all_papers)[:max_results]

    def _dedupe(self, papers: list[Paper]) -> list[Paper]:
        """按标题去重。"""

        merged: dict[str, Paper] = {}
        for paper in papers:
            key = self._key(paper)
            existing = merged.get(key)
            merged[key] = paper if existing is None else self._merge(existing, paper)
        return list(merged.values())

    def _key(self, paper: Paper) -> str:
        """生成去重键。"""

        title_key = " ".join(paper.title.lower().split())
        return title_key or paper.arxiv_id.lower()

    def _merge(self, first: Paper, second: Paper) -> Paper:
        """融合两个来源中的同一篇论文。"""

        preferred_id = first.arxiv_id if first.source == "arxiv" else second.arxiv_id
        return Paper(
            arxiv_id=preferred_id,
            title=first.title or second.title,
            authors=first.authors or second.authors,
            summary=first.summary or second.summary,
            published=first.published or second.published,
            updated=first.updated or second.updated,
            pdf_url=first.pdf_url or second.pdf_url,
            page_url=first.page_url or second.page_url,
            source=f"{first.source}+{second.source}",
            citation_count=max(first.citation_count, second.citation_count),
        )
