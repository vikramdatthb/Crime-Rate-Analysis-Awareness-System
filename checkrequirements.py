import subprocess
import sys
import importlib.util
import os

# List of required packages
required_packages = [
    "flask",
    "pandas",
    "numpy",
    "folium",
    "geopy",
    "flask_cors",
    "plotly",
    "dash",
    "scikit-learn",
    "matplotlib",
    "seaborn"
]

def check_package(package_name):
    """Check if a package is installed"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package_name):
    """Install a package using pip"""
    print(f"Installing {package_name}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
    print(f"{package_name} installed successfully.")

def main():
    """Check and install required packages"""
    print("Checking required packages...")
    
    for package in required_packages:
        if not check_package(package):
            print(f"{package} is not installed.")
            install_package(package)
        else:
            print(f"{package} is already installed.")
    
    print("All required packages are installed.")

if __name__ == "__main__":
    main()
