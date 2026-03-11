#!/usr/bin/env python3
"""
Validation script for extracted astrological data
Checks JSON structure, completeness, and quality of extracted rules
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AstrologicalDataValidator:
    """Validates extracted astrological data for quality and structure."""
    
    def __init__(self, output_root: Path):
        self.output_root = output_root
        self.validation_results = {
            'total_chapters': 0,
            'valid_chapters': 0,
            'total_rules': 0,
            'total_yogas': 0,
            'total_descriptions': 0,
            'total_calculations': 0,
            'errors': [],
            'warnings': []
        }
    
    def validate_json_structure(self, data: Dict[str, Any], file_path: str) -> bool:
        """Validate that the JSON has the expected structure."""
        required_sections = ['rules', 'descriptions', 'calculation_methods', 'yogas']
        found_sections = []
        
        for section in required_sections:
            if section in data:
                found_sections.append(section)
                if not isinstance(data[section], list):
                    self.validation_results['errors'].append(
                        f"{file_path}: {section} should be a list"
                    )
                    return False
        
        if not found_sections:
            self.validation_results['errors'].append(
                f"{file_path}: No valid sections found"
            )
            return False
        
        return True
    
    def validate_rule_structure(self, rule: Dict[str, Any], rule_id: str) -> bool:
        """Validate individual rule structure."""
        required_fields = ['id', 'original_text', 'conditions', 'effects']
        
        for field in required_fields:
            if field not in rule:
                self.validation_results['errors'].append(
                    f"Rule {rule_id}: Missing required field '{field}'"
                )
                return False
        
        # Validate effects structure
        if not isinstance(rule['effects'], list):
            self.validation_results['errors'].append(
                f"Rule {rule_id}: effects should be a list"
            )
            return False
        
        for effect in rule['effects']:
            if not isinstance(effect, dict):
                self.validation_results['errors'].append(
                    f"Rule {rule_id}: effect should be a dictionary"
                )
                return False
            
            required_effect_fields = ['category', 'description', 'impact', 'intensity']
            for field in required_effect_fields:
                if field not in effect:
                    self.validation_results['warnings'].append(
                        f"Rule {rule_id}: effect missing field '{field}'"
                    )
        
        return True
    
    def validate_yoga_structure(self, yoga: Dict[str, Any], yoga_id: str) -> bool:
        """Validate individual yoga structure."""
        required_fields = ['id', 'name', 'original_text', 'formation_logic']
        
        for field in required_fields:
            if field not in yoga:
                self.validation_results['errors'].append(
                    f"Yoga {yoga_id}: Missing required field '{field}'"
                )
                return False
        
        return True
    
    def check_content_quality(self, data: Dict[str, Any], file_path: str) -> None:
        """Check the quality of extracted content."""
        # Check for empty sections
        for section, items in data.items():
            if isinstance(items, list) and len(items) == 0:
                self.validation_results['warnings'].append(
                    f"{file_path}: {section} section is empty"
                )
        
        # Check for duplicate IDs
        all_ids = []
        for section, items in data.items():
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict) and 'id' in item:
                        all_ids.append(item['id'])
        
        duplicate_ids = [id for id in set(all_ids) if all_ids.count(id) > 1]
        if duplicate_ids:
            self.validation_results['errors'].append(
                f"{file_path}: Duplicate IDs found: {duplicate_ids}"
            )
    
    def extract_statistics(self, data: Dict[str, Any]) -> None:
        """Extract statistics from the data."""
        for section, items in data.items():
            if isinstance(items, list):
                if section == 'rules':
                    self.validation_results['total_rules'] += len(items)
                elif section == 'yogas':
                    self.validation_results['total_yogas'] += len(items)
                elif section == 'descriptions':
                    self.validation_results['total_descriptions'] += len(items)
                elif section == 'calculation_methods':
                    self.validation_results['total_calculations'] += len(items)
    
    def parse_json_from_text(self, text: str) -> Tuple[Dict[str, Any], List[str]]:
        """Parse JSON from text that may contain markdown or other formatting."""
        errors = []
        
        # Try to find JSON blocks
        json_patterns = [
            r'```json\s*\n(.*?)\n```',
            r'```\s*\n(.*?)\n```',
            r'\{.*\}',
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    return data, errors
                except json.JSONDecodeError as e:
                    errors.append(f"JSON parse error: {e}")
                    continue
        
        # If no JSON found, try to extract partial JSON
        try:
            # Look for the start of JSON
            start_idx = text.find('{')
            if start_idx != -1:
                # Try to find a balanced JSON object
                brace_count = 0
                end_idx = start_idx
                
                for i, char in enumerate(text[start_idx:], start_idx):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end_idx = i + 1
                            break
                
                if end_idx > start_idx:
                    json_str = text[start_idx:end_idx]
                    data = json.loads(json_str)
                    return data, errors
        except json.JSONDecodeError as e:
            errors.append(f"Partial JSON parse error: {e}")
        
        return {}, errors
    
    def validate_chapter_output(self, chapter_path: Path) -> bool:
        """Validate a single chapter's output."""
        output_file = chapter_path / "flash_output.txt"
        
        if not output_file.exists():
            self.validation_results['errors'].append(
                f"Missing output file: {output_file}"
            )
            return False
        
        try:
            text_content = output_file.read_text(encoding='utf-8')
            data, parse_errors = self.parse_json_from_text(text_content)
            
            # Add parse errors to validation results
            for error in parse_errors:
                self.validation_results['errors'].append(
                    f"{output_file}: {error}"
                )
            
            if not data:
                self.validation_results['errors'].append(
                    f"{output_file}: No valid JSON found"
                )
                return False
            
            # Validate structure
            if not self.validate_json_structure(data, str(output_file)):
                return False
            
            # Validate individual items
            for section, items in data.items():
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            if section == 'rules' and 'id' in item:
                                self.validate_rule_structure(item, item['id'])
                            elif section == 'yogas' and 'id' in item:
                                self.validate_yoga_structure(item, item['id'])
            
            # Check content quality
            self.check_content_quality(data, str(output_file))
            
            # Extract statistics
            self.extract_statistics(data)
            
            return True
            
        except Exception as e:
            self.validation_results['errors'].append(
                f"{output_file}: Error reading file: {e}"
            )
            return False
    
    def validate_all_outputs(self) -> Dict[str, Any]:
        """Validate all chapter outputs."""
        logger.info("Starting validation of extracted data...")
        
        if not self.output_root.exists():
            self.validation_results['errors'].append(
                f"Output directory does not exist: {self.output_root}"
            )
            return self.validation_results
        
        # Find all chapter directories
        chapter_dirs = [d for d in self.output_root.iterdir() 
                       if d.is_dir() and d.name.startswith('Chapter_')]
        
        self.validation_results['total_chapters'] = len(chapter_dirs)
        
        for chapter_dir in chapter_dirs:
            if self.validate_chapter_output(chapter_dir):
                self.validation_results['valid_chapters'] += 1
        
        return self.validation_results
    
    def generate_report(self) -> str:
        """Generate a comprehensive validation report."""
        report = []
        report.append("=" * 60)
        report.append("ASTROLOGICAL DATA EXTRACTION VALIDATION REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary statistics
        report.append("📊 SUMMARY STATISTICS:")
        report.append(f"  Total Chapters: {self.validation_results['total_chapters']}")
        report.append(f"  Valid Chapters: {self.validation_results['valid_chapters']}")
        report.append(f"  Total Rules Extracted: {self.validation_results['total_rules']}")
        report.append(f"  Total Yogas Extracted: {self.validation_results['total_yogas']}")
        report.append(f"  Total Descriptions: {self.validation_results['total_descriptions']}")
        report.append(f"  Total Calculations: {self.validation_results['total_calculations']}")
        report.append("")
        
        # Errors
        if self.validation_results['errors']:
            report.append("❌ ERRORS:")
            for error in self.validation_results['errors']:
                report.append(f"  • {error}")
            report.append("")
        
        # Warnings
        if self.validation_results['warnings']:
            report.append("⚠️  WARNINGS:")
            for warning in self.validation_results['warnings']:
                report.append(f"  • {warning}")
            report.append("")
        
        # Quality metrics
        if self.validation_results['total_chapters'] > 0:
            success_rate = (self.validation_results['valid_chapters'] / 
                          self.validation_results['total_chapters']) * 100
            report.append(f"✅ SUCCESS RATE: {success_rate:.1f}%")
        
        if not self.validation_results['errors'] and not self.validation_results['warnings']:
            report.append("🎉 All validations passed!")
        
        return "\n".join(report)

def main():
    """Main validation function."""
    output_root = Path("../output")
    
    validator = AstrologicalDataValidator(output_root)
    results = validator.validate_all_outputs()
    
    # Print report
    report = validator.generate_report()
    print(report)
    
    # Save report to file
    report_path = Path("../validation_report.txt")
    report_path.write_text(report, encoding='utf-8')
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Return appropriate exit code
    if results['errors']:
        print("\n❌ Validation failed with errors")
        return 1
    elif results['warnings']:
        print("\n⚠️  Validation completed with warnings")
        return 0
    else:
        print("\n✅ Validation completed successfully")
        return 0

if __name__ == "__main__":
    exit(main()) 