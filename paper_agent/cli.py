"""论文研读 Agent 的命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 直接运行 paper_agent/cli.py 时，Python 不知道它属于 paper_agent 包。
# 这里把项目根目录加入 sys.path，让直接运行文件和 -m 运行都能工作。
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from paper_agent.config import AgentConfig
    from paper_agent.evaluator import Evaluator
    from paper_agent.pipeline import PaperAgentPipeline
else:
    from .config import AgentConfig
    from .evaluator import Evaluator
    from .pipeline import PaperAgentPipeline


def build_parser() -> argparse.ArgumentParser:
    """构建顶层命令行解析器。"""

    parser = argparse.ArgumentParser(description="检索、阅读并总结 arXiv 论文。", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.title = "子命令"
    subparsers.description = "可用命令"

    run_parser = subparsers.add_parser("run", help="运行论文综述 Agent。", add_help=False)
    run_parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
    run_parser._positionals.title = "位置参数"
    run_parser._optionals.title = "选项"
    run_parser.add_argument("topic", help="要在 arXiv 上检索的研究主题。")
    run_parser.add_argument("--max-results", type=int, default=10, help="最多检索多少篇论文。")
    run_parser.add_argument("--evidence-per-paper", type=int, default=3, help="每篇论文最多抽取几条证据。")
    run_parser.add_argument("--output", type=Path, default=Path("runs/latest"), help="输出目录。")
    run_parser.add_argument(
        "--writer",
        choices=["rule", "deepseek"],
        default="rule",
        help="报告写作方式：rule 为规则式写作，deepseek 为调用 DeepSeek API。",
    )
    run_parser.add_argument("--deepseek-model", default="deepseek-v4-flash", help="DeepSeek 模型名。")
    run_parser.add_argument("--deepseek-base-url", default="https://api.deepseek.com", help="DeepSeek API 基础地址。")
    run_parser.add_argument("--max-llm-evidence", type=int, default=20, help="最多传给 DeepSeek 的证据条数。")
    run_parser.add_argument("--arxiv-delay-seconds", type=float, default=3.0, help="每次 arXiv 请求前等待几秒，避免 429 限流。")
    run_parser.add_argument("--arxiv-retries", type=int, default=3, help="arXiv 请求失败或限流时最多重试几次。")
    run_parser.add_argument(
        "--sources",
        default="arxiv,semantic_scholar,openalex",
        help="论文检索源，逗号分隔：arxiv,semantic_scholar,openalex。",
    )

    eval_parser = subparsers.add_parser("evaluate", help="评测某个输出目录。", add_help=False)
    eval_parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
    eval_parser._positionals.title = "位置参数"
    eval_parser._optionals.title = "选项"
    eval_parser.add_argument("output", type=Path, help="run 命令生成的输出目录。")

    return parser


def run_agent_from_args(args: argparse.Namespace) -> int:
    """根据命令行参数运行 Agent。"""

    config = AgentConfig(
        topic=args.topic,
        output_dir=args.output,
        max_results=args.max_results,
        evidence_per_paper=args.evidence_per_paper,
        writer=args.writer,
        deepseek_model=args.deepseek_model,
        deepseek_base_url=args.deepseek_base_url,
        max_llm_evidence=args.max_llm_evidence,
        arxiv_delay_seconds=args.arxiv_delay_seconds,
        arxiv_retries=args.arxiv_retries,
        sources=_parse_sources(args.sources),
    )
    try:
        report_path = PaperAgentPipeline(config).run()
    except Exception as exc:
        print("运行失败，请根据下面的错误信息定位问题。")
        if "429" in str(exc) or "Too Many Requests" in str(exc):
            print("arXiv 正在限流。请等 1-3 分钟后再试，或把检索数量设为 1。")
        print(f"错误信息：{exc}")
        return 1
    print(f"综述报告已生成：{report_path}")
    return 0


def interactive_main() -> int:
    """VSCode 直接运行 cli.py 时使用的交互模式。"""

    project_root = Path(__file__).resolve().parents[1]
    print("论文研读 Agent 交互模式")
    print("直接回车会使用括号中的默认值。")
    topic = _ask_required("请输入研究主题，例如 retrieval augmented generation：")
    max_results = _ask_int("最多检索多少篇论文", default=3)
    evidence_per_paper = _ask_int("每篇论文最多抽取几条证据", default=3)
    output = _ask_text("输出目录", default=str(project_root / "runs" / "interactive"))
    sources_text = _ask_text("论文检索源，可选 arxiv,semantic_scholar,openalex", default="arxiv,semantic_scholar,openalex")
    writer = _ask_choice("报告写作方式", choices=["rule", "deepseek"], default="rule")

    args = argparse.Namespace(
        command="run",
        topic=topic,
        max_results=max_results,
        evidence_per_paper=evidence_per_paper,
        output=Path(output),
        writer=writer,
        deepseek_model="deepseek-v4-flash",
        deepseek_base_url="https://api.deepseek.com",
        max_llm_evidence=20,
        arxiv_delay_seconds=3.0,
        arxiv_retries=3,
        sources=_parse_sources(sources_text),
    )
    return run_agent_from_args(args)


def _ask_required(prompt: str) -> str:
    """反复询问，直到用户输入非空内容。"""

    while True:
        value = input(prompt + " ").strip()
        if value:
            return value
        print("研究主题不能为空，请重新输入。")


def _ask_text(prompt: str, default: str) -> str:
    """询问文本参数，空输入时使用默认值。"""

    value = input(f"{prompt}（默认：{default}）：").strip()
    return value or default


def _ask_int(prompt: str, default: int) -> int:
    """询问整数参数，空输入时使用默认值。"""

    while True:
        value = input(f"{prompt}（默认：{default}）：").strip()
        if not value:
            return default
        try:
            number = int(value)
        except ValueError:
            print("请输入整数。")
            continue
        if number <= 0:
            print("请输入大于 0 的整数。")
            continue
        return number


def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
    """询问选项参数，空输入时使用默认值。"""

    choices_text = "/".join(choices)
    while True:
        value = input(f"{prompt}（{choices_text}，默认：{default}）：").strip().lower()
        if not value:
            return default
        if value in choices:
            return value
        print(f"请输入以下选项之一：{choices_text}")


def _parse_sources(value: str | list[str]) -> list[str]:
    """解析逗号分隔的论文源列表。"""

    if isinstance(value, list):
        return value or ["arxiv", "semantic_scholar", "openalex"]
    sources = [item.strip() for item in value.split(",") if item.strip()]
    return sources or ["arxiv", "semantic_scholar", "openalex"]


def main(argv: list[str] | None = None) -> int:
    """运行命令行程序。"""

    if argv is None and len(sys.argv) == 1:
        return interactive_main()
    if argv == []:
        return interactive_main()

    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_agent_from_args(args)

    if args.command == "evaluate":
        result = Evaluator().evaluate(args.output)
        print(result.to_text())
        return 0 if result.passed else 1

    parser.error(f"未知命令：{args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
