import os
import subprocess
import sys

def check_requirements():
    """Run the checkrequirements.py script"""
    print("Checking required packages...")
    subprocess.call([sys.executable, "checkrequirements.py"])

def generate_data():
    """Run the generate_data.py script if the data file doesn't exist"""
    if not os.path.exists('crime_data.csv'):
        print("Generating crime data...")
        subprocess.call([sys.executable, "generate_data.py"])
    else:
        print("Crime data already exists.")

def run_app():
    """Run the Flask application"""
    print("Starting the Flask application...")
    subprocess.call([sys.executable, "app.py"])

if __name__ == "__main__":
    # Check if the required packages are installed
    check_requirements()
    
    # Generate data if needed
    generate_data()
    
    # Run the Flask application
    run_app()
