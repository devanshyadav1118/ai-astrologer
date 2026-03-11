#!/usr/bin/env python3
"""
Setup script for Astrological PDF Extraction Automation
"""

import subprocess
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required. Current version:", sys.version)
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required Python packages."""
    try:
        print("📦 Installing Python dependencies...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "../requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_gemini_cli():
    """Check if Gemini access is available via env API key or Gemini CLI."""
    if os.getenv("GEMINI_API_KEY", "").strip():
        print("✅ GEMINI_API_KEY found in environment")
        print("✅ Extraction can use Python API authentication")
        return True

    try:
        # Check if gemini command exists
        result = subprocess.run(["gemini", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Gemini CLI found")
            
            # Test authentication
            auth_result = subprocess.run(["gemini", "chat", "--model", "flash", "--help"], 
                                       capture_output=True, text=True, timeout=10)
            if auth_result.returncode == 0:
                print("✅ Gemini CLI appears to be authenticated")
                return True
            else:
                print("⚠️  Gemini CLI found but may need authentication")
                print("Set GEMINI_API_KEY or run: gemini login")
                return False
        else:
            print("❌ Gemini CLI not found or not working")
            return False
    except FileNotFoundError:
        print("❌ Gemini CLI not found")
        print("Please set GEMINI_API_KEY or install Gemini CLI and run 'gemini login'")
        return False
    except Exception as e:
        print(f"❌ Error checking Gemini CLI: {e}")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        Path("../input"),
        Path("../output"),
        Path("../logs")
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def create_sample_files():
    """Create sample files for testing."""
    input_dir = Path("../input")
    
    # Create a sample README
    readme_content = """# Astrological PDF Extraction Automation

## Setup Instructions

1. Place your astrology PDF in the `input/` folder as `astrology_full_book.pdf`
2. Set `GEMINI_API_KEY` in your environment, or ensure Gemini CLI is installed and authenticated: `gemini login`
3. Run the extraction: `cd scripts && python process_pdf_chapters.py`

## Output Structure

The system will create:
- `output/Chapter_XX_Title/flash_output.txt` - Extracted rules
- `output/Chapter_XX_Title/prompt.txt` - Original prompt used
- `output/Chapter_XX_Title/metadata.json` - Chapter information
- `extraction.log` - Processing logs

## Features

- Automatic chapter detection and splitting
- Structured JSON extraction using enhanced prompts
- Support for rules, descriptions, calculations, and yogas
- Audit trail with prompts and metadata
- Comprehensive logging and error handling
"""
    
    readme_path = Path("../README.md")
    readme_path.write_text(readme_content, encoding='utf-8')
    print("✅ Created README.md")

def main():
    """Main setup function."""
    print("🚀 Setting up Astrological PDF Extraction Automation")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check Gemini CLI
    if not check_gemini_cli():
        print("\n📋 Next steps:")
        print("1. Preferred: set GEMINI_API_KEY in your environment")
        print("2. Or install Gemini CLI: https://ai.google.dev/gemini-api/docs/quickstart")
        print("3. Authenticate: gemini login")
    
    # Create directories
    create_directories()
    
    # Create sample files
    create_sample_files()
    
    print("\n🎉 Setup completed!")
    print("\n📋 To get started:")
    print("1. Place your astrology PDF in input/astrology_full_book.pdf")
    print("2. Run: cd scripts && python process_pdf_chapters.py")

if __name__ == "__main__":
    main() 
