@echo off
REM Start Wikinews application

REM Change to the directory where this script is located
cd /d "%~dp0"

REM Determine theme
set THEME_ARG=-1
set THEME_NAME=Classic (Modern News UI) [default]

if "%1"=="-1" (
    set THEME_ARG=-1
    set THEME_NAME=Classic (Modern News UI)
)
if "%1"=="-2" (
    set THEME_ARG=-2
    set THEME_NAME=Modern (Dark/Light mode)
)
if "%1"=="-3" (
    set THEME_ARG=-3
    set THEME_NAME=Wikinews 2002 (Retro)
)
if "%1"=="-4" (
    set THEME_ARG=-4
    set THEME_NAME=Wikinews 2001 (Ultra-Retro)
)

echo ========================================
echo Wikinews UI
echo ========================================
echo.
echo Working directory: %~dp0
echo Theme: %THEME_NAME%
echo Starting the Wikinews reader...
echo This may take a few minutes on first run to index articles.
echo.
echo Usage: start_news.bat [-1^|-2^|-3^|-4]
echo   -1: Classic theme (Modern News UI)
echo   -2: Modern theme (Dark/Light mode)
echo   -3: Wikinews 2002 (Retro theme)
echo   -4: Wikinews 2001 (Ultra-Retro theme)
echo.
echo Make sure you have Flask installed: pip install -r requirements.txt
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the Flask app
python news_app.py %THEME_ARG%
pause

