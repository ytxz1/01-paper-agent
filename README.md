# 01-paper-agent

这是一个论文研读与综述生成 Agent 项目。它的目标是：给定一个研究主题后，自动检索真实论文元数据，尽量下载 PDF，解析正文或使用摘要抽取证据，并生成可追溯的 Markdown 综述报告。

本项目最终实现的是一个多源论文检索 Agent，而不是只依赖 arXiv 的单点工具。默认检索源包括：

- arXiv
- Semantic Scholar
- OpenAlex

如果 arXiv 返回 `429 Too Many Requests`、`503 Service Unavailable` 或超时，程序会继续尝试 Semantic Scholar 和 OpenAlex，而不是直接失败。

## 最终运行流程

```text
用户输入研究主题
  ↓
CLI 解析参数或进入 VSCode 交互模式
  ↓
MultiSourcePaperClient 多源检索论文
  ↓
arXiv / Semantic Scholar / OpenAlex 返回论文元数据
  ↓
按标题去重并融合元数据
  ↓
保存 papers.json
  ↓
尝试下载 PDF
  ↓
能解析 PDF：使用正文抽证据
不能解析 PDF：退回摘要抽证据
  ↓
保存 evidence.json
  ↓
rule 模式：规则式生成 report.md
deepseek 模式：把论文和证据交给 DeepSeek 生成 report.md
  ↓
可选 evaluate 命令检查输出质量
```

## 项目结构

```text
01-paper-agent/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── docs/
│   ├── code_walkthrough.md
│   └── project_process.md
├── paper_agent/
│   ├── __init__.py
│   ├── arxiv_client.py
│   ├── cli.py
│   ├── config.py
│   ├── deepseek_client.py
│   ├── env_loader.py
│   ├── evaluator.py
│   ├── llm_writer.py
│   ├── models.py
│   ├── multi_source_client.py
│   ├── openalex_client.py
│   ├── pdf_reader.py
│   ├── report_writer.py
│   ├── semantic_scholar_client.py
│   └── text_utils.py
└── tests/
    └── test_text_utils.py
```

## 安装

建议 Python 3.10 或更高版本。

```powershell
python -m pip install -e .
```

如果要解析 PDF 正文，安装可选依赖：

```powershell
python -m pip install -e ".[pdf]"
```

如果没有安装 PyMuPDF，程序仍然可以运行，只是会使用摘要作为证据来源。

## .env 隐私配置

真实 API Key 放在 `.env`，不要提交到 GitHub。项目已经在 `.gitignore` 中忽略 `.env`。

模板文件是 `.env.example`：

```text
DEEPSEEK_API_KEY=sk-请替换成你的真实DeepSeekApiKey
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

SEMANTIC_SCHOLAR_API_KEY=
OPENALEX_API_KEY=
```

其中：

- `DEEPSEEK_API_KEY`：DeepSeek 写作模式需要。
- `SEMANTIC_SCHOLAR_API_KEY`：可选。没有也能访问公开接口，但可能更容易限流。
- `OPENALEX_API_KEY`：可选。没有也能尝试公开接口。

## VSCode 直接运行

打开：

```text
paper_agent/cli.py
```

点击 VSCode 右上角运行按钮，或者右键选择：

```text
Run Python File in Terminal
```

程序会进入交互模式：

```text
论文研读 Agent 交互模式
直接回车会使用括号中的默认值。
请输入研究主题，例如 retrieval augmented generation：
最多检索多少篇论文（默认：1）：
每篇论文最多抽取几条证据（默认：1）：
输出目录（默认：D:\vscode项目\01-paper-agent\runs\interactive）：
报告写作方式（rule/deepseek，默认：rule）：
```

第一次测试建议：

```text
主题：retrieval augmented generation
论文数量：1
证据数量：1
写作方式：rule
```

跑通后再使用 `deepseek`。

## 命令行运行

规则式报告：

```powershell
python -m paper_agent.cli run "retrieval augmented generation" --max-results 1 --evidence-per-paper 1 --writer rule
```

DeepSeek 报告：

```powershell
python -m paper_agent.cli run "retrieval augmented generation" --max-results 1 --evidence-per-paper 1 --writer deepseek
```

绕开 arXiv，只用 OpenAlex：

```powershell
python -m paper_agent.cli run "tool augmented language models" --sources openalex --max-results 1 --writer rule
```

使用 Semantic Scholar 和 OpenAlex：

```powershell
python -m paper_agent.cli run "tool augmented language models" --sources semantic_scholar,openalex --max-results 1 --writer rule
```

默认三源：

```powershell
python -m paper_agent.cli run "large language model agents" --sources arxiv,semantic_scholar,openalex --max-results 1
```

## 输出文件

默认输出目录是：

```text
runs/interactive
```

核心产物：

- `papers.json`：多源检索到的论文元数据。
- `pdfs/`：成功下载的 PDF。
- `texts/`：成功解析出的 PDF 文本。
- `evidence.json`：抽取出的证据片段。
- `report.md`：最终 Markdown 综述。

## 评测

```powershell
python -m paper_agent.cli evaluate runs/interactive
```

评测会检查：

- 是否生成 `report.md`
- 报告是否包含引用标记
- 是否保存 `papers.json`
- 是否保存 `evidence.json`
- 是否至少抽取一条证据

## 常见问题

### 1. attempted relative import with no known parent package

原因：直接运行 `paper_agent/cli.py` 时，Python 不知道它属于 `paper_agent` 包。

修复：`cli.py` 已经加了项目根目录注入逻辑，现在直接运行和 `python -m paper_agent.cli` 都支持。

### 2. the following arguments are required: command

原因：最初 CLI 必须显式传 `run` 或 `evaluate`。

修复：现在直接运行 `cli.py` 会进入交互模式。

### 3. 未找到 DEEPSEEK_API_KEY

原因：`.env` 查找路径不对，或者 `.env` 中没有真实 Key。

修复：`env_loader.py` 现在会从当前目录、父目录和项目根目录查找 `.env`。

### 4. arXiv 返回 429 或 503

原因：arXiv 对自动请求频率敏感，或者服务端临时不可用。

修复：项目现在支持多源检索。arXiv 失败后会继续尝试 Semantic Scholar 和 OpenAlex。

### 5. list object has no attribute split

原因：交互模式里 `sources` 是列表，命令行模式里 `sources` 是字符串。

修复：`_parse_sources()` 已经同时支持字符串和列表。

## 详细文档

- [代码结构与模块说明](docs/code_walkthrough.md)
- [全部代码逐行解释](docs/line_by_line_code_explanation.md)
- [完整开发与排错过程](docs/project_process.md)
- [简历写法与面试准备指南](docs/resume_interview_guide.md)
