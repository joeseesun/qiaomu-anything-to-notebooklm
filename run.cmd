@echo off
setlocal
set "SKILL_ROOT=%~dp0"
if not exist "%SKILL_ROOT%.venv\Scripts\python.exe" (
    echo Local environment missing. Run install.cmd first. 1>&2
    exit /b 1
)
set "PATH=%SKILL_ROOT%.venv\Scripts;%PATH%"
set "PYTHONIOENCODING=utf-8"
set "PLAYWRIGHT_BROWSERS_PATH=%SKILL_ROOT%.venv\browsers"
"%SKILL_ROOT%.venv\Scripts\python.exe" "%SKILL_ROOT%windows_entry.py" %*
exit /b %errorlevel%
