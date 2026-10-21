@echo off
setlocal
cd /d "%~dp0"
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 run_demo.py
    goto finished
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>&1
if not errorlevel 1 (
    python run_demo.py
    goto finished
)
echo Python 3.10 or newer was not found.
echo Install Python, then run this file again.
echo You can open demo_reports HTML files without Python.
:finished
pause
endlocal
