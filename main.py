#!/usr/bin/env python3
"""qiaomu-anything-to-notebooklm - 多源内容智能处理器
自动识别输入类型，上传到 NotebookLM 并生成指定格式
支持深度分析模式：三轮递进提问（概览→深度挖掘→综合反刍）
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

def label_for(content_type):
    """根据内容类型返回合适的中文指代词"""
    labels = {
        'epub': '本书',
        'document': '这份文档',
        'podcast': '这期播客',
        'x_twitter': '这条推文',
        'youtube': '这个视频',
        'url': '这篇文章',
        'weixin': '这篇文章',
        'search': '这份内容',
    }
    return labels.get(content_type, '这份内容')


def generate_questions_progressive(content_type):
    """
    生成三轮回合递进的深度问题。

    本函数与具体内容解耦，不使用 {title} 等占位符，
    统一用 label_for(content_type) 生成的指代词（如"本书""这个视频"）。

    设计原则：
    - 第一轮（4题）：建立整体认知框架
    - 第二轮（5题）：深入挖掘细节与矛盾
    - 第三轮（3题）：综合反刍与认知升级
    - NotebookLM 在同一 conversation 中保持上下文，后续回合受益于前序回答

    问题设计技巧：
    - "请基于提供的文档内容回答" 防止 NotebookLM 触发网络搜索
    - "列出、拆解、指出、提取" 等动作词引导结构化回答
    - 避免 yes/no 式问题
    """
    name = label_for(content_type)

    # ── 第一轮：概览与框架 ──
    round1 = [
        f"请用一段话概括{name}的核心主题和写作目的。注意：完全基于已上传的文档内容回答，不要搜索网络。",
        f"{name}的整体结构是什么？请按章节或逻辑模块逐一列出，每个模块用2-3句话概括核心内容。完全基于文档回答。",
        f"{name}提出了哪些核心论点或主张？请逐一列出并用文档中的具体内容支撑每个论点。完全基于文档回答。",
        f"{name}中最具颠覆性或反常识的内容是什么？请列出3-5条，并解释每条为什么让人意外。完全基于文档回答。",
    ]

    # ── 第二轮：深度挖掘 ──
    if content_type in ['epub', 'document']:
        # 书籍/文档类：侧重论证逻辑与文本细读
        round2 = [
            f"请拆解{name}的核心论证逻辑：作者的前提假设是什么？推理过程是怎样的？最终结论是什么？请引用具体文本段落说明。",
            f"{name}中引用了哪些关键案例、数据或文本证据？请逐一列出并说明每个证据在整体论证中起到什么作用。",
            f"{name}中是否存在内部矛盾或值得商榷的观点？如果有，请指出并分析矛盾的根源。如果没有，请说明为什么论证站得住脚。",
            f"{name}最独特的贡献或核心洞察是什么？如果只能用一句话概括，应该是什么？为什么这句话重要？",
            f"如果要对{name}提出一个最尖锐的批评，会是什么？请从论证完整性、证据充分性、视角局限性等角度分析。",
        ]
    elif content_type == 'youtube':
        round2 = [
            f"这个视频的核心论点是什么？演讲者用哪些论据来支撑？请拆解其论证结构。",
            f"视频中提到了哪些具体案例、数据或研究？请逐一列出并说明它们在论证中的作用。",
            f"这个视频的立场是否存在偏向或漏洞？哪些观点可能经不起推敲？",
            f"这个视频最独特的信息或洞察是什么？有没有在其他地方看不到的内容？",
            f"如果请一位持反对立场的专家来回应，他最可能提出的三个反驳点是什么？",
        ]
    else:
        # 文章/网页/播客/推文类：侧重叙事与观点分析
        round2 = [
            f"请拆解{name}的论证或叙事结构：开头如何建立框架？中间如何展开？结尾如何收束？使用了哪些修辞或论证手法？",
            f"{name}中引用了哪些关键案例、数据或引用？请逐一列出并评估其可信度和相关性。",
            f"{name}的立场或视角是否存在局限？有没有重要的反例或未被讨论的维度？",
            f"{name}最令人印象深刻的一个洞察或观点是什么？为什么它具有冲击力？",
            f"如果要给{name}的作者写一封简短的反馈信，你会提出哪三个建设性意见或质疑？",
        ]

    # ── 第三轮：综合与反刍 ──
    round3 = [
        f"读完{name}后，读者最应该带走的一个认知改变是什么？哪些观点可能颠覆读者的既有认知？",
        f"从{name}中可以提取出哪些可操作的行动指南、实践建议或决策原则？请列出3-5条。",
        f"请用三个最有力的理由，说服一个没接触过{name}的人去认真阅读它。每个理由用一句话概括。",
    ]

    # 合并所有轮次，每轮之间加一个分隔标识（便于后续处理和展示）
    all_questions = []
    all_questions.append(("【第一轮：概览与框架】", round1))
    all_questions.append(("【第二轮：深度挖掘】", round2))
    all_questions.append(("【第三轮：综合与反刍】", round3))

    return all_questions

def ask_notebooklm(question, max_retries=1):
    """向 NotebookLM 提问并获取答案，带重试机制"""
    for attempt in range(max_retries + 1):
        result = subprocess.run(
            ['notebooklm', 'ask', question],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            answer = result.stdout.strip()
            if answer and len(answer) > 10:  # 有实质内容的回答才算成功
                return answer

        if attempt < max_retries:
            print(f"  重试中...", end=" ")
            time.sleep(2)

    print(f"⚠️ 提问失败（已重试{max_retries}次）", file=sys.stderr)
    return None

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

def ask_round(round_label, questions, title):
    """执行一轮提问，返回 (questions, answers) 列表"""
    print(f"\n📌 {round_label}")
    answers = []
    asked = []
    for i, q in enumerate(questions, 1):
        print(f"  [{i}/{len(questions)}] {q[:60]}...")
        answer = ask_notebooklm(q)
        if answer:
            print(f"  ✅ 回答长度: {len(answer)} 字符")
            answers.append(answer)
        else:
            print(f"  ⚠️ 跳过")
            answers.append("")
        asked.append(q)
        time.sleep(1.5)  # 避免请求过快
    return asked, answers


def deep_analysis(file_path, title, content_type, to_feishu=False):
    """深度分析模式：三轮递进提问"""
    print("\n" + "="*60)
    print("🔍 启动深度分析模式")
    print("="*60 + "\n")

    # 1. 上传到 NotebookLM
    print("📤 上传内容到 NotebookLM...")
    if not upload_to_notebooklm(file_path, title):
        return None

    print("⏳ 等待 NotebookLM 处理内容...")
    time.sleep(3)

    # 2. 生成三轮递进问题
    print("\n📝 生成深度分析问题...")
    rounds = generate_questions_progressive(content_type)
    total_questions = sum(len(qs) for _, qs in rounds)
    print(f"✅ 共 {len(rounds)} 轮 {total_questions} 个问题\n")

    # 3. 逐轮提问（NotebookLM 保持对话上下文，后轮受益于前轮回答）
    print("💬 开始三轮递进提问...\n")
    all_questions = []
    all_answers = []

    for round_label, questions in rounds:
        asked, answers = ask_round(round_label, questions, title)
        all_questions.extend(asked)
        all_answers.extend(answers)

    # 4. 返回结构化数据
    result = {
        "status": "success",
        "title": title,
        "content_type": content_type,
        "rounds": len(rounds),
        "questions": all_questions,
        "answers": all_answers,
        "total_questions": len(all_questions),
        "answered": len([a for a in all_answers if a]),
    }

    # 5. 如果指定了 --to-feishu，创建飞书文档
    if to_feishu:
        markdown = format_feishu_markdown(title, all_questions, all_answers)
        create_feishu_doc(f"{title} - 深度解读", markdown)

    return result

def main():
    if len(sys.argv) < 2:
        print("用法: main.py <输入路径或URL> [--deep-analysis] [--to-feishu]", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    deep_mode = '--deep-analysis' in sys.argv
    to_feishu = '--to-feishu' in sys.argv

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
            result = deep_analysis(txt_path, title, input_type)
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
            result = deep_analysis(str(doc_path), title, input_type)
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
            result_data = deep_analysis(txt_path, title, 'podcast')
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
            result_data = deep_analysis(txt_path, safe_title, 'x_twitter')
            if result_data:
                output_file = f"/tmp/{safe_title}_analysis.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result_data, f, ensure_ascii=False, indent=2)
                print(f"\n✅ 分析完成！结果已保存到: {output_file}")
        else:
            upload_to_notebooklm(txt_path, safe_title)

    elif input_type == 'url':
        print(f"🌐 处理 URL: {input_arg}")

        # 添加 URL 作为 source
        result = subprocess.run(
            ['notebooklm', 'source', 'add', input_arg],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ 添加失败: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        print("✅ URL 已添加到 NotebookLM")

        if deep_mode:
            title = input_arg.split('/')[-1] or 'web_content'
            print("⏳ 等待 NotebookLM 处理内容...")
            time.sleep(3)

            # 使用通用三轮递进提问
            rounds = generate_questions_progressive(input_type)
            total_questions = sum(len(qs) for _, qs in rounds)
            print(f"\n📝 开始提问（共 {total_questions} 个问题，{len(rounds)} 轮）...")

            all_questions = []
            all_answers = []
            for round_label, questions in rounds:
                asked, answers = ask_round(round_label, questions, title)
                all_questions.extend(asked)
                all_answers.extend(answers)

            result_data = {
                "status": "success",
                "title": title,
                "url": input_arg,
                "content_type": input_type,
                "rounds": len(rounds),
                "questions": all_questions,
                "answers": all_answers,
                "total_questions": len(all_questions),
                "answered": len([a for a in all_answers if a]),
            }

            if to_feishu:
                md = format_feishu_markdown(title, all_questions, all_answers)
                create_feishu_doc(f"{title} - 深度解读", md)

            output_file = f"/tmp/{title}_analysis.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ 分析完成！结果已保存到: {output_file}")

    else:
        print(f"❌ 不支持的输入类型: {input_type}", file=sys.stderr)
        print("提示: 请使用 EPUB、PDF、TXT、MD 文件或 URL", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
