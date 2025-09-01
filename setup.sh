#!/bin/bash
echo "Setting up Fuzzy Match Tool environment..."

# Create virtual environment
python3 -m venv fuzzy_env

# Activate virtual environment
source fuzzy_env/bin/activate

# Install required packages
pip install pandas>=2.0.0
pip install fuzzywuzzy>=0.18.0
pip install python-Levenshtein>=0.21.0
pip install customtkinter>=5.2.0
pip install openpyxl>=3.0.0
pip install pillow>=10.0.0
pip install jellyfish>=1.0.0
pip install scikit-learn>=1.7.0

echo "Setup completed successfully!"
echo "To activate the environment, run: source fuzzy_env/bin/activate"
echo "To run the application, run: python main.py"
