@echo off
REM Change to the directory where this batch file is located
cd /d "%~dp0"

REM Determine theme
set THEME_ARG=-1
set THEME_NAME=Classic (Wikipedia-style) [default]

if "%1"=="-1" (
    set THEME_ARG=-1
    set THEME_NAME=Classic (Wikipedia-style)
)
if "%1"=="-2" (
    set THEME_ARG=-2
    set THEME_NAME=Modern (Dark/Light mode)
)
if "%1"=="-3" (
    set THEME_ARG=-3
    set THEME_NAME=Wikipedia 2002 (Retro)
)
if "%1"=="-4" (
    set THEME_ARG=-4
    set THEME_NAME=Wikipedia 2001 (Ultra-Retro)
)

echo ========================================
echo Simple Wikipedia UI
echo ========================================
echo.
echo Working directory: %CD%
echo Theme: %THEME_NAME%
echo Starting the Wikipedia reader...
echo This may take a few minutes on first run to index articles.
echo.
echo Usage: start_wiki.bat [-1^|-2^|-3^|-4]
echo   -1: Classic theme (Wikipedia-style)
echo   -2: Modern theme (Dark/Light mode)
echo   -3: Wikipedia 2002 (Retro theme)
echo   -4: Wikipedia 2001 (Ultra-Retro theme)
echo.
python wiki_app.py %THEME_ARG%
pause

