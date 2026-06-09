"""对论文 Agent 输出产物做简单评测。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class EvaluationResult:
    """一次评测的结果。"""

    # 整体是否通过。
    passed: bool
    # 每个检查项的布尔结果。
    checks: dict[str, bool]

    def to_text(self) -> str:
        """把评测结果格式化成中文终端输出。"""

        lines = [f"整体是否通过：{'通过' if self.passed else '未通过'}"]
        for name, ok in self.checks.items():
            lines.append(f"- {CHECK_NAMES.get(name, name)}：{'通过' if ok else '失败'}")
        return "\n".join(lines)


CHECK_NAMES = {
    "report_exists": "已生成 report.md",
    "report_has_citations": "报告包含引用标记",
    "papers_saved": "已保存论文元数据",
    "evidence_saved": "已保存证据文件",
    "evidence_has_items": "至少抽取一条证据",
}


class Evaluator:
    """评测输出目录是否包含预期产物。"""

    def evaluate(self, output_dir: Path) -> EvaluationResult:
        """执行基础产物检查和内容检查。"""

        # 三个核心产物：综述、论文元数据、证据片段。
        report_path = output_dir / "report.md"
        papers_path = output_dir / "papers.json"
        evidence_path = output_dir / "evidence.json"

        report_text = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        papers = self._load_json_list(papers_path)
        evidence = self._load_json_list(evidence_path)

        # 这里是 MVP 级评测：先确认关键文件存在，再确认报告具备基本引用能力。
        checks = {
            "report_exists": report_path.exists(),
            "report_has_citations": "[" in report_text and "]" in report_text,
            "papers_saved": len(papers) > 0,
            "evidence_saved": evidence_path.exists(),
            "evidence_has_items": len(evidence) > 0,
        }
        return EvaluationResult(passed=all(checks.values()), checks=checks)

    def _load_json_list(self, path: Path) -> list[dict]:
        """读取 JSON 列表；文件不存在或格式错误时返回空列表。"""

        if not path.exists():
            return []
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return value if isinstance(value, list) else []
