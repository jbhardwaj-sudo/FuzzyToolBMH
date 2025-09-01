@echo off
ECHO Setting up Fuzzy Match Tool environment...

REM Create virtual environment
python -m venv fuzzy_env

REM Activate virtual environment
CALL fuzzy_env\Scripts\activate.bat

REM Install required packages
pip install pandas>=2.0.0
pip install fuzzywuzzy>=0.18.0
pip install python-Levenshtein>=0.21.0
pip install customtkinter>=5.2.0
pip install openpyxl>=3.0.0
pip install pillow>=10.0.0
pip install jellyfish>=1.0.0
pip install scikit-learn>=1.7.0

ECHO Setup completed successfully!
ECHO To activate the environment, run: .\fuzzy_env\Scripts\activate
ECHO To run the application, run: python main.py

pause
