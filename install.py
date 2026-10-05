#!/usr/bin/env python3
"""Install into a repository-local environment; never log in or edit user config."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

MIN_PYTHON = (3, 10)  # notebooklm-py requires Python >=3.10


def install(root):
    if sys.version_info < MIN_PYTHON:
        raise RuntimeError('Python 3.10+ is required. Install it and rerun install.cmd.')
    if not shutil.which('git'):
        raise RuntimeError('Git is required. Install Git for Windows and reopen your terminal.')
    root = Path(root).resolve()
    venv = root / '.venv'
    python = venv / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PLAYWRIGHT_BROWSERS_PATH'] = str(venv / 'browsers')

    def run(args):
        subprocess.run([str(arg) for arg in args], check=True, env=env, cwd=root)

    if not python.is_file():
        run([sys.executable, '-m', 'venv', venv])
    # Check an existing environment too; an old .venv must not mask the version gate.
    run([python, '-c', 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'])
    mcp = root / 'wexin-read-mcp'
    if not mcp.exists():
        run(['git', 'clone', 'https://github.com/Bwkyd/wexin-read-mcp.git', mcp])
    if not (mcp / 'src/server.py').is_file():
        raise RuntimeError('Incomplete wexin-read-mcp checkout: src/server.py is missing.')
    run([python, '-m', 'pip', 'install', '-r', root / 'requirements.txt'])
    if (mcp / 'requirements.txt').is_file():
        run([python, '-m', 'pip', 'install', '-r', mcp / 'requirements.txt'])
    run([python, '-m', 'pip', 'install', 'notebooklm-py[browser]'])
    run([python, '-m', 'playwright', 'install', 'chromium'])
    scripts = python.parent
    run([scripts / ('notebooklm.exe' if os.name == 'nt' else 'notebooklm'), '--version'])
    print('Installation complete. Add this MCP entry to your Claude configuration manually:')
    print(json.dumps({'mcpServers': {'weixin-reader': {
        'command': str(python), 'args': [str(mcp / 'src/server.py')],
        'env': {'PLAYWRIGHT_BROWSERS_PATH': env['PLAYWRIGHT_BROWSERS_PATH']}
    }}}, ensure_ascii=True, indent=2))
    print('On Windows, use run.cmd notebooklm login when you are ready to authenticate.')
    print('Then use run.cmd check-env or run.cmd "C:\\path\\to\\document.pdf".')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        install(Path(__file__).parent)
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(f'Installation failed: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
