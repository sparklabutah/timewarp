@echo off
REM Start Wikinews application

echo Starting Wikinews UI...
echo Make sure you have Flask installed: pip install -r requirements.txt
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run the Flask app
python news_app.py
pause

