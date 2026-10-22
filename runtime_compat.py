"""Windows console support based on rice5's encoding fix in community PR #5."""
import sys


def configure_console():
    if sys.platform == 'win32':
        for stream in (sys.stdout, sys.stderr):
            if hasattr(stream, 'reconfigure'):
                stream.reconfigure(encoding='utf-8', errors='replace')
