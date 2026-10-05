"""Dispatch Windows commands using the same local environment as the installer."""
from pathlib import Path
import subprocess
import sys


def main(args=None):
    args = sys.argv[1:] if args is None else args
    root = Path(__file__).resolve().parent
    if args and args[0] == 'notebooklm':
        command = [str(Path(sys.executable).parent / 'notebooklm.exe'), *args[1:]]
    elif args and args[0] == 'check-env':
        command = [sys.executable, str(root / 'check_env.py'), *args[1:]]
    else:
        command = [sys.executable, str(root / 'main.py'), *args]
    try:
        return subprocess.run(command).returncode
    except OSError as error:
        print(f'Unable to start command: {error}. Rerun install.cmd.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
