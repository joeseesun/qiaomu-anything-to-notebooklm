"""Offline regressions: no credentials, downloads, uploads, or external APIs."""
import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import check_env
import install
import main
import runtime_compat
import windows_entry


class InstallerTests(unittest.TestCase):
    def test_install_uses_only_local_environment_and_no_auth(self):
        with tempfile.TemporaryDirectory(prefix='notebooklm 中文 space ') as directory:
            root = Path(directory).resolve()
            mcp = root / 'wexin-read-mcp'
            (mcp / 'src').mkdir(parents=True)
            (mcp / 'src/server.py').touch()
            (mcp / 'requirements.txt').touch()
            (root / 'requirements.txt').touch()
            with patch('install.shutil.which', return_value='git'), patch('install.subprocess.run', return_value=subprocess.CompletedProcess([], 0, install.MCP_REVISION)) as run, contextlib.redirect_stdout(io.StringIO()) as output:
                install.install(root)
            calls = run.call_args_list
            python = str(root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python'))
            self.assertEqual(calls[0].args[0], [sys.executable, '-m', 'venv', str(root / '.venv')])
            pip_calls = [c.args[0] for c in calls if 'pip' in c.args[0]]
            self.assertEqual(len(pip_calls), 3)
            self.assertTrue(all(c[:3] == [python, '-m', 'pip'] for c in pip_calls))
            self.assertIn([python, '-m', 'playwright', 'install', 'chromium'], [c.args[0] for c in calls])
            self.assertTrue(all(c.kwargs['check'] for c in calls))
            self.assertTrue(all(c.kwargs['env']['PLAYWRIGHT_BROWSERS_PATH'] == str(root / '.venv/browsers') for c in calls))
            self.assertFalse(any('login' in c.args[0] or 'list' in c.args[0] for c in calls))
            text = output.getvalue()
            config = json.JSONDecoder().raw_decode(text[text.index('{'):])[0]
            self.assertEqual(config['mcpServers']['weixin-reader']['command'], python)

    def test_clone_missing_mcp_and_reuse_existing_venv(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            python = root / '.venv' / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
            python.parent.mkdir(parents=True)
            python.touch()
            def fake_run(args, **kwargs):
                if args[:2] == ['git', 'clone']:
                    (root / 'wexin-read-mcp/src').mkdir(parents=True)
                    (root / 'wexin-read-mcp/src/server.py').touch()
                return subprocess.CompletedProcess(args, 0, install.MCP_REVISION)
            with patch('install.shutil.which', return_value='git'), patch('install.subprocess.run', side_effect=fake_run) as run, contextlib.redirect_stdout(io.StringIO()):
                install.install(root)
            commands = [c.args[0] for c in run.call_args_list]
            self.assertEqual(commands[1][:2], ['git', 'clone'])
            self.assertIn(['git', '-C', str(root / 'wexin-read-mcp'), 'checkout', '--detach', install.MCP_REVISION], commands)
            self.assertFalse(any('venv' in c for c in commands))

    def test_existing_different_mcp_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            mcp = root / 'wexin-read-mcp'
            mcp.mkdir()
            sentinel = mcp / 'user-edits.txt'
            sentinel.write_text('keep me', encoding='utf-8')
            with patch('install.shutil.which', return_value='git'), patch('install.subprocess.run', return_value=subprocess.CompletedProcess([], 0, 'different-revision')) as run:
                with self.assertRaisesRegex(RuntimeError, 'left unchanged'):
                    install.install(root)
            self.assertEqual(sentinel.read_text(encoding='utf-8'), 'keep me')
            commands = [c.args[0] for c in run.call_args_list]
            self.assertFalse(any('checkout' in c or 'pip' in c for c in commands))

    def test_failure_stops_before_browser_install_or_success(self):
        with tempfile.TemporaryDirectory() as directory, patch('install.shutil.which', return_value='git'), patch('install.subprocess.run', side_effect=subprocess.CalledProcessError(7, 'fixture')), contextlib.redirect_stdout(io.StringIO()) as output:
            with self.assertRaises(subprocess.CalledProcessError):
                install.install(directory)
            self.assertNotIn('Installation complete', output.getvalue())

    def test_old_python_or_missing_git_fails_before_mutation(self):
        for version, git in [((3, 9), 'git'), ((3, 10), None)]:
            with patch('install.sys.version_info', version), patch('install.shutil.which', return_value=git), patch('install.subprocess.run') as run:
                with self.assertRaises(RuntimeError):
                    install.install('.')
                run.assert_not_called()


class RuntimeTests(unittest.TestCase):
    def test_both_gbk_streams_can_print_emoji(self):
        buffers = [io.BytesIO(), io.BytesIO()]
        streams = [io.TextIOWrapper(b, encoding='gbk') for b in buffers]
        with patch('runtime_compat.sys.platform', 'win32'), patch('runtime_compat.sys.stdout', streams[0]), patch('runtime_compat.sys.stderr', streams[1]):
            runtime_compat.configure_console()
            print('✅ 中文')
            print('❌ 错误', file=sys.stderr)
            for stream in streams:
                stream.flush()
        self.assertIn('✅ 中文', buffers[0].getvalue().decode('utf-8'))
        self.assertIn('❌ 错误', buffers[1].getvalue().decode('utf-8'))

    def test_redirected_string_streams_are_supported(self):
        with patch('runtime_compat.sys.platform', 'win32'), patch('runtime_compat.sys.stdout', io.StringIO()), patch('runtime_compat.sys.stderr', io.StringIO()):
            runtime_compat.configure_console()
            check_env.print_status('ok', 'fixture')

    def test_command_output_decodes_utf8_and_non_utf8_without_crash(self):
        actual_run = subprocess.run
        def fixture_run(args, **kwargs):
            self.assertEqual(kwargs['encoding'], 'utf-8')
            self.assertEqual(kwargs['errors'], 'replace')
            return actual_run([sys.executable, '-c', "import sys; sys.stdout.buffer.write('中文 ✅'.encode('utf-8') + b'\\xff')"], **kwargs)
        with patch('shutil.which', return_value='fixture'), patch('subprocess.run', side_effect=fixture_run), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(check_env.check_command('fixture'))
        self.assertIn('中文 ✅', output.getvalue())
        self.assertIn('\ufffd', output.getvalue())

    def test_auth_probe_only_with_mocked_command(self):
        with patch('subprocess.run', return_value=subprocess.CompletedProcess([], 1, '', 'fixture error')) as run, contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(check_env.check_notebooklm_auth())
            self.assertEqual(run.call_args.args[0], ['notebooklm', 'list'])
            self.assertEqual(run.call_args.kwargs['encoding'], 'utf-8')

    def test_broken_commands_are_not_reported_installed(self):
        failures = [subprocess.CompletedProcess([], 7, '', 'broken fixture'),
                    OSError('broken executable'), subprocess.TimeoutExpired('fixture', 5)]
        for failure in failures:
            kwargs = {'side_effect': failure} if isinstance(failure, Exception) else {'return_value': failure}
            with patch('shutil.which', return_value='fixture'), patch('subprocess.run', **kwargs), contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertFalse(check_env.check_command('fixture'))
            self.assertNotIn('已安装', output.getvalue())

    def test_upload_selects_created_notebook_and_stops_on_failure(self):
        for codes in [(0, 0), (7,), (0, 7)]:
            results = [subprocess.CompletedProcess([], code, '', 'fixture failure' if code else '') for code in codes]
            with patch('main.subprocess.run', side_effect=results) as run, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main.upload_to_notebooklm('中文 space.md', '中文 title'), codes == (0, 0))
            self.assertEqual(run.call_args_list[0].args[0], ['notebooklm', 'create', '中文 title', '--use'])
            self.assertEqual(run.call_count, len(codes))

    def test_document_upload_failure_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = Path(directory) / 'synthetic 中文.md'
            doc.write_text('synthetic test only', encoding='utf-8')
            for flags in [[], ['--deep-analysis']]:
                with patch('main.sys.argv', ['main.py', str(doc), *flags]), patch('main.upload_to_notebooklm', return_value=False), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        main.main()
                    self.assertEqual(error.exception.code, 1)

    def test_deep_analysis_writes_portable_path_with_invalid_title(self):
        with tempfile.TemporaryDirectory() as directory:
            doc = Path(directory) / 'fixture.md'
            doc.write_text('offline fixture', encoding='utf-8')
            with patch('main.sys.argv', ['main.py', str(doc), '--deep-analysis']), patch('main.deep_analysis', return_value={'answer': '中文'}), patch('main.tempfile.gettempdir', return_value=directory), contextlib.redirect_stdout(io.StringIO()):
                main.main()
            self.assertEqual(json.loads((Path(directory) / 'fixture_analysis.json').read_text(encoding='utf-8')), {'answer': '中文'})
            output = Path(main.analysis_output_path('bad:/\\<>*?"|\n'))
            self.assertFalse(any(char in output.name for char in '<>:"/\\|?*\n'))

    def test_podcast_child_uses_current_interpreter_utf8(self):
        fixture = {'txt_path': 'fixture.txt', 'title': '中文', 'content_length': 3}
        with patch('main.sys.argv', ['main.py', 'https://xiaoyuzhoufm.com/episode/fixture']), patch('main.subprocess.run', return_value=subprocess.CompletedProcess([], 0, json.dumps(fixture), '')) as run, patch('main.upload_to_notebooklm') as upload, contextlib.redirect_stdout(io.StringIO()):
            main.main()
        self.assertEqual(run.call_args.args[0][:3], [sys.executable, '-X', 'utf8'])
        self.assertEqual(run.call_args.kwargs['encoding'], 'utf-8')
        upload.assert_called_once_with('fixture.txt', '中文')

    def test_dispatch_preserves_spaced_arguments_and_exit_codes(self):
        for args in [['C:\\中文 path\\fixture.pdf'], ['notebooklm', 'source', 'add', 'C:\\中文 path\\fixture.pdf'], ['check-env']]:
            with patch('windows_entry.subprocess.run', return_value=subprocess.CompletedProcess([], 7)) as run:
                self.assertEqual(windows_entry.main(args), 7)
            command = run.call_args.args[0]
            if args[0] == 'notebooklm':
                self.assertEqual(Path(command[0]).name, 'notebooklm.exe')
                self.assertEqual(command[1:], args[1:])
            elif args[0] == 'check-env':
                self.assertEqual(Path(command[1]).name, 'check_env.py')
            else:
                self.assertEqual(command[2:], args)

    @unittest.skipUnless(os.name == 'nt', 'requires Windows CMD and PowerShell')
    def test_native_launchers_from_other_directory_with_unicode_spaces(self):
        source = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory(prefix='notebooklm 中文 space ') as directory:
            root = Path(directory) / 'checkout 中文 space'
            root.mkdir()
            for name in ['install.cmd', 'install.py', 'run.cmd', 'windows_entry.py', 'main.py', 'runtime_compat.py']:
                shutil.copy(source / name, root / name)
            # --help must not create a venv, download anything, or authenticate.
            result = subprocess.run(['cmd', '/d', '/c', str(root / 'install.cmd'), '--help'], cwd=directory, capture_output=True, encoding='utf-8', errors='replace')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((root / '.venv').exists())
            missing = subprocess.run(['cmd', '/d', '/c', str(root / 'run.cmd'), '--help'], cwd=directory, capture_output=True)
            self.assertEqual(missing.returncode, 1)
            subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(root / '.venv')], check=True)
            for shell in [
                ['cmd', '/d', '/c', str(root / 'run.cmd'), '--help'],
                ['powershell', '-NoProfile', '-Command', "& '" + str(root / 'run.cmd').replace("'", "''") + "' --help; exit $LASTEXITCODE"]
            ]:
                result = subprocess.run(shell, cwd=directory, capture_output=True, encoding='utf-8', errors='replace')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('main.py', result.stdout)
            # A failing child must retain its exit status in CMD and PowerShell.
            (root / 'main.py').write_text('import sys; sys.exit(7)', encoding='utf-8')
            for shell in [
                ['cmd', '/d', '/c', str(root / 'run.cmd'), 'fixture'],
                ['powershell', '-NoProfile', '-Command', "& '" + str(root / 'run.cmd').replace("'", "''") + "' fixture; exit $LASTEXITCODE"]
            ]:
                self.assertEqual(subprocess.run(shell, cwd=directory, capture_output=True).returncode, 7)


if __name__ == '__main__':
    unittest.main()
