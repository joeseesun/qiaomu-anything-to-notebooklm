"""Exercise the actual share archive, including runtime imports after extraction."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest


@unittest.skipUnless(os.name != 'nt' and shutil.which('bash'), 'packager requires Bash')
class PackageTests(unittest.TestCase):
    def test_archive_contains_runtime_and_no_local_environments(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='package 中文 space ') as directory:
            root = Path(directory)
            subprocess.run(['bash', str(source / 'package.sh'), '.'], cwd=root, check=True, capture_output=True)
            archive, = root.glob('*.tar.gz')
            with tarfile.open(archive) as tar:
                names = tar.getnames()
                self.assertFalse(any('/.venv/' in name or '/.git/' in name for name in names))
                tar.extractall(root)
            unpacked = root / 'qiaomu-anything-to-notebooklm'
            for name in ['install.cmd', 'run.cmd', 'install.py', 'windows_entry.py',
                         'runtime_compat.py', 'main.py', 'scripts/get_podcast_transcript.py', 'scripts/fetch_url.sh']:
                self.assertTrue((unpacked / name).is_file(), name)
            result = subprocess.run([sys.executable, '-c', 'import check_env, main, install, windows_entry; main.sys.argv=["main.py", "--help"]; main.main()'],
                                    cwd=unpacked, capture_output=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('main.py', result.stdout)


if __name__ == '__main__':
    unittest.main()
