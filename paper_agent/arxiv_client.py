"""arXiv API 访问与 PDF 下载。"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from hashlib import sha256
from pathlib import Path

from .models import Paper
from .text_utils import arxiv_search_topics, normalize_space, safe_filename

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
ARXIV_API_URL = "https://export.arxiv.org/api/query"


class ArxivClient:
    """面向 arXiv Atom API 的轻量客户端。"""

    def __init__(self, user_agent: str, delay_seconds: float = 3.0, retries: int = 3) -> None:
        self.user_agent = user_agent
        self.delay_seconds = delay_seconds
        self.retries = retries

    def search(self, topic: str, max_results: int) -> list[Paper]:
        """根据研究主题检索 arXiv 论文。"""

        last_error: Exception | None = None
        for index, candidate in enumerate(arxiv_search_topics(topic), start=1):
            if index > 1:
                print(f"改用 arXiv 候选检索词重试：{candidate}")
            try:
                papers = self._search_once(candidate, max_results)
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                last_error = exc
                print(f"arXiv 查询失败，继续尝试下一个检索词：{exc}")
                continue
            if papers:
                return papers
            print(f"arXiv 查询没有结果：{candidate}")
        if last_error is not None:
            raise RuntimeError(f"arXiv 多次查询失败，最后一次错误：{last_error}") from last_error
        return []

    def _search_once(self, topic: str, max_results: int) -> list[Paper]:
        """执行一次 arXiv 查询。"""

        cached = self._load_cache(topic, max_results)
        if cached is not None:
            print(f"使用 arXiv 本地缓存：{topic}")
            return cached

        params = {
            "search_query": f"all:{topic}",
            "start": "0",
            "max_results": str(max_results),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        url = f"{ARXIV_API_URL}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        xml_bytes = self._open_with_retry(request)
        papers = self._parse_feed(xml_bytes)
        self._save_cache(topic, max_results, papers)
        return papers

    def _open_with_retry(self, request: urllib.request.Request) -> bytes:
        """带限流等待和重试的 arXiv 请求。"""

        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            if self.delay_seconds > 0:
                print(f"等待 {self.delay_seconds:g} 秒，避免 arXiv 限流...")
                time.sleep(self.delay_seconds)
            try:
                with urllib.request.urlopen(request, timeout=90) as response:
                    return response.read()
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code != 429 or attempt >= self.retries:
                    raise
                wait_seconds = self._retry_wait_seconds(exc, attempt)
                print(f"arXiv 返回 429 Too Many Requests，等待 {wait_seconds:g} 秒后重试...")
                time.sleep(wait_seconds)
            except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise
                wait_seconds = 5 * attempt
                print(f"arXiv 连接暂时失败，等待 {wait_seconds:g} 秒后重试：{exc}")
                time.sleep(wait_seconds)
        raise RuntimeError(f"arXiv 请求失败：{last_error}")

    def _retry_wait_seconds(self, exc: urllib.error.HTTPError, attempt: int) -> float:
        """从 Retry-After 响应头读取等待时间，没有则使用递增等待。"""

        retry_after = exc.headers.get("Retry-After")
        if retry_after:
            try:
                return max(float(retry_after), self.delay_seconds)
            except ValueError:
                pass
        return max(10.0 * attempt, self.delay_seconds)

    def download_pdf(self, paper: Paper, pdf_dir: Path) -> Path:
        """下载单篇论文 PDF，并返回本地路径。"""

        if not paper.pdf_url:
            raise RuntimeError(f"论文没有可下载 PDF：{paper.title}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
        target = pdf_dir / f"{safe_filename(paper.arxiv_id)}.pdf"
        if target.exists():
            print(f"使用已下载 PDF：{target}")
            return target
        request = urllib.request.Request(paper.pdf_url, headers={"User-Agent": self.user_agent})
        if self.delay_seconds > 0:
            print(f"等待 {self.delay_seconds:g} 秒后下载 PDF，避免限流...")
            time.sleep(self.delay_seconds)
        with urllib.request.urlopen(request, timeout=90) as response:
            target.write_bytes(response.read())
        return target

    def save_papers(self, papers: list[Paper], output_path: Path) -> None:
        """把论文元数据保存成易读的 JSON 文件。"""

        output_path.write_text(
            json.dumps([paper.to_dict() for paper in papers], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _parse_feed(self, xml_bytes: bytes) -> list[Paper]:
        """把 arXiv Atom feed 解析成 Paper 对象列表。"""

        root = ET.fromstring(xml_bytes)
        papers: list[Paper] = []
        for entry in root.findall("atom:entry", ATOM_NS):
            paper = self._parse_entry(entry)
            if paper is not None:
                papers.append(paper)
        return papers

    def _parse_entry(self, entry: ET.Element) -> Paper | None:
        """解析单个 Atom entry。"""

        raw_id = self._text(entry, "atom:id")
        title = normalize_space(self._text(entry, "atom:title"))
        summary = normalize_space(self._text(entry, "atom:summary"))
        published = self._text(entry, "atom:published")
        updated = self._text(entry, "atom:updated")
        authors = [
            normalize_space(author.findtext("atom:name", default="", namespaces=ATOM_NS))
            for author in entry.findall("atom:author", ATOM_NS)
        ]
        pdf_url = self._find_pdf_url(entry)
        if not raw_id or not title or not pdf_url:
            return None
        arxiv_id = raw_id.rstrip("/").split("/")[-1]
        return Paper(
            arxiv_id=arxiv_id,
            title=title,
            authors=[author for author in authors if author],
            summary=summary,
            published=published,
            updated=updated,
            pdf_url=pdf_url,
            page_url=raw_id,
            source="arxiv",
        )

    def _find_pdf_url(self, entry: ET.Element) -> str:
        """从单个 Atom entry 中寻找 PDF 链接。"""

        for link in entry.findall("atom:link", ATOM_NS):
            title = link.attrib.get("title", "")
            href = link.attrib.get("href", "")
            if title == "pdf" and href:
                return href
        return ""

    def _text(self, entry: ET.Element, path: str) -> str:
        """读取 XML 子节点文本，找不到时返回空字符串。"""

        return entry.findtext(path, default="", namespaces=ATOM_NS)

    def _cache_path(self, topic: str, max_results: int) -> Path:
        """生成 arXiv 查询缓存文件路径。"""

        cache_key = sha256(f"{topic}|{max_results}".encode("utf-8")).hexdigest()[:16]
        return Path(".cache") / "arxiv" / f"{cache_key}.json"

    def _load_cache(self, topic: str, max_results: int) -> list[Paper] | None:
        """读取 arXiv 查询缓存。"""

        cache_path = self._cache_path(topic, max_results)
        if not cache_path.exists():
            return None
        try:
            raw_items = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
        if not isinstance(raw_items, list):
            return None
        return [Paper(**item) for item in raw_items if isinstance(item, dict)]

    def _save_cache(self, topic: str, max_results: int, papers: list[Paper]) -> None:
        """保存 arXiv 查询缓存，减少反复请求造成的 429。"""

        cache_path = self._cache_path(topic, max_results)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(
            json.dumps([paper.to_dict() for paper in papers], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
