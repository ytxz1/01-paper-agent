"""基于 DeepSeek 的大模型综述写作器。"""

from __future__ import annotations

import json

from .deepseek_client import DeepSeekClient
from .models import Evidence, Paper


class LlmReportWriter:
    """把论文元数据和证据片段交给 DeepSeek，生成中文综述。"""

    def __init__(self, client: DeepSeekClient, max_evidence: int) -> None:
        self.client = client
        self.max_evidence = max_evidence

    def write_markdown(self, topic: str, papers: list[Paper], evidence: list[Evidence]) -> str:
        """生成中文 Markdown 综述文本。"""

        system_prompt = (
            "你是严谨的学术论文综述助手。"
            "你必须只依据用户提供的论文元数据和证据片段写作，不能编造未提供的论文、实验结果或结论。"
            "每个关键结论都必须包含 arXiv ID 形式的引用，例如 [2401.00001]。"
            "请使用中文输出 Markdown。"
        )
        user_prompt = self._build_prompt(topic, papers, evidence)
        return self.client.chat(system_prompt, user_prompt)

    def _build_prompt(self, topic: str, papers: list[Paper], evidence: list[Evidence]) -> str:
        """构造传给 DeepSeek 的提示词。"""

        paper_payload = [
            {
                "arxiv_id": paper.arxiv_id,
                "title": paper.title,
                "authors": paper.authors[:8],
                "published": paper.published,
                "summary": paper.summary,
            }
            for paper in papers
        ]
        evidence_payload = [
            {
                "paper_id": item.paper_id,
                "paper_title": item.paper_title,
                "source": item.source,
                "location": item.location,
                "excerpt": item.excerpt,
                "score": item.score,
            }
            for item in evidence[: self.max_evidence]
        ]
        return (
            f"研究主题：{topic}\n\n"
            "请根据下面的论文和证据，生成一份结构清晰的中文 Markdown 论文综述。\n"
            "必须包含这些小节：\n"
            "1. 执行摘要\n"
            "2. 研究背景\n"
            "3. 主要方法与技术路线\n"
            "4. 关键发现\n"
            "5. 不同论文之间的比较\n"
            "6. 局限性\n"
            "7. 后续研究方向\n"
            "8. 论文列表\n\n"
            "写作要求：\n"
            "- 每条重要判断都要引用 arXiv ID，例如 [2401.00001]。\n"
            "- 如果证据不足，请明确写出“证据不足”，不要猜测。\n"
            "- 不要输出未提供论文之外的引用。\n"
            "- 语言要像学术综述，但保持清晰易读。\n\n"
            "论文元数据 JSON：\n"
            f"{json.dumps(paper_payload, ensure_ascii=False, indent=2)}\n\n"
            "证据片段 JSON：\n"
            f"{json.dumps(evidence_payload, ensure_ascii=False, indent=2)}"
        )
