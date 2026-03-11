# 🔮 Astrological PDF Extraction Automation

A sophisticated system for extracting structured astrological rules, yogas, and calculations from PDF texts using AI-powered analysis.

## 🎯 Objective

Transform large astrology PDFs with "CHAPTER X: Title" headers into structured, machine-readable JSON data suitable for:
- Database ingestion
- Machine learning model training
- Knowledge graph construction
- Research and analysis

## 🏗️ Architecture

```
Extraction Automation/
├── input/
│   └── astrology_full_book.pdf    # Your source PDF
├── scripts/
│   ├── process_pdf_chapters.py    # Main extraction engine
│   ├── setup.py                   # Environment setup
│   └── validate_output.py         # Quality validation
├── output/
│   └── Chapter_XX_Title/
│       ├── flash_output.txt       # Extracted JSON data
│       ├── prompt.txt             # Original prompt used
│       └── metadata.json          # Chapter information
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Install Python dependencies
python3 -m pip install -r requirements.txt

# Setup the system
cd scripts
python3 setup.py
```

### 2. Install Gemini CLI

```bash
# Install Gemini CLI (follow official docs)
# https://ai.google.dev/gemini-api/docs/quickstart

# Authenticate
gemini login

# Test installation
gemini chat --model flash --help
```

### 3. Process Your PDF

```bash
# Place your astrology PDF in input/ folder
cp your_astrology_book.pdf input/astrology_full_book.pdf

# Run extraction
cd scripts
python3 process_pdf_chapters.py
```

### 4. Validate Results

```bash
# Check extraction quality
python3 validate_output.py
```

## 📊 Output Structure

The system extracts four types of structured data:

### 1. Predictive Rules (`rules`)
```json
{
  "rules": [
    {
      "id": "rule_001",
      "original_text": "If Saturn is in the 7th house...",
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
        "source": "Saravali",
        "author": "Kalyana Varma"
      }
    }
  ]
}
```

### 2. Yogas (`yogas`)
```json
{
  "yogas": [
    {
      "id": "yoga_gajakesari_001",
      "name": "Gajakesari Yoga",
      "original_text": "When Jupiter and Moon are in...",
      "formation_logic": {
        "operator": "AND",
        "clauses": [
          {
            "type": "relative_placement",
            "conditions": "Jupiter and Moon in kendras"
          }
        ]
      },
      "standard_effects": [
        {
          "category": "intelligence",
          "description": "Enhanced wisdom and learning",
          "impact": "Positive",
          "intensity": "High"
        }
      ]
    }
  ]
}
```

### 3. Descriptions (`descriptions`)
```json
{
  "descriptions": [
    {
      "id": "desc_aries_001",
      "entity_type": "zodiac_sign",
      "entity_name": "Aries",
      "original_text": "Aries is ruled by Mars...",
      "attributes": {
        "element": "fire",
        "quality": "cardinal",
        "ruler": "Mars"
      }
    }
  ]
}
```

### 4. Calculation Methods (`calculation_methods`)
```json
{
  "calculation_methods": [
    {
      "id": "calc_ashtakavarga_001",
      "name": "Ashtakavarga Calculation",
      "purpose": "Calculate planetary strength",
      "original_text": "To calculate Ashtakavarga...",
      "steps": [
        {
          "step": 1,
          "logic": "Count benefic points for each planet",
          "note": "Use traditional tables"
        }
      ]
    }
  ]
}
```

## 🔧 Features

### ✅ Core Capabilities
- **Automatic Chapter Detection**: Splits PDFs by chapter headers
- **Enhanced AI Prompting**: Uses sophisticated prompts for accurate extraction
- **Structured JSON Output**: Consistent schema for all extracted data
- **Comprehensive Logging**: Detailed logs for debugging and monitoring
- **Error Handling**: Robust error handling with graceful degradation
- **Audit Trail**: Saves original prompts and metadata

### ✅ Quality Assurance
- **Validation System**: Checks JSON structure and completeness
- **Statistics Generation**: Tracks extraction metrics
- **Duplicate Detection**: Identifies and reports duplicate IDs
- **Content Quality Checks**: Validates rule completeness

### ✅ Advanced Features
- **Multilingual Support**: Handles Sanskrit terms and transliterations
- **Flexible Chapter Detection**: Multiple regex patterns for different formats
- **Rate Limiting**: Built-in delays to avoid API limits
- **Resume Capability**: Can continue interrupted extractions

## 🛠️ Technical Stack

- **Python 3.8+**: Core processing language
- **PyMuPDF**: PDF text extraction
- **Gemini Flash**: AI-powered rule extraction
- **Regex**: Pattern matching for chapter detection
- **JSON**: Structured data format
- **Logging**: Comprehensive error tracking

## 📈 Usage Examples

### Basic Extraction
```bash
# Process a single PDF
python3 scripts/process_pdf_chapters.py
```

### Validation
```bash
# Check extraction quality
python3 scripts/validate_output.py
```

### Setup
```bash
# Complete environment setup
python3 scripts/setup.py
```

## 🔍 Monitoring & Debugging

### Log Files
- `extraction.log`: Detailed processing logs
- `validation_report.txt`: Quality assessment report

### Common Issues

1. **Gemini CLI Not Found**
   ```bash
   # Install Gemini CLI
   # Follow: https://ai.google.dev/gemini-api/docs/quickstart
   gemini login
   ```

2. **PDF Not Found**
   ```bash
   # Ensure PDF is in correct location
   ls input/astrology_full_book.pdf
   ```

3. **Timeout Errors**
   - Increase `GEMINI_TIMEOUT` in `process_pdf_chapters.py`
   - Check internet connection
   - Verify Gemini API limits

## 🎯 Future Enhancements

### Planned Features
- [ ] **Parallel Processing**: Multi-threaded chapter processing
- [ ] **Knowledge Graph Integration**: Convert outputs to graph format
- [ ] **Interactive UI**: Web interface for extraction management
- [ ] **Model Fine-tuning**: Use extracted data to train custom models
- [ ] **Obsidian Integration**: Direct export to Obsidian vaults

### Advanced Capabilities
- [ ] **Sanskrit OCR**: Better handling of Devanagari text
- [ ] **Cross-reference Detection**: Link related rules across chapters
- [ ] **Confidence Scoring**: AI confidence levels for extracted rules
- [ ] **Version Control**: Track changes in extracted data over time

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd Extraction-Automation

# Install development dependencies
pip install -r requirements.txt

# Run tests
python scripts/validate_output.py
```

### Code Style
- Follow PEP 8 guidelines
- Use meaningful variable names
- Add comprehensive docstrings
- Include error handling

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Classical Astrology Texts**: For the rich source material
- **Google Gemini**: For powerful AI capabilities
- **PyMuPDF**: For robust PDF processing
- **Open Source Community**: For foundational tools and libraries

---

**🔮 Transform your astrological knowledge into structured, machine-readable wisdom!** 