# Paper Agent 代码结构与模块说明

这份文档解释 `01-paper-agent` 的最终代码结构。项目经历了从 arXiv 单源检索、DeepSeek 写作、`.env` 配置，到多源真实论文检索的完整迭代。

## 1. 总体架构

```text
cli.py
  ↓
config.py
  ↓
pipeline.py
  ↓
multi_source_client.py
  ├── arxiv_client.py
  ├── semantic_scholar_client.py
  └── openalex_client.py
  ↓
pdf_reader.py
  ↓
report_writer.py / llm_writer.py
  ↓
evaluator.py
```

## 2. cli.py

`cli.py` 是入口文件，负责两种运行方式：

- 命令行模式：用户传入 `run` 或 `evaluate`。
- 交互模式：用户在 VSCode 里直接运行 `cli.py`。

关键设计：

```python
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

这段代码解决直接运行 `paper_agent/cli.py` 时相对导入失败的问题。

交互模式由 `interactive_main()` 实现。用户不需要写长命令，只要按提示输入：

- 研究主题
- 论文数量
- 每篇论文证据数量
- 输出目录
- 写作方式

`_parse_sources()` 同时支持字符串和列表：

```python
def _parse_sources(value: str | list[str]) -> list[str]:
```

这是为了兼容命令行模式和交互模式。命令行里 `sources` 是字符串，交互模式里 `sources` 是列表。

## 3. config.py

`AgentConfig` 保存一次运行需要的所有配置：

- `topic`
- `output_dir`
- `max_results`
- `evidence_per_paper`
- `sources`
- `writer`
- `deepseek_model`
- `deepseek_base_url`
- `max_llm_evidence`

其中：

```python
sources: list[str] = field(default_factory=lambda: ["arxiv", "semantic_scholar", "openalex"])
```

表示默认使用三个真实论文源。

## 4. models.py

`Paper` 是统一论文元数据模型。

字段包括：

- `arxiv_id`：论文标识。对于非 arXiv 来源，也会填入 Semantic Scholar 或 OpenAlex ID。
- `title`：标题。
- `authors`：作者列表。
- `summary`：摘要。
- `published`：发布时间。
- `updated`：更新时间。
- `pdf_url`：PDF 地址。
- `page_url`：论文页面地址。
- `source`：来源，例如 `arxiv`、`semantic_scholar`、`openalex`。
- `citation_count`：引用次数。

`Evidence` 表示证据片段：

- `paper_id`
- `paper_title`
- `source`
- `excerpt`
- `score`
- `location`

## 5. multi_source_client.py

这是最终版本中最重要的检索模块。

它依次调用：

```text
arxiv
semantic_scholar
openalex
```

核心逻辑：

1. 遍历配置中的检索源。
2. 调用对应客户端。
3. 如果某个源失败，打印错误并继续下一个源。
4. 收集所有论文。
5. 按标题去重。
6. 返回最多 `max_results` 篇论文。

这样 arXiv 返回 429 或 503 时，项目不会直接挂掉。

## 6. arxiv_client.py

`ArxivClient` 调用 arXiv Atom API。

它保留了：

- 请求前等待，降低 429 风险。
- 429 自动重试。
- 查询缓存 `.cache/arxiv/`。
- PDF 下载方法。

它不再使用内置演示数据。如果 arXiv 失败，会把错误抛给 `MultiSourcePaperClient`，由多源逻辑继续尝试 Semantic Scholar/OpenAlex。

## 7. semantic_scholar_client.py

调用 Semantic Scholar Graph API：

```text
https://api.semanticscholar.org/graph/v1/paper/search
```

请求字段包括：

- `paperId`
- `title`
- `abstract`
- `authors`
- `year`
- `url`
- `openAccessPdf`
- `externalIds`
- `citationCount`

如果 `.env` 中有：

```text
SEMANTIC_SCHOLAR_API_KEY=
```

则会放入请求头 `x-api-key`。

## 8. openalex_client.py

调用 OpenAlex Works API：

```text
https://api.openalex.org/works
```

OpenAlex 的摘要是 `abstract_inverted_index`，代码中会把它还原成普通文本。

OpenAlex 的优势是开放度高，适合作为 arXiv 不稳定时的替代检索源。

## 9. env_loader.py

负责读取 `.env`。

它会查找：

1. 当前运行目录下的 `.env`
2. 项目根目录下的 `.env`
3. 当前目录的父级目录

这样无论用户从：

```text
D:\vscode项目
```

还是：

```text
D:\vscode项目\01-paper-agent
```

运行程序，都能找到项目里的 `.env`。

## 10. deepseek_client.py

负责调用 DeepSeek API。

它从 `.env` 读取：

```text
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
```

如果找不到 `DEEPSEEK_API_KEY`，会给出中文错误提示。

## 11. llm_writer.py

`LlmReportWriter` 把论文元数据和证据片段组织成 prompt，然后交给 DeepSeek 生成中文 Markdown 综述。

关键要求：

- 只能依据提供的论文和证据写作。
- 不能编造没有提供的论文或实验结果。
- 重要结论必须带论文 ID 引用。

## 12. pdf_reader.py

优先使用 PyMuPDF：

```python
import fitz
```

如果没有安装 PyMuPDF，返回空字符串。

流水线会自动退回摘要证据，不会中断运行。

## 13. report_writer.py

规则式报告生成器。

它做两件事：

1. 根据关键词从正文或摘要中抽取证据。
2. 生成中文 Markdown 报告。

规则式模式不需要 API Key，也不消耗费用，适合第一次测试。

## 14. evaluator.py

评测输出目录是否完整。

检查项：

- `report.md` 是否存在。
- 报告是否包含引用标记。
- `papers.json` 是否有论文。
- `evidence.json` 是否存在。
- 是否至少有一条证据。

## 15. text_utils.py

文本工具函数包括：

- 空白归一化。
- 关键词抽取。
- 句子切分。
- 文本打分。
- 安全文件名生成。
- arXiv 查询词改写。

例如用户输入：

```text
RAG的概念
```

会改写成：

```text
retrieval augmented generation RAG concept
```

## 16. 最终设计原则

- 不使用内置论文假数据。
- 多源真实检索。
- arXiv 不稳定时自动尝试替代源。
- DeepSeek 只负责写作增强，不负责凭空编造论文。
- 所有敏感 Key 放 `.env`。
- VSCode 直接运行也能工作。
- 每一步产物都保存到本地，方便检查。
