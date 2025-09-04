# Fuzzy Match Tool 🔍

A powerful and user-friendly tool for fuzzy matching across datasets with an intuitive graphical interface. This tool helps you match similar entries between two Excel files, even when they contain typos, different formatting, or slight variations.

## 📋 Table of Contents
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation Guide](#installation-guide)
- [Running the Application](#running-the-application)
- [Using the Tool](#using-the-tool)
  - [Configuration Tab](#configuration-tab)
  - [Matching Tab](#matching-tab)
  - [Geo Level Refinement Tab](#geo-level-refinement-tab)
- [Understanding the Algorithms](#understanding-the-algorithms)
- [Tips for Better Matching](#tips-for-better-matching)
- [Troubleshooting](#troubleshooting)

## ✨ Features

- **User-friendly GUI**: Easy-to-use interface with clear navigation tabs
- **Multiple Matching Algorithms**: 
  - Levenshtein (for typos and spelling mistakes)
  - Jaro-Winkler (for names and brands)
  - Jaccard (for addresses and word overlap)
  - Cosine (for longer text)
  - Soundex (for phonetic matching)
- **Customizable Weights**: Adjust how much each algorithm influences the final match
- **Geographic Distance Matching**: Filter matches based on location proximity
- **Excel File Support**: Works with .xlsx and .csv files
- **Detailed Match Results**: Get comprehensive match scores and details

## 🔧 Prerequisites

Before you begin, make sure you have:
1. **Python**: Version 3.8 or higher installed on your computer
   - [Download Python](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
   - To verify installation, open Command Prompt and type: `python --version`

2. **Windows OS**: The tool is optimized for Windows operating system

## 📥 Installation Guide

1. **Download the Project**
   - Download this project as a ZIP file
   - Extract it to a location on your computer (e.g., Desktop)
   - Remember the path where you extracted it

2. **Set Up Virtual Environment**
   
   Open Command Prompt (CMD) as administrator and follow these steps:
   ```bash
   # First, go to the project folder
   # Replace "path_to_your_extracted_folder" with your actual path
   cd "path_to_your_extracted_folder\fuzzy-match-tool"

   # Create a virtual environment
   python -m venv fuzzy_env

   # Activate the virtual environment
   .\fuzzy_env\Scripts\activate
   ```
   
   You should see `(fuzzy_env)` at the start of your command line

3. **Install Required Packages**
   
   With the virtual environment activated (you should see `(fuzzy_env)` at the start of your command line), run each of these commands:
   ```bash
   pip install pandas
   pip install fuzzywuzzy
   pip install python-Levenshtein
   pip install numpy
   pip install customtkinter
   pip install openpyxl
   pip install pillow
   pip install geopy
   pip install openrouteservice
   ```

   Wait for each package to install completely before running the next command.

## 🚀 Running the Application

1. Make sure you're in the project directory with the virtual environment activated:
   ```bash
   # If you need to activate the environment again:
   .\fuzzy_env\Scripts\activate

   # Run the application
   python main.py
   ```

2. The application window should appear with three tabs:
   - Configuration
   - Matching
   - Geo Level Refinement

## 📱 Using the Tool

### Configuration Tab

1. **Primary Matching Algorithm**
   - Choose 'weighted' (recommended for beginners)
   - The weighted option combines all algorithms for better results

2. **Algorithm Weights** 
   - Use the sliders to set importance of each algorithm (0-5)
   - Start with these recommended weights:
     - Levenshtein: 2 (good for typos)
     - Jaro-Winkler: 2 (good for names)
     - Jaccard: 1
     - Cosine: 1
     - Soundex: 1

3. **Match Threshold**
   - Start with 80
   - Higher number = stricter matching
   - Lower number = more matches but less accurate

4. **Maximum Matches**
   - Recommended: Start with 3
   - This limits how many matches you get per entry

### Matching Tab

1. **Loading Your Files**
   - Click "Browse" next to Source File
   - Select your main Excel file
   - Click "Browse" next to Reference File
   - Select the file you want to match against
   - Both files should be either .xlsx or .csv

2. **Matching Columns**
   - Select a column from your Source file
   - Select the matching column from your Reference file
   - Set Weight (importance): Start with 1.0
   - Set Threshold: Start with 80
   - Click "Add Column Pair"
   - Repeat for all columns you want to match

3. **Running the Match**
   - Double-check your selections
   - Click "Run Matching"
   - Choose where to save your results file
   - Wait for the process to complete

### Geo Level Refinement Tab

1. **Setting Up**
   - Select your address column from Source file
   - Select your address column from Reference file
   - Enter maximum distance (start with 10 miles)

2. **Running Refinement**
   - Click "Apply Geo Refinement"
   - Wait for processing
   - Save your refined results

## 🧮 Understanding the Algorithms

1. **Levenshtein** (Best for Typos)
   - Good for: Names, simple words
   - Example: "John" matches "Jhon"
   - Use higher weight for: Customer names, product names

2. **Jaro-Winkler** (Best for Names)
   - Good for: Company names, brand names
   - Example: "McDonald's" matches "McDonalds"
   - Use higher weight for: Company names, brand names

3. **Jaccard** (Best for Addresses)
   - Good for: Text with different word orders
   - Example: "123 Main Street" matches "Main St 123"
   - Use higher weight for: Addresses, descriptions

4. **Cosine** (Best for Long Text)
   - Good for: Long descriptions
   - Example: Product descriptions, company profiles
   - Use higher weight for: Detailed text fields

5. **Soundex** (Best for Similar Sounds)
   - Good for: Names that sound alike
   - Example: "Smith" matches "Smyth"
   - Use higher weight for: Last names, phonetic matching

## 💡 Tips for Better Matching

1. **Prepare Your Data**
   - Make sure your Excel files are closed
   - Remove extra spaces from your data
   - Fix obvious typos
   - Make sure addresses are in similar format

2. **Start Simple**
   - Begin with just one or two important columns
   - Use the 'weighted' algorithm
   - Start with recommended weights
   - Test with a small sample first

3. **Improve Results**
   - If too many matches: Increase threshold
   - If too few matches: Lower threshold
   - If wrong matches: Adjust algorithm weights
   - Add more columns for better accuracy

## ❗ Troubleshooting

1. **Program Won't Start**
   - Make sure Python is installed
   - Check if you're in the right folder
   - Verify virtual environment is activated
   - Try reinstalling the packages

2. **Can't Load Files**
   - Close Excel files first
   - Check file format (.xlsx or .csv)
   - Make sure you have read permission
   - Try saving files as .xlsx

3. **No Matches Found**
   - Lower your threshold
   - Check column selections
   - Verify data in both files
   - Try with fewer columns first

4. **Error Messages**
   ```bash
   # If you see "pip not found":
   python -m pip install --upgrade pip

   # If packages fail to install:
   pip install --upgrade setuptools wheel
   ```

5. **Geo Refinement Not Working**
   - Check internet connection
   - Verify address format
   - Try with fewer records first

## 📫 Need Help?

If you're still having problems:
1. Check all steps in this guide
2. Make sure all packages are installed
3. Try with a small test file first
4. Check your Python version
5. Restart your computer

---

Remember:
- Always backup your data before matching
- Start with small test files
- Verify your matches manually
- Save your configurations if they work well

*Happy Matching! 🎯*
