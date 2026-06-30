@echo off
echo Searching for Python...
where python > "%~dp0find_python.txt" 2>&1
where python3 >> "%~dp0find_python.txt" 2>&1
where py >> "%~dp0find_python.txt" 2>&1
py --version >> "%~dp0find_python.txt" 2>&1
py -m pip --version >> "%~dp0find_python.txt" 2>&1
echo DONE >> "%~dp0find_python.txt"
