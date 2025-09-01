import sys
import os

# Add the project root directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.gui.app import FuzzyMatchApp

def main():
    """Main entry point for the application."""
    try:
        app = FuzzyMatchApp()
        app.run()
    except Exception as e:
        print(f"Error starting application: {str(e)}")
        raise

if __name__ == "__main__":
    main()
