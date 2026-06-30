@echo off
echo Installing Stock Market Dashboard dependencies...
cd /d "%~dp0"
python -m pip install -r requirements.txt > "%~dp0install_log.txt" 2>&1
if %errorlevel% == 0 (
    echo SUCCESS >> "%~dp0install_log.txt"
    echo Install complete! You can close this window.
) else (
    echo FAILED >> "%~dp0install_log.txt"
    echo Install failed - check install_log.txt for details.
)
pause
