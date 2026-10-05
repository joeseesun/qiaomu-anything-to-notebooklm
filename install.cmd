@echo off
setlocal
rem Probe real interpreters, avoiding Windows Store aliases and old Python versions.
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 "%~dp0install.py" %*
    exit /b
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    python "%~dp0install.py" %*
    exit /b
)
python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 (
    python3 "%~dp0install.py" %*
    exit /b
)
echo Python 3.10+ was not found. Install Python for Windows and reopen this terminal. 1>&2
exit /b 1
