@echo off
cd /d "%~dp0"
echo ========================================
echo  Pushing Stock Market Dashboard to GitHub
echo ========================================
echo.

echo Initializing git repository...
git init
if %errorlevel% neq 0 (echo ERROR: git init failed & pause & exit /b 1)

echo Adding all files...
git add .
if %errorlevel% neq 0 (echo ERROR: git add failed & pause & exit /b 1)

echo Committing...
git commit -m "Initial commit: Stock Market Analyst dashboard"
if %errorlevel% neq 0 (echo ERROR: git commit failed & pause & exit /b 1)

echo Setting branch to main...
git branch -M main
if %errorlevel% neq 0 (echo ERROR: git branch failed & pause & exit /b 1)

echo Adding remote origin...
git remote remove origin 2>nul
git remote add origin https://github.com/emmetwilkinson-glitch/stock-market-dashboard.git
if %errorlevel% neq 0 (echo ERROR: git remote add failed & pause & exit /b 1)

echo.
echo Pushing to GitHub...
echo (A browser window may open asking you to sign in to GitHub - please do so)
echo.
git push -u origin main
if %errorlevel% neq 0 (
    echo.
    echo Push failed. Trying with credential prompt...
    git push -u origin main
)

echo.
echo ========================================
if %errorlevel% == 0 (
    echo  SUCCESS! Code pushed to GitHub.
    echo  https://github.com/emmetwilkinson-glitch/stock-market-dashboard
) else (
    echo  FAILED. Check output above for errors.
)
echo ========================================
pause
