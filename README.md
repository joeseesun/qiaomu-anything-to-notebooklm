<div align="center">

# 🎯 多源内容 → NotebookLM 智能处理器

**一句话变播客、PPT、思维导图、Quiz...**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![GitHub stars](https://img.shields.io/github/stars/joeseesun/anything-to-notebooklm?style=social)](https://github.com/joeseesun/anything-to-notebooklm/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/joeseesun/anything-to-notebooklm?style=social)](https://github.com/joeseesun/anything-to-notebooklm/network/members)
[![GitHub issues](https://img.shields.io/github/issues/joeseesun/anything-to-notebooklm)](https://github.com/joeseesun/anything-to-notebooklm/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/joeseesun/anything-to-notebooklm)](https://github.com/joeseesun/anything-to-notebooklm/commits/main)

[快速开始](#-快速开始) • [支持格式](#-支持的内容源) • [使用示例](#-使用示例) • [常见问题](#-常见问题)

</div>

---

## ✨ 这是什么？

一个 **Claude Code Skill**，让你用自然语言把**任何内容**变成**任何格式**。

```
你说：把这篇微信文章生成播客
AI ：✅ 8 分钟播客已生成 → podcast.mp3

你说：这本 EPUB 电子书做成思维导图
AI ：✅ 思维导图已生成 → mindmap.json

你说：这个 YouTube 视频做成 PPT
AI ：✅ 25 页 PPT 已生成 → slides.pdf
```

**原理**：自动从多种来源获取内容 → 上传到 [Google NotebookLM](https://notebooklm.google.com/) → AI 生成你想要的格式

## 🧩 架构模式（编排器 + 可选插件）

本项目采用「主 Skill 编排 + 子 Skill 插件」模式：

- `anything-to-notebooklm`：主编排器，负责识别内容源、调用转换工具、上传 NotebookLM、触发生成。
- `bilibili-subtitle`：可选子插件，专门负责 B 站字幕提取/无字幕转录。
- `BBDown`：`bilibili-subtitle` 的底层依赖，由安装脚本自动检查/补装。

这意味着：

- 不安装 `bilibili-subtitle` 时，主 Skill 仍可处理微信/网页/YouTube/PDF 等来源。
- 安装 `bilibili-subtitle` 后，才启用 B 站能力。
- 两个仓库独立升级，靠命令契约协作，不需要代码仓库硬合并。

## 🚀 支持的内容源（15+ 种格式）

<table>
<tr>
<td width="50%">

### 📱 社交媒体
- **微信公众号**（绕过反爬虫）
- **YouTube 视频**（自动提取字幕）
- **Bilibili 视频**（可选插件：`bilibili-subtitle`）

### 🌐 网页
- **任意网页**（新闻、博客、文档）
- **搜索关键词**（自动汇总结果）

### 📄 Office 文档
- **Word** (.docx)
- **PowerPoint** (.pptx)
- **Excel** (.xlsx)

</td>
<td width="50%">

### 📚 电子书与文档
- **PDF**（支持扫描件 OCR）
- **EPUB**（电子书）
- **Markdown** (.md)

### 🖼️ 图片与音频
- **图片**（JPEG/PNG/GIF，自动 OCR）
- **音频**（WAV/MP3，自动转录）

### 📊 结构化数据
- **CSV/JSON/XML**
- **ZIP 压缩包**（批量处理）

</td>
</tr>
</table>

**技术支持**: [Microsoft markitdown](https://github.com/microsoft/markitdown)

## 🎨 可以生成什么？

| 输出格式 | 用途 | 生成时间 | 触发词示例 |
|---------|------|---------|-----------|
| 🎙️ **播客** | 通勤路上听 | 2-5 分钟 | "生成播客"、"做成音频" |
| 📊 **PPT** | 团队分享 | 1-3 分钟 | "做成PPT"、"生成幻灯片" |
| 🗺️ **思维导图** | 理清结构 | 1-2 分钟 | "画个思维导图"、"生成脑图" |
| 📝 **Quiz** | 自测掌握 | 1-2 分钟 | "生成Quiz"、"出题" |
| 🎬 **视频** | 可视化 | 3-8 分钟 | "做个视频" |
| 📄 **报告** | 深度分析 | 2-4 分钟 | "生成报告"、"写个总结" |
| 📈 **信息图** | 数据可视化 | 2-3 分钟 | "做个信息图" |
| 📋 **闪卡** | 记忆巩固 | 1-2 分钟 | "做成闪卡" |

**完全自然语言，无需记命令！**

## ⚡ 快速开始

### 前置需求

- ✅ Python 3.9+
- ✅ Git（macOS/Linux 自带）

**就这两样！** 其他依赖一键自动安装。

### 安装（3 步）

```bash
# 1. 克隆到 Claude skills 目录
cd ~/.claude/skills/
git clone https://github.com/joeseesun/anything-to-notebooklm
cd anything-to-notebooklm

# 2. 一键安装所有依赖
./install.sh

# 3. 按提示配置 MCP，然后重启 Claude Code
```

### 可选：启用 B 站插件能力

```bash
# Claude Code
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.claude/skills/bilibili-subtitle
cd ~/.claude/skills/bilibili-subtitle && ./install.sh

# Codex/Agents（如使用该目录）
git clone https://github.com/HamsteRider-m/bilibili-subtitle.git ~/.agents/skills/bilibili-subtitle
cd ~/.agents/skills/bilibili-subtitle && ./install.sh
```

### 首次使用

```bash
# NotebookLM 认证（只需一次）
notebooklm login
notebooklm list  # 验证成功

# 环境检查（可选）
./check_env.py
```

## 💡 使用示例

### 场景 1：快速学习 - 文章 → 播客

```
你：把这篇文章生成播客 https://mp.weixin.qq.com/s/abc123

AI 自动执行：
  ✓ 抓取微信文章内容
  ✓ 上传到 NotebookLM
  ✓ 生成播客（2-5 分钟）

✅ 结果：/tmp/article_podcast.mp3（8 分钟，12.3 MB）
💡 用途：通勤路上听完一篇深度文章
```

### 场景 2：团队分享 - 电子书 → PPT

```
你：这本书做成 PPT /Users/joe/Books/sapiens.epub

AI 自动执行：
  ✓ 提取电子书内容（15 万字）
  ✓ AI 精炼核心观点
  ✓ 生成专业 PPT

✅ 结果：/tmp/sapiens_slides.pdf（25 页，3.8 MB）
💡 用途：直接用于读书会分享
```

### 场景 3：自测学习 - 视频 → Quiz

```
你：这个 YouTube 视频生成 Quiz https://youtube.com/watch?v=abc

AI 自动执行：
  ✓ 提取视频字幕
  ✓ AI 分析关键知识点
  ✓ 自动出题

✅ 结果：/tmp/video_quiz.md（15 道题，10 选择 + 5 简答）
💡 用途：检验学习效果
```

### 场景 4：信息整合 - 多源 → 报告

```
你：把这些内容一起做成报告：
    - https://example.com/article1
    - https://youtube.com/watch?v=xyz
    - /Users/joe/research.pdf

AI 自动执行：
  ✓ 汇总 3 个不同来源
  ✓ AI 整合分析
  ✓ 生成综合报告

✅ 结果：/tmp/multi_source_report.md（7 个章节，15.2 KB）
💡 用途：全面的主题研究报告
```

### 场景 5：文档数字化 - 扫描件 → 文字

```
你：把这个扫描图片做成文档 /Users/joe/scan.jpg

AI 自动执行：
  ✓ OCR 识别图片中的文字
  ✓ 提取为纯文本
  ✓ 生成结构化文档

✅ 结果：/tmp/scan_document.txt（识别准确率 95%+）
💡 用途：扫描件数字化归档
```

## 🎯 核心特性

### 🧠 智能识别
自动判断输入类型，无需手动指定

```
https://mp.weixin.qq.com/s/xxx   → 微信公众号
https://youtube.com/watch?v=xxx  → YouTube 视频
/path/to/file.epub               → EPUB 电子书
"搜索 'AI 趋势'"                  → 搜索查询
```

### 🚀 全自动处理
从获取到生成，一气呵成

```
输入 → 获取 → 转换 → 上传 → 生成 → 下载
      ︿________全自动________︿
```

### 🌐 多源整合
支持混合多种内容源

```
文章 + 视频 + PDF + 搜索结果 → 综合报告
```

### 🔒 本地优先
敏感内容本地处理

```
微信文章 → 本地 MCP 抓取 → 本地转换 → NotebookLM
```

## 📦 技术架构

```
┌─────────────────────────────────────┐
│          用户自然语言输入             │
│  "把这篇文章生成播客 https://..."   │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│        Claude Code Skill             │
│  • 智能识别内容源类型                 │
│  • 自动调用对应工具                   │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌──────────┐     ┌─────────────┐
│ 微信公众号 │     │  其他格式    │
│ MCP 抓取  │     │ markitdown  │
└─────┬────┘     └──────┬──────┘
      │                 │
      └────────┬────────┘
               │
               ▼
┌─────────────────────────────────────┐
│         NotebookLM API               │
│  • 上传内容源                         │
│  • AI 生成目标格式                    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│           生成的文件                  │
│  .mp3 / .pdf / .json / .md          │
└─────────────────────────────────────┘
```

## 🔧 高级用法

### 指定已有 Notebook

```
把这篇文章加到我的【AI研究】笔记本 https://example.com
```

### 批量处理

```
把这些文章都生成播客：
1. https://mp.weixin.qq.com/s/abc123
2. https://example.com/article2
3. /Users/joe/notes.md
```

### ZIP 批量转换

```
把这个压缩包里的所有文档做成播客 /path/to/files.zip
```

自动解压、识别、转换、合并

## 🐛 故障排查

### MCP 工具未找到

```bash
# 测试 MCP 服务器
python ~/.claude/skills/anything-to-notebooklm/wexin-read-mcp/src/server.py

# 重新安装依赖
cd ~/.claude/skills/anything-to-notebooklm/wexin-read-mcp
pip install -r requirements.txt
playwright install chromium
```

### NotebookLM 认证失败

```bash
notebooklm login     # 重新登录
notebooklm list      # 验证
```

### 环境检查

```bash
./check_env.py       # 13 项全面检查
./install.sh         # 重新安装
```

### B 站能力不可用

```bash
# 1) 确认子 Skill 已安装
ls ~/.agents/skills/bilibili-subtitle

# 2) 重跑安装，确保 BBDown 存在
cd ~/.agents/skills/bilibili-subtitle && ./install.sh

# 3) 首次使用前登录 BBDown
BBDown login
```

## 🤝 贡献

欢迎 PR、Issue、建议！

## ❓ 常见问题

<details>
<summary><b>Q: 支持哪些语言？</b></summary>

A: NotebookLM 支持多语言，中文、英文效果最佳。
</details>

<details>
<summary><b>Q: 播客是谁的声音？</b></summary>

A: Google AI 语音合成。英文是两个 AI 主持人对话，中文是单人叙述。
</details>

<details>
<summary><b>Q: 内容长度限制？</b></summary>

A:
- 最短：约 500 字
- 最长：约 50 万字
- 推荐：1000-10000 字效果最佳
</details>

<details>
<summary><b>Q: 可以商用吗？</b></summary>

A:
- 本 Skill：MIT 开源，可自由使用
- 生成内容：遵守 NotebookLM 服务条款
- 原始内容：遵守原内容版权
- 建议：仅用于个人学习研究
</details>

<details>
<summary><b>Q: 为什么需要 MCP？</b></summary>

A: 微信公众号有反爬虫，MCP 用浏览器模拟绕过。其他内容源（网页、YouTube、PDF）不需要 MCP。
</details>

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [Google NotebookLM](https://notebooklm.google.com/) - AI 内容生成
- [Microsoft markitdown](https://github.com/microsoft/markitdown) - 文件转换
- [wexin-read-mcp](https://github.com/Bwkyd/wexin-read-mcp) - 微信抓取
- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) - NotebookLM CLI

## 📮 联系

- **Issues**: [GitHub Issues](https://github.com/joeseesun/anything-to-notebooklm/issues)
- **Discussions**: [GitHub Discussions](https://github.com/joeseesun/anything-to-notebooklm/discussions)

---

<div align="center">

**如果觉得有用，请给个 ⭐ Star！**

Made with ❤️ by [Joe](https://github.com/joeseesun)

</div>
