#!/usr/bin/env python3
"""
qiaomu-anything-to-notebooklm - 多源内容智能处理器
自动识别输入类型，上传到 NotebookLM 并生成指定格式
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def detect_input_type(input_path):
    """检测输入类型"""
    if input_path.startswith('http'):
        if 'mp.weixin.qq.com' in input_path:
            return 'weixin'
        elif 'youtube.com' in input_path or 'youtu.be' in input_path:
            return 'youtube'
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

def main():
    if len(sys.argv) < 2:
        print("用法: main.py <输入路径或URL>", file=sys.stderr)
        sys.exit(1)

    input_arg = sys.argv[1]
    input_type = detect_input_type(input_arg)

    print(f"📋 检测到输入类型: {input_type}")

    # 根据类型处理
    if input_type == 'epub':
        epub_path = Path(input_arg).expanduser()
        print(f"📚 处理 EPUB: {epub_path.name}")

        # 提取文本
        txt_path = extract_epub_to_txt(epub_path)
        print(f"✅ 文本已提取: {txt_path}")

        # 上传到 NotebookLM
        title = epub_path.stem
        upload_to_notebooklm(txt_path, title)

    elif input_type == 'document':
        doc_path = Path(input_arg).expanduser()
        print(f"📄 处理文档: {doc_path.name}")

        # 直接上传
        title = doc_path.stem
        upload_to_notebooklm(str(doc_path), title)

    elif input_type == 'url':
        print(f"🌐 处理 URL: {input_arg}")
        # URL 可以直接传给 NotebookLM
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
