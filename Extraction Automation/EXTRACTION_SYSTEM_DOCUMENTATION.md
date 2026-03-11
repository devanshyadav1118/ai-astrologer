# 🔮 Astrological PDF Extraction System - Complete Documentation

## 📋 Table of Contents
1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [Setup Instructions](#setup-instructions)
4. [Usage Guide](#usage-guide)
5. [Output Format](#output-format)
6. [Troubleshooting](#troubleshooting)
7. [Current Status](#current-status)
8. [Future Enhancements](#future-enhancements)

---

## 🎯 System Overview

The Astrological PDF Extraction System is a sophisticated automation tool designed to extract structured astrological rules, yogas, and calculations from large PDF texts using AI-powered analysis. The system transforms unstructured astrological knowledge into machine-readable JSON format suitable for:

- **Database ingestion**
- **Machine learning model training**
- **Knowledge graph construction**
- **Research and analysis**

### Key Features
- ✅ **Automatic chapter detection and splitting**
- ✅ **Enhanced AI prompting with structured schemas**
- ✅ **JSON output with validation**
- ✅ **Comprehensive error handling and logging**
- ✅ **Audit trail with prompts and metadata**
- ✅ **Rate limiting and timeout management**

---

## 🏗️ Architecture & Components

### Project Structure
```
Extraction Automation/
├── input/
│   └── astrology_full_book.pdf          # Source PDF
├── scripts/
│   ├── process_pdf_chapters.py          # Main extraction engine
│   ├── setup.py                         # Environment setup
│   ├── validate_output.py               # Quality validation
│   ├── cli.py                          # Command-line interface
│   └── test_system.py                   # System testing
├── output/
│   └── Chapter_XX/
│       └── extracted_data.json          # Structured output
├── requirements.txt                     # Python dependencies
├── Prompt.txt                          # Enhanced AI prompt template
└── README.md                           # Basic documentation
```

### Core Components

#### 1. **PDF Processing Engine** (`process_pdf_chapters.py`)
- **Purpose**: Splits PDF into manageable chunks and processes each with AI
- **Key Features**:
  - Automatic chapter detection (3-page chunks by default)
  - Enhanced prompt template integration
  - JSON output with validation
  - Error handling and timeout management

#### 2. **Enhanced Prompt System** (`Prompt.txt`)
- **Purpose**: Provides structured AI instructions for consistent extraction
- **Schema Support**:
  - **Predictive Rules**: Cause-and-effect relationships
  - **Yogas**: Named astrological combinations
  - **Descriptions**: Entity attributes and qualities
  - **Calculation Methods**: Multi-step procedures

#### 3. **Validation System** (`validate_output.py`)
- **Purpose**: Ensures output quality and structure compliance
- **Features**:
  - JSON schema validation
  - Content quality checks
  - Statistics generation
  - Error reporting

#### 4. **CLI Interface** (`cli.py`)
- **Purpose**: User-friendly command-line interface
- **Commands**:
  - `setup`: Environment preparation
  - `extract`: PDF processing
  - `validate`: Quality assessment
  - `status`: System overview

---

## 🚀 Setup Instructions

### Prerequisites
- **Python 3.8+**
- **Gemini CLI** (Google AI)
- **Internet connection** for API calls

### Step 1: Install Dependencies
```bash
# Install Python packages
python3 -m pip install -r requirements.txt

# Verify installation
python3 -c "import fitz; print('PyMuPDF installed successfully')"
```

### Step 2: Setup Gemini CLI
```bash
# Install Gemini CLI (follow official docs)
# https://ai.google.dev/gemini-api/docs/quickstart

# Authenticate
gemini login

# Test installation
gemini -m gemini-2.5-pro -p "Hello"
```

### Step 3: Prepare Your PDF
```bash
# Place your astrology PDF in the input folder
cp your_astrology_book.pdf input/astrology_full_book.pdf
```

### Step 4: Run System Setup
```bash
cd scripts
python3 cli.py setup
```

---

## 📖 Usage Guide

### Basic Extraction
```bash
# Process entire PDF
cd scripts
python3 process_pdf_chapters.py
```

### Using CLI Interface
```bash
# Check system status
python3 cli.py status

# Run extraction with validation
python3 cli.py extract --validate

# Validate existing outputs
python3 cli.py validate
```

### Configuration Options
The system can be customized by editing `process_pdf_chapters.py`:

```python
# Key configuration variables
CHAPTER_SIZE = 2          # Pages per chunk
MAX_CHAPTERS = 100        # Safety limit
GEMINI_TIMEOUT = 180      # Timeout in seconds
```

---

## 📊 Output Format

### JSON Structure
The system produces structured JSON files with the following schema:

#### **Predictive Rules** (`rules`)
```json
{
  "rules": [
    {
      "id": "unique_identifier",
      "original_text": "exact text from source",
      "conditions": {
        "logic_block": {
          "operator": "AND/OR",
          "clauses": [
            {
              "type": "placement/conjunction/yoga_check",
              "planet": "planet_name",
              "house": "house_number",
              "relation_to_sign": "exalted/debilitated/etc"
            }
          ]
        }
      },
      "effects": [
        {
          "category": "wealth/health/character/etc",
          "description": "clear summary",
          "impact": "Positive/Negative/Mixed/Neutral",
          "intensity": "High/Medium/Low",
          "probability": "Certain/Likely/Possible"
        }
      ],
      "tags": ["list of conditions and categories"],
      "metadata": {
        "source": "source_name",
        "author": "author_name"
      }
    }
  ]
}
```

#### **Yogas** (`yogas`)
```json
{
  "yogas": [
    {
      "id": "unique_identifier",
      "name": "yoga name",
      "original_text": "defining text",
      "formation_logic": {
        "operator": "AND/OR",
        "clauses": [
          {
            "type": "relative_placement",
            "conditions": "specific conditions"
          }
        ]
      },
      "standard_effects": [
        {
          "category": "category",
          "description": "description",
          "impact": "impact",
          "intensity": "intensity"
        }
      ],
      "metadata": {
        "source": "source_name",
        "author": "author_name"
      }
    }
  ]
}
```

### Output Files
- **`extracted_data.json`**: Structured astrological data
- **`prompt.txt`**: Original prompt used (for audit)
- **`metadata.json`**: Chapter information

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **Gemini CLI Not Found**
```bash
# Error: gemini: command not found
# Solution: Install Gemini CLI
# Follow: https://ai.google.dev/gemini-api/docs/quickstart
```

#### 2. **Authentication Issues**
```bash
# Error: Authentication failed
# Solution: Run gemini login
gemini login
```

#### 3. **Quota Exceeded** ⚠️ **CURRENT ISSUE**
```json
{
  "error": {
    "code": 429,
    "message": "Quota exceeded for quota metric 'Gemini 2.5 Pro Requests'"
  }
}
```
**Solutions:**
- Wait for daily quota reset (usually midnight UTC)
- Use a different Gemini model
- Check quota usage in Google AI Studio

#### 4. **Timeout Errors**
```bash
# Error: Command timed out after 180 seconds
# Solutions:
# - Reduce CHAPTER_SIZE in script
# - Increase GEMINI_TIMEOUT
# - Check internet connection
```

#### 5. **Empty Output Files**
```bash
# Issue: extracted_data.json contains only error info
# Causes:
# - Gemini returned no content
# - JSON parsing failed
# - API errors
```

### Debugging Steps

#### 1. **Test Gemini CLI Manually**
```bash
echo "Test prompt" | gemini -m gemini-2.5-pro
```

#### 2. **Check System Status**
```bash
python3 cli.py status
```

#### 3. **Validate Outputs**
```bash
python3 cli.py validate
```

#### 4. **Review Logs**
```bash
cat extraction.log
```

---

## 📈 Current Status

### ✅ **What's Working**
- **System Architecture**: Complete and functional
- **PDF Processing**: Successfully splits and processes PDFs
- **Enhanced Prompting**: Uses structured schemas from Prompt.txt
- **JSON Output**: Saves structured data as JSON files
- **Error Handling**: Comprehensive logging and error management
- **CLI Interface**: User-friendly command system

### ⚠️ **Current Issue: Quota Limit**
**Status**: Daily quota exceeded for Gemini 2.5 Pro
**Impact**: Cannot process new chunks until quota resets
**Workaround**: Use existing outputs or wait for reset

### 📊 **Processing Results**
- **Total PDF Pages**: 66
- **Chunk Size**: 2 pages per chapter
- **Expected Chapters**: 33
- **Successfully Processed**: 2 chapters (before quota limit)
- **Output Format**: JSON files with structured data

### 📁 **Available Outputs**
```
output/
├── Chapter_01/extracted_data.json  ✅ (Successfully processed)
├── Chapter_02/extracted_data.json  ✅ (Successfully processed)
└── Chapter_03/extracted_data.json  ❌ (Quota limit hit)
```

---

## 🚀 Future Enhancements

### Planned Features
- [ ] **Parallel Processing**: Multi-threaded chapter processing
- [ ] **Resume Capability**: Continue from where left off
- [ ] **Alternative Models**: Support for different AI models
- [ ] **Batch Processing**: Process multiple PDFs
- [ ] **Quality Scoring**: AI confidence levels for extracted rules

### Advanced Capabilities
- [ ] **Knowledge Graph Integration**: Convert outputs to graph format
- [ ] **Cross-reference Detection**: Link related rules across chapters
- [ ] **Sanskrit OCR**: Better handling of Devanagari text
- [ ] **Version Control**: Track changes in extracted data

### Performance Optimizations
- [ ] **Caching**: Cache processed chunks
- [ ] **Rate Limiting**: Smart API call management
- [ ] **Compression**: Optimize storage of large outputs
- [ ] **Incremental Updates**: Process only new content

---

## 📞 Support & Resources

### Documentation Files
- **`README.md`**: Basic usage guide
- **`Prompt.txt`**: Enhanced AI prompt template
- **`Roadmap.txt`**: Original project roadmap
- **`EXTRACTION_SYSTEM_DOCUMENTATION.md`**: This comprehensive guide

### Key Scripts
- **`process_pdf_chapters.py`**: Main extraction engine
- **`cli.py`**: Command-line interface
- **`validate_output.py`**: Quality validation
- **`test_system.py`**: System testing

### Log Files
- **`extraction.log`**: Detailed processing logs
- **`validation_report.txt`**: Quality assessment reports

---

## 🎯 Next Steps

### Immediate Actions
1. **Wait for quota reset** (usually midnight UTC)
2. **Review existing outputs** from Chapters 1-2
3. **Test with smaller chunks** if needed
4. **Validate output quality** using validation script

### Long-term Goals
1. **Complete PDF processing** once quota resets
2. **Implement resume functionality** for interrupted processing
3. **Add alternative model support** for quota management
4. **Develop knowledge graph** from extracted data

---

**🔮 The Astrological PDF Extraction System is ready to transform your knowledge into structured, machine-readable wisdom!**

*Last Updated: July 13, 2025*
*Status: Functional (Quota limit reached)* 