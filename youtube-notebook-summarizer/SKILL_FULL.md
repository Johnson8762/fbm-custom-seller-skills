---
name: youtube-notebook-summarizer
description: 当用户发来 YouTube 视频链接并要求总结、做笔记或归档时使用：抓取字幕，生成全中文长文笔记，按知识点分类保存。
---

# YouTube 视频中文笔记（原 NotebookLM YouTube Summarizer）

## 运行环境（box）——替代说明

原流程依赖 NotebookLM MCP（`mcp_notebooklm_notebook_create` / `source_add` / `notebook_query`），box 上**没有 NotebookLM MCP**。
- 默认路线：脚本抓字幕 → 由你（agent）直接按下方 Prompt 要求写中文总结
- 备选路线：用户明确要求用 NotebookLM 时，用 box 浏览器打开 notebooklm.google.com（需用户先在 box 浏览器登录 Google），新建 notebook → 添加 YouTube 来源 → 用同一 Prompt 提问 → 复制结果
- Python：`python`；脚本：`youtube-notebook-summarizer/fetch_youtube_transcript.py`

## 核心前提
1. **语言绝对限制**：总结、笔记全文**完全使用中文**。
2. **存储路径统一**：笔记只能存到 `reports/NotebookLM/<核心知识点类型>/`，不得写到其他目录。

## 执行步骤

### Step 1：抓取视频信息与字幕
```bash
python youtube-notebook-summarizer/fetch_youtube_transcript.py "<YouTube URL 或 ID>" -o ./tmp/yt_<id>.json
```
输出 JSON：`video_id`、`title`、`channel`、`duration`、`lang`、`transcript[]`（带时间戳）、`text`（全文）。字幕优先级：中文 > 英文；人工字幕 > 自动字幕。
- 若出现 `transcript_error`（无字幕/被限流）：告知用户，并改用备选 NotebookLM 浏览器路线，或请用户提供字幕文件；**不要凭标题编造内容**。
- 长视频（全文很长）先按时间段分块阅读，再汇总。

### Step 2：内容提炼与知识点归类
按以下要求写总结（等同原 NotebookLM 查询 Prompt）：
1. 用全中文详细总结视频的核心观点、具体操作步骤、面临的问题与解决方案。
2. 提取一个最核心的 **1-2 个词的知识点/主题**（如：AI应用、个人管理、被动收入、电商运营），第一行单独输出 `目录分类: [知识点]`，不加其他标点。
3. 全文用清晰的 Markdown 分级排版；关键结论可附 `[mm:ss]` 时间戳。

### Step 3：写入分类目录
1. 解析第一行的 `[知识点]`。
2. `mkdir -p "reports/NotebookLM/[知识点]"`
3. 保存为 `reports/NotebookLM/[知识点]/[视频标题].md`（标题中的 `/ \ : * ? " < > |` 替换为 `_`）。
4. 回复用户：知识点分类、文件路径、3-5 条要点摘要。

> [!IMPORTANT]
> 原流程写入 Obsidian（Mac 本地）。box 上无法直接写入用户的 Obsidian 仓库；如需同步，把 md 文件交给用户或上传到其云盘。
