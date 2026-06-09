"""PDF 文本抽取。"""

from __future__ import annotations

from pathlib import Path


class PdfReader:
    """使用可选的 PyMuPDF 依赖从 PDF 中抽取文本。"""

    def extract_text(self, pdf_path: Path) -> str:
        """返回 PDF 文本；如果依赖不可用，则返回空字符串。"""

        try:
            import fitz
        except ImportError:
            # PyMuPDF 是可选依赖。没有安装时，项目仍可使用摘要生成报告。
            return ""

        pages: list[str] = []
        with fitz.open(pdf_path) as document:
            for page_index, page in enumerate(document, start=1):
                # "text" 模式会返回较朴素的纯文本，适合后续做证据切片。
                text = page.get_text("text")
                if text.strip():
                    # 给每页加页码标记，方便人类回溯证据来源。
                    pages.append(f"\n[Page {page_index}]\n{text}")
        return "\n".join(pages).strip()
