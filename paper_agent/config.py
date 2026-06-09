"""论文研读 Agent 的运行配置。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AgentConfig:
    """一次 Agent 运行所需的配置。"""

    topic: str
    output_dir: Path
    max_results: int = 5
    evidence_per_paper: int = 3
    user_agent: str = "paper-agent/0.1.0 (local educational project)"
    arxiv_delay_seconds: float = 3.0
    '''
    每次请求arXiv时的延迟时间（秒）。
    '''
    arxiv_retries: int = 3
    sources: list[str] = field(default_factory=lambda: ["arxiv", "semantic_scholar", "openalex"])
    writer: str = "rule"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_base_url: str = "https://api.deepseek.com"
    max_llm_evidence: int = 20

    @property
    def pdf_dir(self) -> Path:
        """下载 PDF 的保存目录。"""

        return self.output_dir / "pdfs"

    @property
    def text_dir(self) -> Path:
        """PDF 正文解析结果的保存目录。"""

        return self.output_dir / "texts"
