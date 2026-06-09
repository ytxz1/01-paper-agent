# 项目完整开发与排错过程

这份文档记录 `01-paper-agent` 从零生成到最终多源检索版本的完整过程。它不是简单说明书，而是把实际开发中遇到的问题、报错原因和修复方案都写下来，方便以后复盘和继续开发。

## 1. 初始目标

用户给出的目标是参考：

```text
https://github.com/adongwanai/AgentGuide/tree/main/projects/01-paper-agent
```

项目目标是做一个论文研读 Agent：

- 输入研究主题。
- 检索论文。
- 下载 PDF。
- 解析 PDF 文本。
- 抽取证据。
- 生成 Markdown 综述。
- 对输出做基础评测。

## 2. 第一版：arXiv 单源 MVP

第一版实现了：

- `arxiv_client.py`
- `pdf_reader.py`
- `report_writer.py`
- `pipeline.py`
- `cli.py`
- `evaluator.py`

当时流程是：

```text
topic
  ↓
arXiv API
  ↓
papers.json
  ↓
PDF 下载
  ↓
PDF 文本解析
  ↓
evidence.json
  ↓
report.md
```

优点是结构清楚，缺点是过度依赖 arXiv。

## 3. 增加 DeepSeek API

用户问是否需要 API，于是加入 DeepSeek。

新增：

- `deepseek_client.py`
- `llm_writer.py`

DeepSeek 模式下：

```text
papers.json + evidence.json
  ↓
DeepSeek API
  ↓
中文 Markdown 综述
```

重要原则：

- DeepSeek 不负责检索论文。
- DeepSeek 只基于已有论文和证据写作。
- Key 不写进代码。

## 4. 增加 .env

用户要求 API Key 不要传到 GitHub。

于是新增：

- `.env`
- `.env.example`
- `env_loader.py`

`.gitignore` 中加入：

```text
.env
.env.*
!.env.example
```

这样真实密钥不会提交，模板可以提交。

## 5. 修复 .env 查找路径

用户从：

```text
D:\vscode项目
```

运行：

```powershell
python d:/vscode项目/01-paper-agent/paper_agent/cli.py
```

旧代码只查当前目录：

```text
D:\vscode项目\.env
```

但真实 `.env` 在：

```text
D:\vscode项目\01-paper-agent\.env
```

修复方案：

`env_loader.py` 同时查：

- 当前目录
- 项目根目录
- 父级目录

## 6. 修复直接运行 cli.py 的导入问题

用户直接运行：

```powershell
python paper_agent/cli.py
```

报错：

```text
ImportError: attempted relative import with no known parent package
```

原因：

```python
from .config import AgentConfig
```

这种相对导入要求文件以包方式运行。

修复方案：

在 `cli.py` 顶部判断：

```python
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

这样直接运行和 `python -m paper_agent.cli` 都支持。

## 7. 修复没有 command 的问题

直接运行 `cli.py` 时，最初会报：

```text
the following arguments are required: command
```

原因是 CLI 默认要求：

```text
run
evaluate
```

用户希望 VSCode 直接运行后输入话题。

修复方案：

增加 `interactive_main()`：

```text
论文研读 Agent 交互模式
请输入研究主题
最多检索多少篇论文
每篇论文最多抽取几条证据
输出目录
报告写作方式
```

现在直接运行 `cli.py` 会进入交互模式。

## 8. 中文查询在 arXiv 查不到

用户输入：

```text
RAG的概念
```

arXiv 返回 0 篇。

原因是 arXiv 主要按英文标题、摘要、作者检索，中文查询不容易命中。

修复方案：

`text_utils.py` 增加 arXiv 查询词改写：

```text
RAG的概念
  ↓
retrieval augmented generation RAG concept
```

这解决了中文关键词和英文论文库之间的桥接问题。

## 9. arXiv 超时、429、503

用户多次遇到：

```text
The read operation timed out
HTTP Error 429: Too Many Requests
HTTP Error 503: Service Unavailable
```

原因：

- arXiv 对自动请求频率敏感。
- `RAG` 这种短词太宽泛。
- arXiv 服务可能临时不可用。

先做的修复：

- 请求前等待 3 秒。
- 429 自动等待重试。
- 查询结果缓存到 `.cache/arxiv/`。
- 默认检索数量改成 1。

但这只能缓解，不能从根本上解决 arXiv 单点失败。

## 10. 短暂加入内置演示数据

为了让流程先跑通，曾经加入过内置论文数据。

但用户明确表示：

```text
我不需要你给我展示内置数据，我现在就想程序拥有论文检索的能力
```

所以最终删除内置演示数据，转向真实多源检索。

## 11. 最终方案：多源真实论文检索

新增：

- `semantic_scholar_client.py`
- `openalex_client.py`
- `multi_source_client.py`

默认检索源：

```text
arxiv
semantic_scholar
openalex
```

最终流程：

```text
先查 arXiv
  ↓
arXiv 失败
  ↓
继续查 Semantic Scholar
  ↓
继续查 OpenAlex
  ↓
多源去重融合
```

这才是真正的论文检索能力，而不是演示数据。

## 12. Semantic Scholar 接入

端点：

```text
https://api.semanticscholar.org/graph/v1/paper/search
```

返回字段：

- `paperId`
- `title`
- `abstract`
- `authors`
- `year`
- `url`
- `openAccessPdf`
- `externalIds`
- `citationCount`

可选 `.env`：

```text
SEMANTIC_SCHOLAR_API_KEY=
```

## 13. OpenAlex 接入

端点：

```text
https://api.openalex.org/works
```

返回字段：

- `id`
- `title`
- `authorships`
- `publication_date`
- `abstract_inverted_index`
- `primary_location`
- `cited_by_count`

OpenAlex 摘要是倒排索引形式，代码中会还原成普通摘要文本。

可选 `.env`：

```text
OPENALEX_API_KEY=
```

## 14. 修复 sources 类型错误

交互模式报错：

```text
AttributeError: 'list' object has no attribute 'split'
```

原因：

- 命令行模式中 `sources` 是字符串。
- 交互模式中 `sources` 是列表。

修复：

```python
def _parse_sources(value: str | list[str]) -> list[str]:
```

现在字符串和列表都支持。

## 15. 当前最终版本的运行建议

第一次运行：

```powershell
python -m paper_agent.cli run "retrieval augmented generation" --max-results 1 --evidence-per-paper 1 --writer rule
```

如果 arXiv 老是限流，直接绕开 arXiv：

```powershell
python -m paper_agent.cli run "retrieval augmented generation" --sources semantic_scholar,openalex --max-results 1 --writer rule
```

如果要 DeepSeek 写作：

```powershell
python -m paper_agent.cli run "retrieval augmented generation" --sources semantic_scholar,openalex --max-results 1 --writer deepseek
```

## 16. 当前最终版本的核心价值

最终项目具备：

- VSCode 直接运行交互输入。
- `.env` 管理 API Key。
- DeepSeek 写作增强。
- arXiv 检索。
- Semantic Scholar 检索。
- OpenAlex 检索。
- 多源去重融合。
- PDF 下载失败自动退回摘要。
- Markdown 报告生成。
- 输出评测。

它已经不再是单一 arXiv 脚本，而是一个真正具备多源论文检索能力的论文综述 Agent。
