#!/usr/bin/env python3
"""
Command Line Interface for Astrological PDF Extraction Automation
"""

import argparse
import sys
from pathlib import Path
import subprocess
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(cmd: str, description: str) -> bool:
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False

def check_environment() -> bool:
    """Check if the environment is properly set up."""
    print("🔍 Checking environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # Check if required files exist
    required_files = [
        "process_pdf_chapters.py",
        "validate_output.py",
        "setup.py"
    ]
    
    for file in required_files:
        if not Path(file).exists():
            print(f"❌ Required file not found: {file}")
            return False
    
    # Check if input directory exists
    if not Path("../input").exists():
        print("⚠️  Input directory not found, creating...")
        Path("../input").mkdir(exist_ok=True)
    
    # Check if output directory exists
    if not Path("../output").exists():
        print("⚠️  Output directory not found, creating...")
        Path("../output").mkdir(exist_ok=True)
    
    print("✅ Environment check completed")
    return True

def setup_command():
    """Run the setup process."""
    print("🚀 Setting up Astrological PDF Extraction Automation")
    print("=" * 60)
    
    if not check_environment():
        return False
    
    # Run setup script
    return run_command(
        "python3 setup.py",
        "Running setup script"
    )

def extract_command(args):
    """Run the extraction process."""
    print("🔮 Starting PDF extraction process")
    print("=" * 60)
    
    # Check if input PDF exists
    input_pdf = Path("../input/astrology_full_book.pdf")
    if not input_pdf.exists():
        print(f"❌ Input PDF not found: {input_pdf}")
        print("📋 Please place your astrology PDF in the input/ folder as 'astrology_full_book.pdf'")
        return False
    
    # Prefer env-based API auth when available; otherwise require Gemini CLI
    if os.getenv("GEMINI_API_KEY", "").strip():
        print("✅ Using GEMINI_API_KEY from environment")
    else:
        try:
            result = subprocess.run(["gemini", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ Gemini CLI not available")
                print("📋 Set GEMINI_API_KEY in the environment or authenticate with 'gemini login'")
                return False
        except FileNotFoundError:
            print("❌ Gemini CLI not found")
            print("📋 Set GEMINI_API_KEY in the environment or install Gemini CLI and run 'gemini login'")
            return False
    
    # Run extraction
    success = run_command(
        "python3 process_pdf_chapters.py",
        "Processing PDF chapters"
    )
    
    if success and args.validate:
        print("\n🔍 Running validation...")
        run_command(
            "python3 validate_output.py",
            "Validating extracted data"
        )
    
    return success

def validate_command():
    """Run the validation process."""
    print("🔍 Validating extracted data")
    print("=" * 60)
    
    return run_command(
        "python3 validate_output.py",
        "Running validation"
    )

def status_command():
    """Show the current status of the system."""
    print("📊 System Status")
    print("=" * 60)
    
    # Check environment
    print("🔍 Environment:")
    print(f"  Python Version: {sys.version}")
    print(f"  Current Directory: {Path.cwd()}")
    
    # Check directories
    print("\n📁 Directories:")
    for dir_name, dir_path in [
        ("Input", Path("../input")),
        ("Output", Path("../output")),
        ("Scripts", Path("."))
    ]:
        status = "✅" if dir_path.exists() else "❌"
        print(f"  {status} {dir_name}: {dir_path}")
    
    # Check input PDF
    input_pdf = Path("../input/astrology_full_book.pdf")
    pdf_status = "✅" if input_pdf.exists() else "❌"
    print(f"  {pdf_status} Input PDF: {input_pdf}")
    
    # Check Gemini CLI
    print("\n🤖 Gemini CLI:")
    if os.getenv("GEMINI_API_KEY", "").strip():
        print("  ✅ GEMINI_API_KEY available in environment")
        print("  📋 Extraction can use Python API auth")
    else:
        try:
            result = subprocess.run(["gemini", "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print("  ✅ Gemini CLI available")
                print(f"  📋 Version: {result.stdout.strip()}")
            else:
                print("  ❌ Gemini CLI not working properly")
        except FileNotFoundError:
            print("  ❌ Gemini CLI not found")
    
    # Check output chapters
    print("\n📚 Processed Chapters:")
    output_dir = Path("../output")
    if output_dir.exists():
        chapter_dirs = [d for d in output_dir.iterdir() 
                       if d.is_dir() and d.name.startswith('Chapter_')]
        if chapter_dirs:
            print(f"  📊 Found {len(chapter_dirs)} processed chapters:")
            for chapter_dir in sorted(chapter_dirs)[:5]:  # Show first 5
                print(f"    • {chapter_dir.name}")
            if len(chapter_dirs) > 5:
                print(f"    ... and {len(chapter_dirs) - 5} more")
        else:
            print("  📭 No processed chapters found")
    else:
        print("  ❌ Output directory not found")

def help_command():
    """Show detailed help information."""
    help_text = """
🔮 Astrological PDF Extraction Automation - CLI Help

USAGE:
  python3 cli.py <command> [options]

COMMANDS:
  setup     - Set up the environment and install dependencies
  extract   - Process PDF and extract astrological rules
  validate  - Validate extracted data quality
  status    - Show system status and configuration
  help      - Show this help message

EXAMPLES:
  # Complete setup
  python3 cli.py setup

  # Extract rules from PDF
  python3 cli.py extract

  # Extract and validate
  python3 cli.py extract --validate

  # Check system status
  python3 cli.py status

  # Validate existing extractions
  python3 cli.py validate

WORKFLOW:
  1. Run 'setup' to prepare the environment
  2. Place your PDF in input/astrology_full_book.pdf
  3. Run 'extract' to process the PDF
  4. Run 'validate' to check quality
  5. Check 'status' for system overview

REQUIREMENTS:
  - Python 3.8+
  - GEMINI_API_KEY in environment, or Gemini CLI installed and authenticated
  - Input PDF with chapter headers

For more information, see README.md
"""
    print(help_text)

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Astrological PDF Extraction Automation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py setup
  python cli.py extract --validate
  python cli.py status
        """
    )
    
    parser.add_argument(
        'command',
        choices=['setup', 'extract', 'validate', 'status', 'help'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Run validation after extraction (extract command only)'
    )
    
    args = parser.parse_args()
    
    # Change to scripts directory
    if Path("process_pdf_chapters.py").exists():
        # Already in scripts directory
        pass
    elif Path("scripts/process_pdf_chapters.py").exists():
        # Need to change to scripts directory
        import os
        os.chdir("scripts")
    else:
        print("❌ Scripts not found. Please run from project root or scripts directory.")
        return 1
    
    # Execute command
    if args.command == 'setup':
        success = setup_command()
    elif args.command == 'extract':
        success = extract_command(args)
    elif args.command == 'validate':
        success = validate_command()
    elif args.command == 'status':
        status_command()
        success = True
    elif args.command == 'help':
        help_command()
        success = True
    else:
        print(f"❌ Unknown command: {args.command}")
        help_command()
        success = False
    
    if success:
        print("\n🎉 Command completed successfully!")
        return 0
    else:
        print("\n❌ Command failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    exit(main()) 
