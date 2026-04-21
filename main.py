#!/usr/bin/env python3
"""
qiaomu-anything-to-notebooklm - 多源内容智能处理器
自动识别输入类型，上传到 NotebookLM 并生成指定格式
支持深度分析模式：自动生成10个问题并递归提问
"""

import sys
import os
import subprocess
import tempfile
import json
import time
import re
from pathlib import Path

def detect_input_type(input_path):
    """检测输入类型"""
    if input_path.startswith('http'):
        if 'mp.weixin.qq.com' in input_path:
            return 'weixin'
        elif 'youtube.com' in input_path or 'youtu.be' in input_path:
            return 'youtube'
        elif 'xiaoyuzhoufm.com' in input_path or 'ximalaya.com' in input_path or 'bilibili.com' in input_path:
            return 'podcast'
        elif 'x.com' in input_path or 'twitter.com' in input_path:
            return 'x_twitter'
        else:
            return 'url'

    path = Path(input_path).expanduser()
    if not path.exists():
        return 'search'  # 不是文件路径，当作搜索关键词

    suffix = path.suffix.lower()
    if suffix == '.epub':
        return 'epub'
    elif suffix in ['.pdf', '.txt', '.md']:
        return 'document'
    elif suffix in ['.docx', '.pptx', '.xlsx']:
        return 'office'
    elif suffix in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        return 'image'
    elif suffix in ['.mp3', '.wav']:
        return 'audio'
    elif suffix == '.zip':
        return 'zip'
    else:
        return 'unknown'

def extract_epub_to_txt(epub_path):
    """提取 EPUB 到 TXT"""
    import ebooklib
    from ebooklib import epub
    from bs4 import BeautifulSoup

    book = epub.read_epub(str(epub_path))
    content = []

    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            soup = BeautifulSoup(item.get_content(), 'html.parser')
            content.append(soup.get_text())

    # 保存到临时文件
    txt_path = tempfile.mktemp(suffix='.txt', prefix='epub_')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(content))

    return txt_path

def upload_to_notebooklm(file_path, title):
    """上传文件到 NotebookLM"""
    # 创建笔记本
    result = subprocess.run(
        ['notebooklm', 'create', title],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 创建笔记本失败: {result.stderr}", file=sys.stderr)
        return False

    # 上传文件
    result = subprocess.run(
        ['notebooklm', 'source', 'add', file_path, '--title', title],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 上传文件失败: {result.stderr}", file=sys.stderr)
        return False

    print(f"✅ 已上传到 NotebookLM: {title}")
    return True

def generate_questions(content_type, title):
    """根据内容类型生成10个深度问题"""

    # 基础问题模板（适用于所有类型）
    base_questions = [
        f"请用一句话概括《{title}》的核心主题",
        f"《{title}》中最重要的3个观点是什么？",
        f"作者在《{title}》中想要解决什么问题？",
        f"《{title}》中有哪些令人印象深刻的金句或名言？（列出5-10条）",
        f"《{title}》的论证逻辑是什么？作者如何展开论述的？",
    ]

    # 根据内容类型添加特定问题
    if content_type in ['epub', 'document']:
        # 书籍/文档类
        specific_questions = [
            f"《{title}》适合什么样的读者？为什么？",
            f"《{title}》中有哪些实践建议或行动指南？",
            f"《{title}》的局限性是什么？有哪些观点值得商榷？",
            f"如果要向朋友推荐《{title}》，你会怎么说？（50字以内）",
            f"读完《{title}》后，最大的收获是什么？",
        ]
    elif content_type == 'youtube':
        # 视频类
        specific_questions = [
            f"这个视频的目标受众是谁？",
            f"视频中提到了哪些关键数据或案例？",
            f"视频的叙事结构是什么？",
            f"如果要做一个5分钟的精华版，应该保留哪些内容？",
            f"这个视频的观点在当前环境下是否仍然适用？",
        ]
    else:
        # 文章/网页类
        specific_questions = [
            f"这篇内容的写作目的是什么？",
            f"内容中有哪些数据或事实支撑？",
            f"作者的立场和观点是什么？",
            f"这篇内容对我有什么启发？",
            f"如果要转发这篇内容，我会加什么评论？",
        ]

    return base_questions + specific_questions

def ask_notebooklm(question):
    """向 NotebookLM 提问并获取答案"""
    result = subprocess.run(
        ['notebooklm', 'ask', question],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"⚠️ 提问失败: {result.stderr}", file=sys.stderr)
        return None

    return result.stdout.strip()

def format_feishu_markdown(title, questions, answers):
    """将问答结果格式化为飞书 Markdown"""
    lines = [
        f"# {title} - 深度解读",
        "",
        "> 本文档由 NotebookLM 深度分析生成",
        "",
    ]

    for i, (q, a) in enumerate(zip(questions, answers), 1):
        lines.append(f"## {i}. {q}")
        lines.append("")
        if a:
            lines.append(a)
        else:
            lines.append("*（未回答）*")
        lines.append("")

    return "\n".join(lines)

def create_feishu_doc(title, markdown_content):
    """创建飞书文档"""
    print("\n📝 创建飞书文档...")

    # 调用 lark-cli docs +create
    result = subprocess.run(
        ['lark-cli', 'docs', '+create', '--title', title, '--markdown', markdown_content],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ 创建飞书文档失败: {result.stderr}", file=sys.stderr)
        return None

    # 从输出中提取文档 URL（如果有）
    output = result.stdout
    print(f"✅ 飞书文档已创建")
    print(output)

    return True

def deep_analysis(file_path, title, content_type, to_feishu=False, provider="notebooklm", model=None):
    """深度分析模式：生成问题并递归提问

    Args:
        file_path:    本地内容文件路径
        title:        内容标题
        content_type: 内容类型（epub / document / url 等）
        to_feishu:    是否写入飞书文档
        provider:     AI 分析提供方，"notebooklm"（默认）或 "minimax"
        model:        使用 minimax provider 时的模型名，默认 MiniMax-M2.7
    """
    print("\n" + "="*60)
    print("🔍 启动深度分析模式")
    if provider == "minimax":
        used_model = model or "MiniMax-M2.7"
        print(f"   Provider: MiniMax ({used_model})")
    else:
        print("   Provider: NotebookLM")
    print("="*60 + "\n")

    # 2. 生成问题
    print("\n📝 Step 1/2: 生成深度分析问题...")
    questions = generate_questions(content_type, title)
    print(f"✅ 已生成 {len(questions)} 个问题\n")

    # 3. 递归提问
    print("💬 Step 2/2: 开始递归提问...\n")
    answers = []

    if provider == "minimax":
        # 读取内容文件，直接传给 MiniMax API
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError as exc:
            print(f"❌ 读取文件失败: {exc}", file=sys.stderr)
            return None

        from minimax_provider import analyze_content
        try:
            answers = analyze_content(
                content,
                questions,
                model=used_model,
            )
            print(f"✅ MiniMax 已回答 {len(answers)} 个问题\n")
        except Exception as exc:
            print(f"❌ MiniMax 分析失败: {exc}", file=sys.stderr)
            return None
    else:
        # 默认 NotebookLM 流程
        print("📤 上传内容到 NotebookLM...")
        if not upload_to_notebooklm(file_path, title):
            return None

        print("⏳ 等待 NotebookLM 处理内容...")
        time.sleep(3)

        for i, question in enumerate(questions, 1):
            print(f"[{i}/{len(questions)}] {question}")
            answer = ask_notebooklm(question)

            if answer:
                print(f"✅ 已回答\n")
                answers.append(answer)
            else:
                print(f"⚠️ 跳过\n")
                answers.append("")

            time.sleep(1)

    # 4. 返回结构化数据
    result = {
        "status": "success",
        "title": title,
        "content_type": content_type,
        "provider": provider,
        "questions": questions,
        "answers": answers,
        "total_questions": len(questions),
        "answered": len([a for a in answers if a])
    }

    # 5. 如果指定了 --to-feishu，创建飞书文档
    if to_feishu:
        markdown = format_feishu_markdown(title, questions, answers)
        create_feishu_doc(f"{title} - 深度解读", markdown)

    return result

def main():
    if len(sys.argv) < 2:
        print("用法: main.py <输入路径或URL> [--deep-analysis] [--to-feishu] [--provider notebooklm|minimax] [--model MiniMax-M2.7]", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    deep_mode = '--deep-analysis' in sys.argv
    to_feishu = '--to-feishu' in sys.argv

    # --provider notebooklm (default) | minimax
    provider = "notebooklm"
    if '--provider' in sys.argv:
        idx = sys.argv.index('--provider')
        if idx + 1 < len(sys.argv):
            provider = sys.argv[idx + 1]

    # --model <model-id>  (only used with --provider minimax)
    llm_model = None
    if '--model' in sys.argv:
        idx = sys.argv.index('--model')
        if idx + 1 < len(sys.argv):
            llm_model = sys.argv[idx + 1]

    input_type = detect_input_type(input_arg)
    print(f"📋 检测到输入类型: {input_type}")

    # 根据类型处理
    if input_type == 'epub':
        epub_path = Path(input_arg).expanduser()
        print(f"📚 处理 EPUB: {epub_path.name}")

        # 提取文本
        txt_path = extract_epub_to_txt(epub_path)
        print(f"✅ 文本已提取: {txt_path}")

        title = epub_path.stem

        if deep_mode:
            result = deep_analysis(txt_path, title, input_type, to_feishu=to_feishu, provider=provider, model=llm_model)
            if result:
                # 保存结果到文件
                output_file = f"/tmp/{title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
        else:
            upload_to_notebooklm(txt_path, title)

    elif input_type == 'document':
        doc_path = Path(input_arg).expanduser()
        print(f"📄 处理文档: {doc_path.name}")

        title = doc_path.stem

        if deep_mode:
            result = deep_analysis(str(doc_path), title, input_type, to_feishu=to_feishu, provider=provider, model=llm_model)
            if result:
                output_file = f"/tmp/{title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
        else:
            upload_to_notebooklm(str(doc_path), title)

    elif input_type == 'podcast':
        print(f"🎙️ 处理播客/视频: {input_arg}")
        print("   通过 Get笔记 API 获取转写（可能需要 2-5 分钟）...")

        script = os.path.join(os.path.dirname(__file__), 'scripts', 'get_podcast_transcript.py')
        result = subprocess.run(
            ['python3', script, input_arg],
            capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ 获取转写失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        # Parse JSON output from script
        try:
            data = json.loads(result.stdout.strip())
        except json.JSONDecodeError:
            print(f"❌ 解析输出失败: {result.stdout}", file=sys.stderr)
            sys.exit(1)

        txt_path = data['txt_path']
        title = data['title']
        content_length = data['content_length']
        print(f"✅ 转写完成: {title} ({content_length} 字符)")
        print(f"   TXT: {txt_path}")

        if deep_mode:
            result_data = deep_analysis(txt_path, title, 'podcast', to_feishu=to_feishu, provider=provider, model=llm_model)
            if result_data:
                safe_title = re.sub(r'[：:/\\?|<>*"\']', '_', title).strip('_')[:60]
                output_file = f"/tmp/{safe_title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
        else:
            upload_to_notebooklm(txt_path, title)

    elif input_type == 'x_twitter':
        print(f"🐦 处理 X/Twitter: {input_arg}")
        print("   通过代理级联获取推文内容...")

        fetch_script = os.path.join(os.path.dirname(__file__), 'scripts', 'fetch_url.sh')
        result = subprocess.run(
            ['bash', fetch_script, input_arg],
            capture_output=True, text=True, timeout=60
        )

        if result.returncode != 0:
            print(f"❌ 获取推文失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        content = result.stdout.strip()
        if not content:
            print("❌ 获取到空内容", file=sys.stderr)
            sys.exit(1)

        # Extract title from content or URL
        title = input_arg.split('/')[-1] or 'x_post'
        # Try to extract first line as title
        first_line = content.split('\n')[0].strip()
        if first_line and len(first_line) < 100:
            title = first_line.lstrip('#').strip()

        safe_title = re.sub(r'[：:/\\?|<>*"\']', '_', title).strip('_')[:60]
        txt_path = tempfile.mktemp(suffix='.txt', prefix=f'x_{safe_title}_')

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            f.write(f"来源: {input_arg}\n")
            f.write(f"获取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n")
            f.write(content)

        print(f"✅ 推文内容已获取: {safe_title} ({len(content)} 字符)")
        print(f"   TXT: {txt_path}")

        if deep_mode:
            result_data = deep_analysis(txt_path, safe_title, 'x_twitter', to_feishu=to_feishu, provider=provider, model=llm_model)
            if result_data:
                output_file = f"/tmp/{safe_title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
        else:
            upload_to_notebooklm(txt_path, safe_title)

    elif input_type == 'url':
        print(f"🌐 处理 URL: {input_arg}")

        if deep_mode:
            # URL 需要先上传，然后提取标题
            result = subprocess.run(
                ['notebooklm', 'source', 'add', input_arg],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ URL 已添加到 NotebookLM")
                # 从 URL 提取标题（简化版）
                title = input_arg.split('/')[-1] or 'web_content'

                # 等待处理
                time.sleep(3)

                # 生成问题并提问
                questions = generate_questions('url', title)
                answers = []

                print(f"\n💬 开始提问（共 {len(questions)} 个问题）...\n")
                for i, question in enumerate(questions, 1):
                    print(f"[{i}/{len(questions)}] {question}")
                    answer = ask_notebooklm(question)
                    if answer:
                        print(f"✅ 已回答\n")
                        answers.append(answer)
                    else:
                        print(f"⚠️ 跳过\n")
                        answers.append("")
                    time.sleep(1)

                result = {
                    "status": "success",
                    "title": title,
                    "url": input_arg,
                    "questions": questions,
                    "answers": answers
                }

                output_file = f"/tmp/{title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
            else:
                print(f"❌ 添加失败: {result.stderr}", file=sys.stderr)
                sys.exit(1)
        else:
            # 普通模式：只上传
            result = subprocess.run(
                ['notebooklm', 'source', 'add', input_arg],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✅ URL 已添加到 NotebookLM")
            else:
                print(f"❌ 添加失败: {result.stderr}", file=sys.stderr)
                sys.exit(1)

    else:
        print(f"❌ 不支持的输入类型: {input_type}", file=sys.stderr)
        print("提示: 请使用 EPUB、PDF、TXT、MD 文件或 URL", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
