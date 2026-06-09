"""证据抽取与 Markdown 综述生成。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Evidence, Paper
from .text_utils import keywords, normalize_space, score_text, split_sentences


class ReportWriter:
    """创建证据文件和 Markdown 论文综述。"""

    def collect_evidence(
        self,
        topic: str,
        papers: list[Paper],
        text_by_paper: dict[str, str],
        evidence_per_paper: int,
    ) -> list[Evidence]:
        """为每篇论文收集关键词匹配度最高的证据片段。"""

        terms = keywords(topic)
        all_evidence: list[Evidence] = []
        for paper in papers:
            # 优先使用 PDF 正文；如果 PDF 无法解析，就使用 arXiv 摘要兜底。
            source_text = text_by_paper.get(paper.arxiv_id) or paper.summary
            chunks = split_sentences(source_text)
            # 每个 chunk 保存三元组：(分数, 原始位置, 文本)。
            scored_chunks = [
                (score_text(chunk, terms), index, chunk)
                for index, chunk in enumerate(chunks)
                if score_text(chunk, terms) > 0
            ]
            # 分数高的片段更可能与用户主题相关，因此排在前面。
            scored_chunks.sort(key=lambda item: item[0], reverse=True)
            for score, index, chunk in scored_chunks[:evidence_per_paper]:
                all_evidence.append(
                    Evidence(
                        paper_id=paper.arxiv_id,
                        paper_title=paper.title,
                        source="pdf_text" if paper.arxiv_id in text_by_paper else "abstract",
                        excerpt=normalize_space(chunk)[:700],
                        score=score,
                        location=f"chunk-{index + 1}",
                    )
                )
        return all_evidence

    def save_evidence(self, evidence: list[Evidence], output_path: Path) -> None:
        """把证据片段保存成 JSON。"""

        output_path.write_text(
            json.dumps([item.to_dict() for item in evidence], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def write_report(
        self,
        topic: str,
        papers: list[Paper],
        evidence: list[Evidence],
        output_path: Path,
    ) -> None:
        """写出中文 Markdown 综述报告。"""

        lines: list[str] = [
            f"# 论文综述：{topic}",
            "",
            "## 执行摘要",
            "",
            self._summary(topic, papers, evidence),
            "",
            "## 关键证据",
            "",
        ]
        if evidence:
            for item in evidence:
                source_name = "PDF 正文" if item.source == "pdf_text" else "摘要"
                lines.extend(
                    [
                        f"- [{item.paper_id}] {item.excerpt}",
                        f"  - 来源：{item.paper_title}；来源类型：{source_name}；位置：{item.location}；分数={item.score}",
                    ]
                )
        else:
            lines.append("- 没有抽取到匹配证据。可以尝试扩大主题范围，或安装 PDF 解析依赖。")
        lines.extend(["", "## 论文列表", ""])
        for paper in papers:
            authors = ", ".join(paper.authors[:5])
            if len(paper.authors) > 5:
                authors += ", et al."
            lines.extend(
                [
                    f"### [{paper.arxiv_id}] {paper.title}",
                    "",
                    f"- 作者：{authors or '未知'}",
                    f"- 发布时间：{paper.published}",
                    f"- PDF: {paper.pdf_url}",
                    f"- 页面：{paper.page_url}",
                    f"- 摘要：{paper.summary}",
                    "",
                ]
            )
        lines.extend(
            [
                "## 局限性",
                "",
                "- 当前 MVP 使用关键词计分，因此可能漏掉表达方式不同但语义相关的证据。",
                "- 当前综述是抽取式和保守式的，不会编造论文之外的结论。",
                "- 如果需要更深入的归纳、比较和批判性分析，可以接入 LLM 写作模块，并让它读取 `papers.json` 与 `evidence.json`。",
            ]
        )
        output_path.write_text("\n".join(lines), encoding="utf-8")

    def _summary(self, topic: str, papers: list[Paper], evidence: list[Evidence]) -> str:
        """创建一个确定性的中文摘要段落。"""

        return (
            f"本次运行围绕 `{topic}` 在 arXiv 上检索论文，并选择了 {len(papers)} 篇论文进入分析。"
            f"Agent 共抽取 {len(evidence)} 条证据片段，并把它们整理成可追溯的 Markdown 综述。"
            "关键证据部分的每条内容都带有 arXiv 论文编号，便于回到原始论文核查。"
        )
