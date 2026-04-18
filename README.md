<div align="center">

# 🎯 Anything → NotebookLM

**多源内容智能处理器：任何内容 → 播客 / PPT / 思维导图 / Quiz**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)
[![GitHub stars](https://img.shields.io/github/stars/joeseesun/qiaomu-anything-to-notebooklm?style=social)](https://github.com/joeseesun/qiaomu-anything-to-notebooklm/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/joeseesun/qiaomu-anything-to-notebooklm?style=social)](https://github.com/joeseesun/qiaomu-anything-to-notebooklm/network/members)
[![GitHub issues](https://img.shields.io/github/issues/joeseesun/qiaomu-anything-to-notebooklm)](https://github.com/joeseesun/qiaomu-anything-to-notebooklm/issues)
[![GitHub last commit](https://img.shields.io/github/last-commit/joeseesun/qiaomu-anything-to-notebooklm)](https://github.com/joeseesun/qiaomu-anything-to-notebooklm/commits/main)

[快速开始](#-快速开始) • [支持格式](#-支持的内容源-15-种) • [使用示例](#-使用示例) • [付费墙绕过](#-付费墙绕过) • [常见问题](#-常见问题)

</div>

---

## ✨ 这是什么？

一个 **Claude Code Skill**，用自然语言把**任何内容**变成**任何格式**。

```
你说：把这篇微信文章生成播客
AI ：✅ 8 分钟播客已生成 → podcast.mp3

你说：这个付费文章做成思维导图
AI ：✅ 自动绕过付费墙 → 思维导图已生成

你说：这期播客（小宇宙）做成 PPT
AI ：✅ 自动转录音频 → 25 页 PPT 已生成
```

**核心能力**：多源内容获取（含付费墙绕过）→ 上传 [Google NotebookLM](https://notebooklm.google.com/) → AI 生成目标格式

---

## 🚀 支持的内容源（15+ 种）

<table>
<tr>
<td width="50%">

### 📱 社交与媒体
- **微信公众号**（MCP 浏览器模拟）
- **X/Twitter**（推文 + 长线程）
- **YouTube 视频**（自动提取字幕）
- **播客**（小宇宙 / 喜马拉雅 / B站）

### 🌐 网页（含付费墙绕过）
- **300+ 付费网站**（NYT/WSJ/FT/Economist...）
- **任意公开网页**（新闻、博客、文档）
- **搜索关键词**（自动汇总结果）

</td>
<td width="50%">

### 📚 电子书与文档
- **PDF**（支持扫描件 OCR）
- **EPUB** 电子书
- **Markdown** (.md)
- **纯文本** (.txt)

### 📄 Office 文档
- **Word** (.docx)
- **PowerPoint** (.pptx)
- **Excel** (.xlsx)

### 🖼️ 其他
- **图片**（JPEG/PNG，自动 OCR）
- **音频**（WAV/MP3，自动转录）
- **ZIP 压缩包**（批量处理）

</td>
</tr>
</table>

---

## 🛡️ 付费墙绕过

**核心特性**：自动检测并绕过 300+ 付费新闻网站的付费墙。

### 绕过策略（6 层级联）

```
Level 1: 代理服务（r.jina.ai / defuddle.md）
    ↓ 失败
Level 2: 站点专属 Bot UA（Googlebot ~50站 / Bingbot ~4站）
    ↓ 失败
Level 3: 通用绕过（UA伪装 + X-Forwarded-For + Referer伪装 + AMP + EU IP）
    ↓ 失败
Level 4: archive.today 存档（CAPTCHA 自动检测）
    ↓ 失败
Level 5: Google Cache
    ↓ 失败
Level 6: agent-fetch 本地工具
```

### 支持的付费网站（部分）

| 类别 | 站点 |
|------|------|
| 🇺🇸 美国媒体 | NYT, WSJ, Bloomberg, Washington Post, The Information, Forbes, WIRED, The New Yorker, The Atlantic, USA Today, Boston Globe, LA Times, Chicago Tribune, Seattle Times, MIT Tech Review, Foreign Affairs |
| 🇬🇧 英国媒体 | FT, The Times, The Telegraph, The Economist |
| 🇩🇪 德国媒体 | Spiegel, Zeit, Sueddeutsche, FAZ, Handelsblatt |
| 🇫🇷 法国媒体 | Le Monde, Le Figaro, Le Parisien |
| 🇦🇺 澳洲媒体 | The Australian, SMH, The Age, Brisbane Times |
| 🇨🇳 中文媒体 | SCMP, Medium |
| 🌐 其他 | Haaretz, NZ Herald, Statista, Quora |

### 绕过技术（学自 [Bypass Paywalls Clean](https://gitflic.ru/project/magnolia1234/bypass-paywalls-chrome-clean)）

| 技术 | 原理 | 覆盖率 |
|------|------|--------|
| **Googlebot UA + X-Forwarded-For** | 搜索引擎爬虫白名单，直接获取全文 | ~50 站 |
| **Bingbot UA** | 同上，部分站点对 Bing 更友好 | ~4 站 |
| **Cookie 清空 + Referer 伪装** | 清除计量 cookie，伪装来自 Google/Facebook/Twitter | 计量付费墙 |
| **AMP 页面** | AMP 版付费墙实现较弱 | ~10 站 |
| **JSON-LD 提取** | 从 HTML 内嵌的结构化数据提取 articleBody | 通用 |
| **archive.today** | 从网页存档获取已保存的内容 | 兜底方案 |

---

## 🎨 可以生成什么？

| 输出格式 | 用途 | 触发词示例 |
|---------|------|-----------|
| 🎙️ **播客** | 通勤路上听 | "生成播客"、"做成音频" |
| 📊 **PPT** | 团队分享 | "做成PPT"、"生成幻灯片" |
| 🗺️ **思维导图** | 理清结构 | "画个思维导图"、"生成脑图" |
| 📝 **Quiz** | 自测掌握 | "生成Quiz"、"出题" |
| 🎬 **视频** | 可视化 | "做个视频" |
| 📄 **报告** | 深度分析 | "生成报告"、"写个总结" |
| 📈 **信息图** | 数据可视化 | "做个信息图" |
| 📋 **闪卡** | 记忆巩固 | "做成闪卡" |

---

## ⚡ 快速开始

### 前置需求

- ✅ Python 3.9+
- ✅ Git（macOS/Linux 自带）

**就这两样！** 其他依赖一键自动安装。

### 安装（3 步）

```bash
# 1. 克隆到 Claude skills 目录
cd ~/.claude/skills/
git clone https://github.com/joeseesun/qiaomu-anything-to-notebooklm
cd qiaomu-anything-to-notebooklm

# 2. 一键安装所有依赖
./install.sh

# 3. 按提示配置 MCP，然后重启 Claude Code
```

### 首次使用

```bash
# NotebookLM 认证（只需一次）
notebooklm login
notebooklm list  # 验证成功

# 环境检查（可选）
./check_env.py
```

### 播客转写配置（可选）

如需使用小宇宙/喜马拉雅/B站转写功能，配置 Get笔记 API：

```bash
export GETNOTE_API_KEY="your_api_key"
export GETNOTE_CLIENT_ID="your_client_id"
```

---

## 💡 使用示例

### 场景 1：付费文章 → 播客

```
你：把这篇 The Information 文章生成播客 https://www.theinformation.com/articles/...

AI 自动执行：
  ✓ 检测付费墙 → Googlebot UA 绕过
  ✓ 获取完整文章内容
  ✓ 上传到 NotebookLM
  ✓ 生成播客

✅ 结果：/tmp/article_podcast.mp3
```

### 场景 2：播客（小宇宙）→ PPT

```
你：这期小宇宙播客做成 PPT https://xiaoyuzhoufm.com/episode/...

AI 自动执行：
  ✓ Get笔记 API 转写音频（2-5 分钟）
  ✓ 上传转写文本到 NotebookLM
  ✓ 生成 PPT

✅ 结果：/tmp/podcast_slides.pdf（25 页）
```

### 场景 3：电子书 → 深度分析

```
你：深度分析这本书 /Users/joe/Books/sapiens.epub

AI 自动执行：
  ✓ 提取 EPUB 全文
  ✓ 上传到 NotebookLM
  ✓ 生成 10 个核心问题
  ✓ 逐一递归提问并收集答案
  ✓ 输出结构化 JSON

✅ 结果：/tmp/sapiens_analysis.json（10 个问答，含金句、核心观点、局限性分析）
```

### 场景 4：X/Twitter 线程 → 思维导图

```
你：这个推文线程做成思维导图 https://x.com/user/status/123...

AI 自动执行：
  ✓ 代理级联获取推文内容（含完整线程）
  ✓ 上传到 NotebookLM
  ✓ 生成思维导图

✅ 结果：/tmp/tweet_mindmap.json
```

### 场景 5：微信文章 → 飞书文档（深度分析）

```
你：深度分析这篇微信文章并写入飞书 https://mp.weixin.qq.com/s/abc123

AI 自动执行：
  ✓ MCP 浏览器模拟抓取微信文章
  ✓ 上传到 NotebookLM
  ✓ 生成 10 个问题并递归提问
  ✓ 格式化为飞书 Markdown
  ✓ 自动创建飞书文档

✅ 结果：飞书文档已创建（含完整问答）
```

---

## 🎯 核心特性

### 🧠 智能识别
自动判断输入类型，无需手动指定

```
https://mp.weixin.qq.com/s/xxx        → 微信公众号
https://xiaoyuzhoufm.com/episode/xxx  → 小宇宙播客
https://x.com/user/status/xxx         → X/Twitter
https://youtube.com/watch?v=xxx       → YouTube 视频
/path/to/file.epub                    → EPUB 电子书
"搜索 'AI 趋势'"                       → 搜索查询
```

### 🛡️ 付费墙自动绕过
无需手动处理，自动检测并绕过

```
检测付费墙 → 选择最佳策略 → 获取完整内容
     ︿________全自动________︿
```

### 🚀 全自动处理
从获取到生成，一气呵成

```
输入 → 获取 → 转换 → 上传 → 生成 → 下载
      ︿___________全自动___________︿
```

### 🌐 多源整合
支持混合多种内容源

```
付费文章 + YouTube 视频 + EPUB + 播客 → 综合报告
```

---

## 📦 技术架构

```
┌──────────────────────────────────────────┐
│            用户自然语言输入                │
│  "把这个付费文章生成播客 https://..."     │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│         Claude Code Skill                 │
│  • 智能识别内容源类型                      │
│  • 自动调用对应工具                        │
└──────────┬───────────────────────────────┘
           │
   ┌───────┴───────┐
   │               │
   ▼               ▼
┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐
│ 微信 MCP  │  │ 付费墙绕过   │  │ 播客转写  │  │ markitdown│
│ 浏览器模拟 │  │ 6层级联策略  │  │ Get笔记API│  │ 文件转换  │
└─────┬────┘  └──────┬───────┘  └─────┬────┘  └─────┬────┘
      │              │                 │              │
      └──────────────┴─────────────────┴──────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │    NotebookLM API      │
              │  • 上传内容源           │
              │  • AI 生成目标格式      │
              └───────────┬────────────┘
                          │
                          ▼
              ┌────────────────────────┐
              │       生成的文件        │
              │ .mp3 / .pdf / .json    │
              └────────────────────────┘
```

---

## 📂 项目结构

```
qiaomu-anything-to-notebooklm/
├── SKILL.md                          # Skill 定义文件
├── README.md                         # 本文件
├── main.py                           # 主入口：CLI 智能处理器
├── install.sh                        # 一键安装脚本
├── check_env.py                      # 13 项环境检查
├── package.sh                        # 打包分享脚本
├── requirements.txt                  # Python 依赖
├── LICENSE                           # MIT
├── scripts/
│   ├── fetch_url.sh                  # URL 抓取 + 付费墙绕过（6 层级联）
│   └── get_podcast_transcript.py     # 播客/视频转写（Get笔记 API）
├── wexin-read-mcp/                   # 微信公众号 MCP 服务器
│   └── src/
│       ├── server.py                 # MCP 入口
│       ├── scraper.py                # Playwright 浏览器模拟
│       └── parser.py                 # HTML 解析
└── feishu-read-mcp/                  # 飞书文档 MCP 服务器
    └── src/
        ├── server.py                 # MCP 入口
        ├── scraper.py                # 飞书文档抓取
        ├── parser.py                 # HTML → Markdown
        └── image_handler.py          # 图片处理
```

---

## 🔧 高级用法

### 深度分析模式

```bash
python main.py https://example.com/article --deep-analysis
# 自动生成 10 个核心问题，逐一递归提问，输出结构化 JSON
```

### 飞书文档输出

```bash
python main.py ./book.epub --deep-analysis --to-feishu
# 深度分析后自动创建飞书文档
```

### 批量处理

```
把这些文章都生成播客：
1. https://mp.weixin.qq.com/s/abc123
2. https://www.wsj.com/articles/...
3. /Users/joe/notes.md
```

---

## 🐛 故障排查

### MCP 工具未找到

```bash
python ~/.claude/skills/qiaomu-anything-to-notebooklm/wexin-read-mcp/src/server.py
cd ~/.claude/skills/qiaomu-anything-to-notebooklm/wexin-read-mcp
pip install -r requirements.txt
playwright install chromium
```

### NotebookLM 认证失败

```bash
notebooklm login     # 重新登录
notebooklm list      # 验证
```

### 付费墙绕过失败

部分硬付费墙网站（如 The Information）服务器端不发送内容，需要 archive.today 存档。脚本会自动检测并提示：
```
⚠️  archive.ph needs human verification.
   已自动打开浏览器，请完成验证后重试
```

### 环境检查

```bash
./check_env.py       # 13 项全面检查
./install.sh         # 重新安装
```

---

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
<summary><b>Q: 付费墙绕过合法吗？</b></summary>

A: 本工具仅用于个人学习研究。技术原理基于搜索引擎白名单（Googlebot/Bingbot），不破解任何加密。建议支持优质新闻媒体，购买订阅。
</details>

<details>
<summary><b>Q: 内容长度限制？</b></summary>

A:
- 最短：约 500 字
- 最长：约 50 万字
- 推荐：1000-10000 字效果最佳
</details>

<details>
<summary><b>Q: 为什么需要 MCP？</b></summary>

A: 微信公众号有反爬虫，MCP 用 Playwright 浏览器模拟绕过。其他内容源（网页、YouTube、PDF）不需要 MCP。
</details>

<details>
<summary><b>Q: 播客转写支持哪些平台？</b></summary>

A: 通过 Get笔记 API 支持小宇宙、喜马拉雅、B站视频。YouTube 由 NotebookLM 直接处理。
</details>

---

## 🙏 致谢

- [Google NotebookLM](https://notebooklm.google.com/) - AI 内容生成
- [Microsoft markitdown](https://github.com/microsoft/markitdown) - 文件转换
- [Bypass Paywalls Clean](https://gitflic.ru/project/magnolia1234/bypass-paywalls-chrome-clean) - 付费墙绕过策略参考
- [wexin-read-mcp](https://github.com/Bwkyd/wexin-read-mcp) - 微信抓取
- [notebooklm-py](https://github.com/teng-lin/notebooklm-py) - NotebookLM CLI

## 📄 许可证

[MIT License](LICENSE) - 仅限个人学习研究使用

---

<div align="center">

**如果觉得有用，请给个 ⭐ Star！**

Made with ❤️ by [Joe](https://github.com/joeseesun) · [Twitter @vista8](https://x.com/vista8) · 微信公众号「向阳乔木推荐看」

</div>
