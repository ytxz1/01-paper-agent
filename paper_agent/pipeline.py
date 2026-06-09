"""论文研读 Agent 的端到端流水线。"""

from __future__ import annotations

import json
from pathlib import Path

from .arxiv_client import ArxivClient
from .config import AgentConfig
from .deepseek_client import DeepSeekClient
from .llm_writer import LlmReportWriter
from .multi_source_client import MultiSourcePaperClient
from .pdf_reader import PdfReader
from .report_writer import ReportWriter
from .text_utils import safe_filename


class PaperAgentPipeline:
    """编排检索、下载、解析、证据抽取和报告生成。"""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self.search_client = MultiSourcePaperClient(
            user_agent=config.user_agent,
            arxiv_delay_seconds=config.arxiv_delay_seconds,
            arxiv_retries=config.arxiv_retries,
            sources=config.sources,
        )
        # 这里继续复用 ArxivClient 的 PDF 下载方法，因为它只是通用 URL 下载器。
        self.downloader = ArxivClient(
            config.user_agent,
            delay_seconds=config.arxiv_delay_seconds,
            retries=config.arxiv_retries,
        )
        self.pdf_reader = PdfReader()
        self.writer = ReportWriter()

    def run(self) -> Path:
        """执行完整工作流，并返回最终报告路径。"""

        self._prepare_output()
        print(f"开始多源检索：主题={self.config.topic}，数量={self.config.max_results}")
        print(f"检索源：{', '.join(self.config.sources)}")
        papers = self.search_client.search(self.config.topic, self.config.max_results)
        if not papers:
            raise RuntimeError("所有论文检索源都没有返回结果，请检查网络或更换检索源。")
        self._save_papers(papers, self.config.output_dir / "papers.json")
        print(f"已保存论文元数据：{len(papers)} 篇")

        text_by_paper: dict[str, str] = {}
        for paper in papers:
            print(f"处理论文：{paper.arxiv_id} - {paper.title}（来源：{paper.source}）")
            try:
                pdf_path = self.downloader.download_pdf(paper, self.config.pdf_dir)
                text = self.pdf_reader.extract_text(pdf_path)
            except Exception as exc:
                print(f"PDF 下载或解析失败，将使用摘要作为证据来源：{paper.arxiv_id}；错误：{exc}")
                text = ""
            if text:
                text_by_paper[paper.arxiv_id] = text
                text_path = self.config.text_dir / f"{safe_filename(paper.arxiv_id)}.txt"
                text_path.write_text(text, encoding="utf-8")
                print(f"已解析正文：{text_path}")
            else:
                print(f"未解析出正文，将使用摘要作为证据来源：{paper.arxiv_id}")

        print("开始抽取证据片段")
        evidence = self.writer.collect_evidence(
            topic=self.config.topic,
            papers=papers,
            text_by_paper=text_by_paper,
            evidence_per_paper=self.config.evidence_per_paper,
        )
        self.writer.save_evidence(evidence, self.config.output_dir / "evidence.json")
        print(f"已保存证据片段：{len(evidence)} 条")

        report_path = self.config.output_dir / "report.md"
        if self.config.writer == "deepseek":
            print(f"正在调用 DeepSeek 生成中文综述：模型={self.config.deepseek_model}")
            client = DeepSeekClient.from_env(
                base_url=self.config.deepseek_base_url,
                model=self.config.deepseek_model,
            )
            markdown = LlmReportWriter(client, self.config.max_llm_evidence).write_markdown(
                self.config.topic,
                papers,
                evidence,
            )
            report_path.write_text(markdown, encoding="utf-8")
        else:
            self.writer.write_report(self.config.topic, papers, evidence, report_path)
        print(f"已写入 Markdown 综述：{report_path}")
        return report_path

    def _prepare_output(self) -> None:
        """创建流水线需要的输出目录。"""

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        self.config.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.config.text_dir.mkdir(parents=True, exist_ok=True)

    def _save_papers(self, papers: list, output_path: Path) -> None:
        """保存多源论文元数据。"""

        output_path.write_text(
            json.dumps([paper.to_dict() for paper in papers], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
