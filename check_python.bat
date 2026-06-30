@echo off
python --version > "%~dp0python_check.txt" 2>&1
if %errorlevel% == 0 (
    echo FOUND >> "%~dp0python_check.txt"
) else (
    echo NOT_FOUND >> "%~dp0python_check.txt"
)
