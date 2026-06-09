"""读取 .env 文件中的本地隐私配置。"""

from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: Path | None = None) -> None:
    """把 .env 文件中的键值加载到环境变量中。"""

    env_path = path or find_env_file()
    if env_path is None:
        return
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        # 空行和注释行不参与解析。
        if not line or line.startswith("#"):
            continue
        # 只处理 KEY=VALUE 这种最常见的 .env 写法。
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())
        if not key:
            continue
        # 已经存在的系统环境变量优先级更高，避免 .env 意外覆盖外部配置。
        os.environ.setdefault(key, value)


def _strip_quotes(value: str) -> str:
    """去掉 .env 值两侧成对的单引号或双引号。"""

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def find_env_file() -> Path | None:
    """查找最适合当前运行场景的 .env 文件。"""

    # 直接运行 paper_agent/cli.py 时，终端当前目录可能不是项目根目录。
    # 因此除了当前目录，还要检查 env_loader.py 所在包的上一级项目目录。
    project_root = Path(__file__).resolve().parents[1]
    candidates = [Path.cwd() / ".env", project_root / ".env"]

    # 如果用户在项目子目录中运行，也沿着当前目录向上查找 .env。
    for parent in Path.cwd().resolve().parents:
        candidates.append(parent / ".env")

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved
    return None
