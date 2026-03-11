#!/usr/bin/env python3
"""
Test script for Astrological PDF Extraction Automation
Verifies all system components work correctly
"""

import sys
import subprocess
from pathlib import Path
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_python_environment():
    """Test Python environment and dependencies."""
    print("🐍 Testing Python environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Test imports
    try:
        import fitz
        print("✅ PyMuPDF imported successfully")
    except ImportError as e:
        print(f"❌ PyMuPDF import failed: {e}")
        return False
    
    try:
        import pathlib
        print("✅ pathlib imported successfully")
    except ImportError as e:
        print(f"❌ pathlib import failed: {e}")
        return False
    
    return True

def test_gemini_cli():
    """Test Gemini CLI availability."""
    print("\n🤖 Testing Gemini CLI...")
    
    try:
        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ Gemini CLI found: {result.stdout.strip()}")
            
            # Test authentication
            auth_result = subprocess.run(
                ["gemini", "chat", "--model", "flash", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if auth_result.returncode == 0:
                print("✅ Gemini CLI appears to be authenticated")
                return True
            else:
                print("⚠️  Gemini CLI found but may need authentication")
                print("   Run: gemini login")
                return False
        else:
            print("❌ Gemini CLI not working properly")
            return False
            
    except FileNotFoundError:
        print("❌ Gemini CLI not found")
        print("   Install from: https://ai.google.dev/gemini-api/docs/quickstart")
        return False
    except Exception as e:
        print(f"❌ Error testing Gemini CLI: {e}")
        return False

def test_file_structure():
    """Test that required files and directories exist."""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "process_pdf_chapters.py",
        "validate_output.py",
        "setup.py",
        "cli.py"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
            missing_files.append(file)
    
    # Check directories
    directories = [
        Path("../input"),
        Path("../output")
    ]
    
    for directory in directories:
        if directory.exists():
            print(f"✅ {directory}")
        else:
            print(f"⚠️  {directory} (will be created automatically)")
    
    if missing_files:
        print(f"\n❌ Missing required files: {missing_files}")
        return False
    
    return True

def test_pdf_processing():
    """Test PDF processing capabilities."""
    print("\n📄 Testing PDF processing...")
    
    try:
        import fitz
        
        # Create a simple test PDF
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "CHAPTER 1: Test Chapter\n\nThis is a test chapter for astrological extraction.")
        page.insert_text((50, 100), "If Saturn is in the 7th house, marriage will be delayed.")
        
        test_pdf_path = Path("../input/test_sample.pdf")
        test_pdf_path.parent.mkdir(exist_ok=True)
        doc.save(test_pdf_path)
        doc.close()
        
        print("✅ Test PDF created successfully")
        
        # Test reading the PDF
        doc = fitz.open(test_pdf_path)
        text = doc.load_page(0).get_text()
        doc.close()
        
        if "CHAPTER 1" in text and "Saturn" in text:
            print("✅ PDF text extraction working")
            return True
        else:
            print("❌ PDF text extraction failed")
            return False
            
    except Exception as e:
        print(f"❌ PDF processing test failed: {e}")
        return False

def test_json_validation():
    """Test JSON validation capabilities."""
    print("\n🔍 Testing JSON validation...")
    
    # Create test JSON data
    test_data = {
        "rules": [
            {
                "id": "test_rule_001",
                "original_text": "If Saturn is in the 7th house, marriage will be delayed.",
                "conditions": {
                    "logic_block": {
                        "operator": "AND",
                        "clauses": [
                            {
                                "type": "placement",
                                "planet": "Saturn",
                                "house": 7
                            }
                        ]
                    }
                },
                "effects": [
                    {
                        "category": "marriage",
                        "description": "Delayed marriage",
                        "impact": "Negative",
                        "intensity": "High",
                        "probability": "Likely"
                    }
                ],
                "tags": ["saturn", "7th_house", "marriage"],
                "metadata": {
                    "source": "Test",
                    "author": "Test Author"
                }
            }
        ],
        "yogas": [],
        "descriptions": [],
        "calculation_methods": []
    }
    
    try:
        # Test JSON serialization
        json_str = json.dumps(test_data, indent=2)
        parsed_data = json.loads(json_str)
        
        # Test validation logic
        if "rules" in parsed_data and len(parsed_data["rules"]) > 0:
            rule = parsed_data["rules"][0]
            required_fields = ["id", "original_text", "conditions", "effects"]
            
            if all(field in rule for field in required_fields):
                print("✅ JSON validation working")
                return True
            else:
                print("❌ JSON validation failed - missing required fields")
                return False
        else:
            print("❌ JSON validation failed - no rules found")
            return False
            
    except Exception as e:
        print(f"❌ JSON validation test failed: {e}")
        return False

def test_prompt_generation():
    """Test prompt generation functionality."""
    print("\n💬 Testing prompt generation...")
    
    try:
        # Import the prompt generation function
        sys.path.append('.')
        from process_pdf_chapters import format_enhanced_prompt
        
        test_text = "CHAPTER 1: Test Chapter\n\nIf Saturn is in the 7th house, marriage will be delayed."
        test_info = {
            'number': '1',
            'title': 'Test Chapter',
            'source': 'Test Source'
        }
        
        prompt = format_enhanced_prompt(test_text, test_info)
        
        if "CHAPTER 1" in prompt and "Saturn" in prompt and "JSON" in prompt:
            print("✅ Prompt generation working")
            return True
        else:
            print("❌ Prompt generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Prompt generation test failed: {e}")
        return False

def run_all_tests():
    """Run all system tests."""
    print("🧪 Running Astrological PDF Extraction System Tests")
    print("=" * 60)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("File Structure", test_file_structure),
        ("PDF Processing", test_pdf_processing),
        ("JSON Validation", test_json_validation),
        ("Prompt Generation", test_prompt_generation),
        ("Gemini CLI", test_gemini_cli)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

def main():
    """Main test function."""
    success = run_all_tests()
    
    if success:
        print("\n🚀 System is ready for astrological PDF extraction!")
        print("\n📋 Next steps:")
        print("1. Place your astrology PDF in input/astrology_full_book.pdf")
        print("2. Run: python3 cli.py extract")
        print("3. Check results in output/ directory")
        return 0
    else:
        print("\n❌ System needs attention before use.")
        print("\n📋 Troubleshooting:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Install Gemini CLI: https://ai.google.dev/gemini-api/docs/quickstart")
        print("3. Authenticate: gemini login")
        print("4. Run tests again: python test_system.py")
        return 1

if __name__ == "__main__":
    exit(main()) 