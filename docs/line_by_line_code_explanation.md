# 全部代码逐行解释

这份文档专门解释项目中的所有 Python 代码。它和 `code_walkthrough.md` 不一样：`code_walkthrough.md` 偏结构说明，这份文档偏逐行解释，适合你打开源码时对照阅读。

说明：

- 本文覆盖 `paper_agent/` 下的全部源码文件。
- 本文覆盖 `tests/test_text_utils.py`。
- 对连续 import、字段声明、参数声明这类代码，会按顺序逐行解释。
- 对循环、异常处理、API 请求、数据融合这类关键逻辑，会解释每一行为什么存在。

## 1. paper_agent/__init__.py

```python
"""论文研读 Agent 的 Python 包入口。"""
```

这一行是包级文档字符串。它说明 `paper_agent` 是论文研读 Agent 的 Python 包。

```python
__all__ = ["__version__"]
```

这一行声明当别人写 `from paper_agent import *` 时，只导出 `__version__`。

```python
__version__ = "0.1.0"
```

这一行保存项目版本号。

## 2. paper_agent/models.py

```python
"""论文研读 Agent 使用的数据模型。"""
```

模块文档字符串，说明这个文件存放数据模型。

```python
from __future__ import annotations
```

启用延迟类型注解。这样 Python 不会在运行时立刻解析所有类型，有利于兼容复杂类型标注。

```python
from dataclasses import asdict, dataclass
```

导入 `dataclass` 和 `asdict`。`dataclass` 用来定义数据对象，`asdict` 用来把对象转成字典。

```python
from typing import Any
```

导入 `Any`，用于表示字典里的值可以是任意类型。

```python
@dataclass(slots=True)
```

把下面的 `Paper` 类变成数据类。`slots=True` 可以减少内存占用，并防止随意添加不存在的字段。

```python
class Paper:
```

定义论文元数据类。

```python
"""一篇论文的统一元数据。"""
```

说明这个类不是只服务 arXiv，而是统一表示 arXiv、Semantic Scholar、OpenAlex 返回的论文。

```python
arxiv_id: str
```

论文标识。名字叫 `arxiv_id` 是为了兼容早期代码；非 arXiv 来源会填入 Semantic Scholar ID 或 OpenAlex Work ID。

```python
title: str
```

论文标题。

```python
authors: list[str]
```

作者列表。

```python
summary: str
```

论文摘要。

```python
published: str
```

论文发布时间。

```python
updated: str
```

论文更新时间。部分来源没有更新时间，就使用发布时间或空字符串。

```python
pdf_url: str
```

PDF 下载地址。如果数据源没有开放 PDF，这里会是空字符串。

```python
page_url: str
```

论文详情页地址。

```python
source: str = "arxiv"
```

论文来源，默认是 `arxiv`。多源检索时可能是 `semantic_scholar`、`openalex` 或融合后的来源字符串。

```python
citation_count: int = 0
```

引用次数。arXiv 通常没有引用数字，Semantic Scholar 和 OpenAlex 会尽量提供。

```python
def to_dict(self) -> dict[str, Any]:
```

定义对象转字典的方法。

```python
"""把论文对象转换成可以写入 JSON 的字典。"""
```

说明这个方法的用途。

```python
return asdict(self)
```

调用 dataclass 的 `asdict`，把整个 `Paper` 对象变成普通字典，方便写入 `papers.json`。

```python
@dataclass(slots=True)
```

把下面的 `Evidence` 类变成数据类。

```python
class Evidence:
```

定义证据片段类。

```python
"""可以支撑综述结论的一条论文证据。"""
```

说明一条 `Evidence` 对应一段可引用文本。

```python
paper_id: str
```

证据来自哪篇论文。

```python
paper_title: str
```

证据对应的论文标题。

```python
source: str
```

证据来源，例如 `pdf_text` 或 `abstract`。

```python
excerpt: str
```

具体证据文本。

```python
score: int
```

关键词匹配分数，分数越高说明越贴近主题。

```python
location: str
```

证据位置。当前实现用 `chunk-数字` 表示。

```python
def to_dict(self) -> dict[str, Any]:
```

定义证据对象转字典的方法。

```python
"""把证据对象转换成可以写入 JSON 的字典。"""
```

说明这个方法用于 JSON 保存。

```python
return asdict(self)
```

把 `Evidence` 对象转成普通字典。

## 3. paper_agent/config.py

```python
"""论文研读 Agent 的运行配置。"""
```

说明这个文件保存运行配置。

```python
from __future__ import annotations
```

启用延迟类型注解。

```python
from dataclasses import dataclass, field
```

导入 `dataclass` 和 `field`。`field(default_factory=...)` 用于给列表字段设置默认值。

```python
from pathlib import Path
```

导入 `Path`，用于处理文件路径。

```python
@dataclass(slots=True)
```

定义配置数据类，并使用 `slots=True` 限制字段。

```python
class AgentConfig:
```

定义一次运行的配置对象。

```python
"""一次 Agent 运行所需的配置。"""
```

说明这个类保存一次运行所需的所有参数。

```python
topic: str
```

用户输入的研究主题。

```python
output_dir: Path
```

输出目录。

```python
max_results: int = 5
```

最多检索几篇论文，默认 5。

```python
evidence_per_paper: int = 3
```

每篇论文最多抽取几条证据，默认 3。

```python
user_agent: str = "paper-agent/0.1.0 (local educational project)"
```

访问外部 API 时使用的 User-Agent。给服务端识别调用方，也能减少被当成异常请求的概率。

```python
arxiv_delay_seconds: float = 3.0
```

每次 arXiv 请求前等待几秒，默认 3 秒，用于降低 429 限流风险。

```python
arxiv_retries: int = 3
```

arXiv 请求失败时最多重试几次。

```python
sources: list[str] = field(default_factory=lambda: ["arxiv", "semantic_scholar", "openalex"])
```

默认论文检索源。使用 `default_factory` 是因为列表是可变对象，不能直接写成默认列表。

```python
writer: str = "rule"
```

报告写作方式。`rule` 表示规则式写作，`deepseek` 表示调用 DeepSeek。

```python
deepseek_model: str = "deepseek-v4-flash"
```

DeepSeek 模型名。

```python
deepseek_base_url: str = "https://api.deepseek.com"
```

DeepSeek API 基础地址。

```python
max_llm_evidence: int = 20
```

最多传给 DeepSeek 的证据条数，避免 prompt 太长。

```python
@property
```

把下面的方法变成只读属性。

```python
def pdf_dir(self) -> Path:
```

定义 PDF 保存目录属性。

```python
"""下载 PDF 的保存目录。"""
```

说明该属性用途。

```python
return self.output_dir / "pdfs"
```

PDF 保存到输出目录下的 `pdfs` 子目录。

```python
@property
```

把下面的方法变成只读属性。

```python
def text_dir(self) -> Path:
```

定义文本保存目录属性。

```python
"""PDF 正文解析结果的保存目录。"""
```

说明该属性用途。

```python
return self.output_dir / "texts"
```

解析出的正文保存到输出目录下的 `texts` 子目录。

## 4. paper_agent/env_loader.py

```python
"""读取 .env 文件中的本地隐私配置。"""
```

说明这个文件负责加载 `.env`。

```python
from __future__ import annotations
```

启用延迟类型注解。

```python
import os
```

导入系统环境变量模块。

```python
from pathlib import Path
```

导入路径处理工具。

```python
def load_env_file(path: Path | None = None) -> None:
```

定义加载 `.env` 的函数。如果传入路径，就加载指定文件；否则自动查找。

```python
"""把 .env 文件中的键值加载到环境变量中。"""
```

说明函数用途。

```python
env_path = path or find_env_file()
```

优先使用调用者传入的路径；没有传入就自动查找 `.env`。

```python
if env_path is None:
    return
```

如果没找到 `.env`，直接返回，不报错。

```python
if not env_path.exists():
    return
```

如果路径不存在，也直接返回。

```python
for raw_line in env_path.read_text(encoding="utf-8").splitlines():
```

按 UTF-8 读取 `.env`，并逐行处理。

```python
line = raw_line.strip()
```

去掉每行两侧空白。

```python
if not line or line.startswith("#"):
    continue
```

跳过空行和注释行。

```python
if "=" not in line:
    continue
```

只处理 `KEY=VALUE` 格式的行。

```python
key, value = line.split("=", 1)
```

按照第一个等号切成键和值。

```python
key = key.strip()
```

清理键两侧空白。

```python
value = _strip_quotes(value.strip())
```

清理值两侧空白，并去掉成对引号。

```python
if not key:
    continue
```

如果键为空，跳过。

```python
os.environ.setdefault(key, value)
```

把键值写入环境变量。使用 `setdefault` 是为了不覆盖系统中已经设置的真实环境变量。

```python
def _strip_quotes(value: str) -> str:
```

定义去引号函数。

```python
"""去掉 .env 值两侧成对的单引号或双引号。"""
```

说明函数用途。

```python
if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
```

判断值是否被一对相同的单引号或双引号包裹。

```python
return value[1:-1]
```

去掉首尾引号。

```python
return value
```

如果没有成对引号，原样返回。

```python
def find_env_file() -> Path | None:
```

定义自动查找 `.env` 的函数。

```python
"""查找最适合当前运行场景的 .env 文件。"""
```

说明函数用途。

```python
project_root = Path(__file__).resolve().parents[1]
```

根据 `env_loader.py` 的位置推导项目根目录。

```python
candidates = [Path.cwd() / ".env", project_root / ".env"]
```

候选位置包括当前运行目录和项目根目录。

```python
for parent in Path.cwd().resolve().parents:
    candidates.append(parent / ".env")
```

把当前目录的所有父目录也加入候选列表。

```python
seen: set[Path] = set()
```

创建集合，用来避免重复检查同一个路径。

```python
for candidate in candidates:
```

遍历所有候选 `.env` 路径。

```python
resolved = candidate.resolve()
```

把路径解析成绝对路径。

```python
if resolved in seen:
    continue
```

如果这个路径已经检查过，就跳过。

```python
seen.add(resolved)
```

记录这个路径已经检查过。

```python
if resolved.exists():
    return resolved
```

找到第一个存在的 `.env` 就返回。

```python
return None
```

所有候选都不存在时返回 `None`。

## 5. paper_agent/text_utils.py

```python
"""小型文本处理工具函数。"""
```

说明这个文件放文本工具。

```python
from __future__ import annotations
```

启用延迟类型注解。

```python
import re
```

导入正则表达式模块。

```python
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]+")
```

定义英文关键词匹配正则。要求单词以字母开头，后面可以跟数字、下划线或连字符。

```python
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
```

定义中文字符匹配正则，用来判断用户查询是否包含中文。

```python
def normalize_space(text: str) -> str:
```

定义空白归一化函数。

```python
return re.sub(r"\s+", " ", text).strip()
```

把连续空白变成一个空格，并去掉首尾空白。

```python
def keywords(topic: str) -> list[str]:
```

定义关键词抽取函数。

```python
seen: set[str] = set()
```

记录已经出现过的关键词。

```python
result: list[str] = []
```

保存最终关键词列表。

```python
for match in WORD_RE.finditer(topic.lower()):
```

把主题转小写，然后用正则找英文关键词。

```python
word = match.group(0)
```

取出匹配到的词。

```python
if len(word) < 3 or word in seen:
    continue
```

跳过太短的词和重复词。

```python
seen.add(word)
```

记录这个词已经出现。

```python
result.append(word)
```

加入结果列表。

```python
return result
```

返回关键词。

```python
def arxiv_search_topic(topic: str) -> str:
```

返回一个最适合 arXiv 的查询词。

```python
return arxiv_search_topics(topic)[0]
```

调用候选查询词函数，并取第一个。

```python
def arxiv_search_topics(topic: str) -> list[str]:
```

生成一组 arXiv 候选查询词。

```python
lowered = topic.lower()
```

转小写，便于判断是否包含 `rag`。

```python
terms: list[str] = []
```

准备保存扩展查询词。

```python
if "rag" in lowered:
    terms.extend(["retrieval augmented generation", "RAG"])
```

如果用户输入 RAG，就扩展成完整英文。

```python
if "概念" in topic:
    terms.append("concept")
```

中文“概念”转成英文 `concept`。

```python
if "综述" in topic or "文献" in topic:
    terms.extend(["survey", "review"])
```

中文“综述/文献”转成 `survey/review`。

```python
if "方法" in topic:
    terms.append("method")
```

中文“方法”转成 `method`。

```python
if "应用" in topic:
    terms.append("application")
```

中文“应用”转成 `application`。

```python
terms.extend(match.group(0) for match in WORD_RE.finditer(topic))
```

保留用户原本输入里的英文词。

```python
result: list[str] = []
seen: set[str] = set()
```

准备去重后的扩展词列表。

```python
for term in terms:
```

遍历所有候选词。

```python
cleaned = normalize_space(term)
key = cleaned.lower()
```

清理空白，并生成小写去重键。

```python
if cleaned and key not in seen:
```

只保留非空且未出现过的词。

```python
seen.add(key)
result.append(cleaned)
```

记录并加入结果。

```python
original = normalize_space(topic)
expanded = " ".join(result)
```

保存原始查询词和扩展查询词。

```python
candidates: list[str] = []
```

准备候选查询列表。

```python
if expanded and expanded.lower() != original.lower():
    candidates.append(expanded)
```

如果扩展词和原始词不同，优先使用扩展词。

```python
if original:
    candidates.append(original)
```

保留原始查询词作为候选。

```python
if "rag" in lowered and "retrieval augmented generation" not in [item.lower() for item in candidates]:
    candidates.append("retrieval augmented generation")
```

如果用户输入 RAG，但候选中还没有完整词，就补上完整英文。

```python
return _unique_texts(candidates) or [original]
```

对候选词去重。如果结果为空，就返回原始词。

```python
def _unique_texts(values: list[str]) -> list[str]:
```

定义文本列表去重函数。

```python
seen: set[str] = set()
result: list[str] = []
```

准备去重集合和结果列表。

```python
for value in values:
```

遍历输入文本。

```python
cleaned = normalize_space(value)
key = cleaned.lower()
```

清理空白，并生成小写去重键。

```python
if cleaned and key not in seen:
```

只保留非空且未出现过的文本。

```python
seen.add(key)
result.append(cleaned)
```

记录并加入结果。

```python
return result
```

返回去重列表。

后面的 `split_sentences()`、`score_text()`、`safe_filename()` 分别负责句子切分、关键词计分和安全文件名生成，逻辑和函数名一致。

## 6. paper_agent/arxiv_client.py

这个文件负责 arXiv 检索和 PDF 下载。

关键 import：

- `json`：保存和读取缓存。
- `socket`：捕获网络超时。
- `time`：请求前等待，避免 arXiv 429。
- `urllib.*`：标准库 HTTP 请求。
- `ElementTree`：解析 arXiv Atom XML。
- `sha256`：生成缓存文件名。
- `Path`：处理路径。

```python
ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}
```

定义 Atom XML 命名空间。

```python
ARXIV_API_URL = "https://export.arxiv.org/api/query"
```

定义 arXiv API 地址。

```python
class ArxivClient:
```

定义 arXiv 客户端。

```python
def __init__(self, user_agent: str, delay_seconds: float = 3.0, retries: int = 3) -> None:
```

初始化时接收 User-Agent、请求等待秒数和重试次数。

```python
self.user_agent = user_agent
self.delay_seconds = delay_seconds
self.retries = retries
```

保存配置。

```python
def search(self, topic: str, max_results: int) -> list[Paper]:
```

根据主题检索 arXiv。

```python
last_error: Exception | None = None
```

保存最后一次错误，方便最后报错。

```python
for index, candidate in enumerate(arxiv_search_topics(topic), start=1):
```

遍历候选查询词。

```python
if index > 1:
    print(...)
```

如果不是第一个查询词，就提示正在换词重试。

```python
try:
    papers = self._search_once(candidate, max_results)
```

尝试执行一次 arXiv 查询。

```python
except (TimeoutError, socket.timeout, urllib.error.URLError) as exc:
```

捕获超时和网络错误。

```python
last_error = exc
print(...)
continue
```

记录错误，提示用户，然后尝试下一个候选词。

```python
if papers:
    return papers
```

只要查到论文就返回。

```python
print(f"arXiv 查询没有结果：{candidate}")
```

如果查询成功但没有结果，输出提示。

```python
if last_error is not None:
    raise RuntimeError(...)
```

如果所有候选词都失败，抛出运行时错误。

```python
return []
```

如果没有错误但也没有结果，返回空列表。

`_search_once()` 负责真正发请求。它先查缓存，没有缓存才请求 arXiv。

`_open_with_retry()` 负责请求前等待、429 重试、超时重试。

`download_pdf()` 负责下载 PDF。如果 `paper.pdf_url` 为空，会抛出错误，流水线会退回摘要证据。

`_parse_feed()` 和 `_parse_entry()` 负责把 arXiv XML 转成 `Paper`。

`_cache_path()`、`_load_cache()`、`_save_cache()` 负责本地缓存。

## 7. paper_agent/semantic_scholar_client.py

这个文件负责 Semantic Scholar 检索。

```python
SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
```

定义 Semantic Scholar 搜索接口地址。

```python
class SemanticScholarClient:
```

定义客户端类。

```python
def __init__(self, user_agent: str) -> None:
    self.user_agent = user_agent
```

保存 User-Agent。

```python
def search(self, topic: str, max_results: int) -> list[Paper]:
```

定义检索方法。

```python
load_env_file()
```

加载 `.env`，以便读取可选的 `SEMANTIC_SCHOLAR_API_KEY`。

```python
fields = ",".join([...])
```

声明希望 Semantic Scholar 返回哪些字段。

```python
params = {"query": topic, "limit": str(max_results), "fields": fields}
```

构造 URL 查询参数。

```python
url = f"{SEMANTIC_SCHOLAR_SEARCH_URL}?{urllib.parse.urlencode(params)}"
```

生成完整请求 URL。

```python
headers = {"User-Agent": self.user_agent}
```

设置请求头。

```python
api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", "").strip()
```

从环境变量读取可选 API Key。

```python
if api_key:
    headers["x-api-key"] = api_key
```

如果有 Key，就加入请求头。

```python
request = urllib.request.Request(url, headers=headers)
```

创建请求对象。

```python
with urllib.request.urlopen(request, timeout=90) as response:
    payload = json.loads(response.read().decode("utf-8"))
```

发送请求，读取 JSON。

```python
return [self._parse_item(item) for item in payload.get("data", []) if item.get("title")]
```

把每条结果转换成统一 `Paper` 对象。

`_parse_item()` 负责字段映射：

- Semantic Scholar 的 `paperId` 转成内部 ID。
- `externalIds.ArXiv` 优先作为论文 ID。
- `openAccessPdf.url` 转成 `pdf_url`。
- `citationCount` 转成 `citation_count`。

## 8. paper_agent/openalex_client.py

这个文件负责 OpenAlex 检索。

```python
OPENALEX_WORKS_URL = "https://api.openalex.org/works"
```

定义 OpenAlex Works API 地址。

`search()` 的流程和 Semantic Scholar 类似：

1. 加载 `.env`。
2. 组装参数。
3. 可选加入 `OPENALEX_API_KEY`。
4. 发请求。
5. 把结果转成 `Paper`。

OpenAlex 的特殊点是摘要字段：

```python
abstract_inverted_index
```

它不是普通字符串，而是倒排索引。

```python
def _abstract(self, inverted_index: dict[str, list[int]]) -> str:
```

这个函数把倒排索引还原成普通摘要。

```python
words: list[tuple[int, str]] = []
```

准备保存 `(位置, 单词)`。

```python
for word, positions in inverted_index.items():
```

遍历每个单词及其出现位置。

```python
for position in positions:
    words.append((position, word))
```

把每个位置和单词加入列表。

```python
return " ".join(word for _, word in sorted(words))
```

按位置排序后拼接成摘要。

## 9. paper_agent/multi_source_client.py

这是多源检索核心。

```python
class MultiSourcePaperClient:
```

定义多源论文客户端。

```python
self.sources = sources
```

保存用户配置的检索源列表。

```python
self.clients = {...}
```

建立源名称到具体客户端的映射。

```python
for source in self.sources:
```

按顺序遍历检索源。

```python
client = self.clients.get(source)
```

根据名称取对应客户端。

```python
if client is None:
    print(...)
    continue
```

如果源名称写错，就跳过。

```python
try:
    papers = client.search(topic, max_results)
```

调用当前来源的检索方法。

```python
except (...) as exc:
    print(...)
    continue
```

如果当前来源失败，就继续下一个来源。

```python
all_papers.extend(papers)
```

把结果加入总列表。

```python
if len(self._dedupe(all_papers)) >= max_results:
    break
```

如果去重后已经够数量，就停止继续请求后面的源。

```python
return self._dedupe(all_papers)[:max_results]
```

返回去重后的前 `max_results` 篇。

`_dedupe()` 按标题去重。

`_merge()` 融合两个来源的同一篇论文，保留更完整的元数据和更高引用数。

## 10. paper_agent/pipeline.py

这是总流水线。

```python
self.search_client = MultiSourcePaperClient(...)
```

创建多源检索客户端。

```python
self.downloader = ArxivClient(...)
```

创建下载器。虽然名字是 arXivClient，但下载方法本质是通用 URL 下载。

```python
self.pdf_reader = PdfReader()
self.writer = ReportWriter()
```

创建 PDF 解析器和规则式报告生成器。

```python
self._prepare_output()
```

创建输出目录。

```python
papers = self.search_client.search(...)
```

多源检索论文。

```python
if not papers:
    raise RuntimeError(...)
```

如果所有来源都没有结果，明确报错。

```python
self._save_papers(...)
```

保存 `papers.json`。

```python
for paper in papers:
```

逐篇论文处理。

```python
try:
    pdf_path = self.downloader.download_pdf(...)
    text = self.pdf_reader.extract_text(pdf_path)
```

尝试下载并解析 PDF。

```python
except Exception as exc:
    print(...)
    text = ""
```

如果 PDF 下载或解析失败，不中断流程，改用摘要。

```python
if text:
    text_by_paper[paper.arxiv_id] = text
```

如果解析出正文，就保存到内存字典。

```python
text_path.write_text(text, encoding="utf-8")
```

把正文保存到 `texts/`。

```python
evidence = self.writer.collect_evidence(...)
```

从正文或摘要中抽取证据。

```python
self.writer.save_evidence(...)
```

保存 `evidence.json`。

```python
if self.config.writer == "deepseek":
```

判断是否使用 DeepSeek 写作。

```python
client = DeepSeekClient.from_env(...)
```

从 `.env` 创建 DeepSeek 客户端。

```python
markdown = LlmReportWriter(...).write_markdown(...)
```

让 DeepSeek 生成 Markdown。

```python
report_path.write_text(markdown, encoding="utf-8")
```

保存 DeepSeek 生成的报告。

```python
else:
    self.writer.write_report(...)
```

如果不是 DeepSeek，就使用规则式报告。

## 11. paper_agent/pdf_reader.py

`PdfReader` 负责 PDF 文本解析。

```python
try:
    import fitz
except ImportError:
    return ""
```

尝试导入 PyMuPDF。如果没安装，就返回空字符串。

```python
with fitz.open(pdf_path) as document:
```

打开 PDF。

```python
for page_index, page in enumerate(document, start=1):
```

逐页遍历。

```python
text = page.get_text("text")
```

抽取当前页文本。

```python
if text.strip():
    pages.append(f"\n[Page {page_index}]\n{text}")
```

如果当前页有文本，就带页码保存。

```python
return "\n".join(pages).strip()
```

拼接所有页文本。

## 12. paper_agent/report_writer.py

`ReportWriter` 负责规则式证据抽取和 Markdown 报告。

`collect_evidence()` 的逻辑：

1. 从主题抽关键词。
2. 每篇论文优先用 PDF 正文。
3. 没有正文就用摘要。
4. 切句。
5. 对每句按关键词出现次数打分。
6. 每篇论文取分数最高的若干条。
7. 保存为 `Evidence`。

`write_report()` 的逻辑：

1. 写标题。
2. 写执行摘要。
3. 写关键证据。
4. 写论文列表。
5. 写局限性。
6. 保存 `report.md`。

## 13. paper_agent/deepseek_client.py

`DeepSeekClient` 负责 API 通信。

```python
load_env_file()
```

读取 `.env`。

```python
api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
```

读取 DeepSeek Key。

```python
if not api_key:
    raise RuntimeError(...)
```

没有 Key 就报错。

```python
url = self.config.base_url.rstrip("/") + "/chat/completions"
```

拼出 Chat Completions API 地址。

```python
payload = {...}
```

构造请求体，包括模型、消息、温度、最大 token。

```python
request = urllib.request.Request(...)
```

构造 HTTP POST 请求。

```python
with urllib.request.urlopen(request, timeout=120) as response:
```

发送请求。

```python
return data["choices"][0]["message"]["content"].strip()
```

读取模型生成文本。

## 14. paper_agent/llm_writer.py

`LlmReportWriter` 负责构造 prompt。

```python
system_prompt = (...)
```

告诉 DeepSeek 必须严谨、必须基于证据、必须中文 Markdown 输出。

```python
user_prompt = self._build_prompt(topic, papers, evidence)
```

把论文元数据和证据构造成用户提示词。

```python
return self.client.chat(system_prompt, user_prompt)
```

调用 DeepSeek。

`_build_prompt()` 会把 `papers` 和 `evidence` 转成 JSON 字符串放进 prompt。

## 15. paper_agent/evaluator.py

`Evaluator` 负责检查输出目录。

```python
report_path = output_dir / "report.md"
papers_path = output_dir / "papers.json"
evidence_path = output_dir / "evidence.json"
```

定位三个核心文件。

```python
report_text = ...
```

读取报告文本。

```python
papers = self._load_json_list(papers_path)
evidence = self._load_json_list(evidence_path)
```

读取论文和证据 JSON。

```python
checks = {...}
```

生成检查项。

```python
return EvaluationResult(passed=all(checks.values()), checks=checks)
```

所有检查通过才算整体通过。

## 16. tests/test_text_utils.py

这个测试文件验证文本工具函数。

```python
assert normalize_space("a\n\n  b\tc") == "a b c"
```

验证空白归一化。

```python
assert keywords("RAG RAG Retrieval AI") == ["rag", "retrieval"]
```

验证关键词小写、去重、过滤短词。

```python
assert split_sentences("One sentence. Another one!") == ["One sentence.", "Another one!"]
```

验证句子切分。

```python
assert score_text(...) == 4
```

验证关键词计分。

```python
assert safe_filename("2301.12345/v2: bad") == "2301.12345_v2_bad"
```

验证文件名清理。

## 17. paper_agent/cli.py

`cli.py` 是整个项目的入口文件。它既支持命令行运行，也支持 VSCode 直接运行后交互输入。

```python
"""论文研读 Agent 的命令行入口。"""
```

文件文档字符串，说明这个文件是命令行入口。

```python
from __future__ import annotations
```

启用延迟类型注解。

```python
import argparse
```

导入命令行参数解析库。

```python
import sys
```

导入系统模块，用来读取命令行参数和修改 `sys.path`。

```python
from pathlib import Path
```

导入路径处理工具。

```python
if __package__ in {None, ""}:
```

判断当前文件是否是被直接运行。如果直接运行 `paper_agent/cli.py`，`__package__` 通常为空。

```python
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

把项目根目录加入 Python 导入路径，解决直接运行时无法导入 `paper_agent` 包的问题。

```python
from paper_agent.config import AgentConfig
from paper_agent.evaluator import Evaluator
from paper_agent.pipeline import PaperAgentPipeline
```

直接运行文件时，使用绝对导入。

```python
else:
```

如果不是直接运行，而是通过 `python -m paper_agent.cli` 运行，就进入这个分支。

```python
from .config import AgentConfig
from .evaluator import Evaluator
from .pipeline import PaperAgentPipeline
```

包运行模式下使用相对导入。

```python
def build_parser() -> argparse.ArgumentParser:
```

定义命令行解析器构建函数。

```python
parser = argparse.ArgumentParser(..., add_help=False)
```

创建主解析器。`add_help=False` 是为了自己定义中文帮助。

```python
parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出。")
```

添加中文帮助选项。

```python
parser._positionals.title = "位置参数"
parser._optionals.title = "选项"
```

把 argparse 默认分组标题改成中文。

```python
subparsers = parser.add_subparsers(dest="command", required=True)
```

创建子命令系统。用户需要输入 `run` 或 `evaluate`。

```python
run_parser = subparsers.add_parser("run", ...)
```

创建 `run` 子命令。

```python
run_parser.add_argument("topic", ...)
```

添加必填研究主题。

```python
run_parser.add_argument("--max-results", type=int, default=5, ...)
```

设置最多检索论文数量。

```python
run_parser.add_argument("--evidence-per-paper", type=int, default=3, ...)
```

设置每篇论文最多抽取几条证据。

```python
run_parser.add_argument("--output", type=Path, default=Path("runs/latest"), ...)
```

设置输出目录。

```python
run_parser.add_argument("--writer", choices=["rule", "deepseek"], ...)
```

设置报告写作方式，只允许 `rule` 或 `deepseek`。

```python
run_parser.add_argument("--deepseek-model", ...)
run_parser.add_argument("--deepseek-base-url", ...)
run_parser.add_argument("--max-llm-evidence", ...)
```

设置 DeepSeek 模型、API 地址和最多传给模型的证据数量。

```python
run_parser.add_argument("--arxiv-delay-seconds", ...)
run_parser.add_argument("--arxiv-retries", ...)
```

设置 arXiv 请求等待时间和重试次数。

```python
run_parser.add_argument("--sources", ...)
```

设置论文检索源，例如 `arxiv,semantic_scholar,openalex`。

```python
eval_parser = subparsers.add_parser("evaluate", ...)
```

创建 `evaluate` 子命令。

```python
eval_parser.add_argument("output", type=Path, ...)
```

评测命令需要一个输出目录。

```python
return parser
```

返回构建好的命令行解析器。

```python
def run_agent_from_args(args: argparse.Namespace) -> int:
```

定义根据参数运行 Agent 的函数。

```python
config = AgentConfig(...)
```

把命令行参数转换成统一配置对象。

```python
sources=_parse_sources(args.sources)
```

把论文源参数解析成列表。

```python
try:
    report_path = PaperAgentPipeline(config).run()
```

创建流水线并运行。

```python
except Exception as exc:
```

捕获运行过程中的异常，避免直接刷 traceback。

```python
print("运行失败，请根据下面的错误信息定位问题。")
```

输出友好的中文失败提示。

```python
if "429" in str(exc) or "Too Many Requests" in str(exc):
```

如果错误里包含 arXiv 限流信息，就额外提示用户。

```python
print(f"错误信息：{exc}")
return 1
```

打印具体错误，并返回失败退出码。

```python
print(f"综述报告已生成：{report_path}")
return 0
```

运行成功时打印报告路径，并返回成功退出码。

```python
def interactive_main() -> int:
```

定义 VSCode 直接运行时使用的交互模式。

```python
project_root = Path(__file__).resolve().parents[1]
```

计算项目根目录，用于设置默认输出路径。

```python
topic = _ask_required(...)
```

询问研究主题，不能为空。

```python
max_results = _ask_int(..., default=1)
```

询问论文数量，默认 1。

```python
evidence_per_paper = _ask_int(..., default=1)
```

询问每篇论文证据数量，默认 1。

```python
output = _ask_text(...)
```

询问输出目录。

```python
writer = _ask_choice(...)
```

询问写作方式。

```python
args = argparse.Namespace(...)
```

把交互输入包装成类似命令行解析结果的对象。

```python
return run_agent_from_args(args)
```

复用命令行模式的运行逻辑。

```python
def _ask_required(prompt: str) -> str:
```

定义必填输入函数。

```python
while True:
```

反复询问，直到用户输入合法内容。

```python
value = input(prompt + " ").strip()
```

读取用户输入并清理空白。

```python
if value:
    return value
```

非空就返回。

```python
print("研究主题不能为空，请重新输入。")
```

空输入时提示用户重试。

```python
def _ask_text(prompt: str, default: str) -> str:
```

定义文本输入函数。

```python
value = input(...).strip()
return value or default
```

用户输入为空时使用默认值。

```python
def _ask_int(prompt: str, default: int) -> int:
```

定义整数输入函数。

```python
try:
    number = int(value)
except ValueError:
```

尝试把输入转成整数，失败就提示重新输入。

```python
if number <= 0:
```

要求整数必须大于 0。

```python
def _ask_choice(prompt: str, choices: list[str], default: str) -> str:
```

定义选项输入函数。

```python
if value in choices:
    return value
```

只有输入在允许选项中才返回。

```python
def _parse_sources(value: str | list[str]) -> list[str]:
```

定义论文源解析函数，同时支持字符串和列表。

```python
if isinstance(value, list):
    return value or [...]
```

如果已经是列表，直接返回；空列表则使用默认源。

```python
sources = [item.strip() for item in value.split(",") if item.strip()]
```

如果是字符串，就按逗号切分，并清理空白。

```python
return sources or ["arxiv", "semantic_scholar", "openalex"]
```

如果解析结果为空，使用默认三源。

```python
def main(argv: list[str] | None = None) -> int:
```

定义程序主入口。

```python
if argv is None and len(sys.argv) == 1:
    return interactive_main()
```

如果用户直接运行文件且没有参数，进入交互模式。

```python
parser = build_parser()
args = parser.parse_args(argv)
```

构建解析器并解析命令行参数。

```python
if args.command == "run":
    return run_agent_from_args(args)
```

如果是 `run` 命令，运行 Agent。

```python
if args.command == "evaluate":
```

如果是 `evaluate` 命令，进入评测逻辑。

```python
result = Evaluator().evaluate(args.output)
print(result.to_text())
```

评测输出目录，并打印结果。

```python
return 0 if result.passed else 1
```

评测通过返回 0，否则返回 1。

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

当文件被直接运行时，调用 `main()`，并把返回值作为进程退出码。

## 18. 这份逐行解释的阅读建议

建议按这个顺序看源码：

1. `models.py`
2. `config.py`
3. `cli.py`
4. `pipeline.py`
5. `multi_source_client.py`
6. `arxiv_client.py`
7. `semantic_scholar_client.py`
8. `openalex_client.py`
9. `report_writer.py`
10. `deepseek_client.py`
11. `llm_writer.py`
12. `evaluator.py`

这样读，你会先理解数据结构，再理解入口，再理解流水线，最后理解各个具体能力模块。
