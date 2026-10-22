"""Installed-stack smoke test: synthetic files only, no login or upload.

Run with .venv's Python after install.py. Browser pages use set_content; MCP
only initializes and lists tools. NotebookLM is tested with an empty state
directory and must reject a synthetic upload before any account request.
"""
import asyncio
from importlib.metadata import version
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


async def mcp_handshake(env):
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server = StdioServerParameters(
        command=sys.executable,
        args=[str(ROOT / 'wexin-read-mcp/src/server.py')], env=env, cwd=str(ROOT))
    with anyio.fail_after(30):
        async with stdio_client(server) as (reader, writer):
            async with ClientSession(reader, writer) as session:
                await session.initialize()
                tools = await session.list_tools()
                assert 'read_weixin_article' in [tool.name for tool in tools.tools]
    print('PASS MCP stdio initialize/tools-list (no tool invocation)')


def main():
    with tempfile.TemporaryDirectory(prefix='installed 中文 space ') as directory:
        temp = Path(directory)
        env = {k: v for k, v in os.environ.items() if not k.startswith('NOTEBOOKLM_')}
        env.update(NOTEBOOKLM_HOME=str(temp / 'empty-auth'), PYTHONIOENCODING='utf-8',
                   PLAYWRIGHT_BROWSERS_PATH=str(ROOT / '.venv/browsers'),
                   FASTMCP_CHECK_FOR_UPDATES='off')
        env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
        # Also apply isolation to in-process imports and the browser.
        for key in list(os.environ):
            if key.startswith('NOTEBOOKLM_'):
                del os.environ[key]
        os.environ.update(env)

        def run(args, expected=0):
            command = args if isinstance(args, str) else [str(a) for a in args]
            result = subprocess.run(command, env=env, cwd=temp,
                                    capture_output=True, encoding='utf-8', errors='replace', timeout=60)
            assert result.returncode == expected, (args, result.returncode, result.stdout, result.stderr)
            return result

        scripts = Path(sys.executable).parent
        cli = scripts / ('notebooklm.exe' if os.name == 'nt' else 'notebooklm')
        run([sys.executable, '-m', 'pip', 'check'])
        run([cli, '--version'])
        assert '--use' in run([cli, 'create', '--help']).stdout
        assert '--title' in run([cli, 'source', 'add', '--help']).stdout
        print('PASS pip check and NotebookLM CLI contract:', version('notebooklm-py'))
        print('Installed Python:', sys.version.split()[0])
        expected_python = env.get('SMOKE_EXPECT_PYTHON')
        if expected_python:
            assert sys.version.startswith(expected_python + '.'), sys.version

        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_content('<html><body><h1>合成测试 ✅</h1></body></html>')
            assert page.locator('h1').inner_text() == '合成测试 ✅'
            browser.close()
        print('PASS downloaded Chromium launch and synthetic DOM')

        from ebooklib import epub
        import main as app
        book = epub.EpubBook()
        book.set_identifier('synthetic-test-only')
        book.set_title('合成测试')
        book.set_language('zh')
        chapter = epub.EpubHtml(title='测试', file_name='chapter.xhtml', lang='zh')
        chapter.content = '<h1>合成 EPUB ✅</h1><p>No user documents.</p>'
        book.add_item(chapter)
        book.toc = [chapter]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = [chapter]
        source = temp / '合成 space.epub'
        epub.write_epub(str(source), book)
        extracted = Path(app.extract_epub_to_txt(source))
        try:
            assert '合成 EPUB ✅' in extracted.read_text(encoding='utf-8')
        finally:
            extracted.unlink()
        html = temp / '合成 space.html'
        html.write_text('<html><head><meta charset="utf-8"></head><body><h1>合成转换</h1></body></html>', encoding='utf-8')
        markdown = temp / 'converted.md'
        converter = scripts / ('markitdown.exe' if os.name == 'nt' else 'markitdown')
        run([converter, html, '-o', markdown])
        assert '合成转换' in markdown.read_text(encoding='utf-8')
        print('PASS synthetic EPUB extraction and markitdown conversion')

        asyncio.run(mcp_handshake(env))
        document = temp / '合成 upload must fail.md'
        document.write_text('Synthetic smoke test. No account or user data.', encoding='utf-8')
        if os.name == 'nt':
            # CMD needs an outer pair when both the batch path and argument
            # are quoted. list2cmdline applies C-runtime quoting, not CMD's.
            result = run(f'cmd.exe /d /s /c ""{ROOT / "run.cmd"}" "{document}""', expected=1)
        else:
            result = run([sys.executable, ROOT / 'main.py', document], expected=1)
        assert '创建笔记本失败' in result.stderr, result.stderr
        assert '已上传到 NotebookLM' not in result.stdout
        assert not list((temp / 'empty-auth').rglob('storage_state.json'))
        print('PASS empty-auth synthetic upload rejected with exit 1 (no login/upload)')
        print('Versions:', {name: version(name) for name in ['fastmcp', 'playwright', 'ebooklib', 'markitdown']})


if __name__ == '__main__':
    main()
