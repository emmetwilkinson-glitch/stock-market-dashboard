@echo off
echo Adding Python Scripts to PATH...
setx PATH "%PATH%;C:\Users\Emmet Wilkinson\AppData\Local\Python\pythoncore-3.14-64\Scripts;C:\Users\Emmet Wilkinson\AppData\Local\Python\pythoncore-3.14-64" > "%~dp0path_log.txt" 2>&1
echo DONE >> "%~dp0path_log.txt"
echo Path updated. Please close and reopen any Command Prompt windows.
pause
