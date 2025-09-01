@echo off
echo 🚀 Starting Fuzzy Match Tool...
echo.
echo Activating virtual environment...
call fuzzy_env\Scripts\activate.bat

echo Starting application...
streamlit run fuzzy_match_app.py

pause
