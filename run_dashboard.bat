@echo off
cd /d "%~dp0"
echo Starting Stock Market Analyst Dashboard...
echo The dashboard will open in your browser automatically.
echo Press Ctrl+C in this window to stop the dashboard.
echo.
"C:\Users\Emmet Wilkinson\AppData\Local\Python\pythoncore-3.14-64\Scripts\streamlit.exe" run app.py
pause
