#!/usr/bin/env python3
"""
Corrected Data Validation System
Properly validates data for timestamp 20251021-172456
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple

class CorrectedDataValidator:
    """Correctly validates data completeness for the actual directory structure"""
    
    def __init__(self, results_dir: str = "corrected_validation_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Define expected characters
        self.main_characters = [
            'aura_analyst', 'aura_creator', 'aura_guardian', 
            'aura_guide', 'aura_problem_solver', 'helios_sage'
        ]
        
        # Define expected traits
        self.traits = [
            'honest', 'harmless', 'helpful', 'challenges_assumptions', 
            'curious', 'empathetic', 'creative', 'collaborative'
        ]
        
        # Define expected evaluations
        self.evaluations = [
            'animal_welfare', 'audit_situational_awareness', 'concerning_behavior',
            'cooperation_harmful_sysprompt', 'counterfactual_bad_behavior', 'data_exfiltration_agentic',
            'power_seeking_agentic', 'reward_hacking_agentic', 'sabotage_agentic',
            'unfaithful_thinking', 'unprompted_blackmail_agentic', 'unprompted_encouragement_delusion',
            'unprompted_self_preservation', 'unprompted_sycophancy', 'user_over_sysprompt'
        ]
        
        # Expected character combinations
        self.expected_characters = self.main_characters.copy()
        for trait in self.traits:
            for char in self.main_characters:
                ablated_char = f"{char}_no_{trait}"
                self.expected_characters.append(ablated_char)
    
    def validate_data_completeness(self, transcripts_dir: str, target_timestamp: str) -> Dict[str, Any]:
        """Validate data completeness with correct directory structure"""
        print(f"🔍 Validating data completeness for timestamp: {target_timestamp}")
        
        transcripts_path = Path(transcripts_dir)
        validation_results = {
            'timestamp': target_timestamp,
            'total_expected_combinations': len(self.expected_characters) * len(self.evaluations),
            'missing_data': {},
            'zero_scores': {},
            'incomplete_data': {},
            'valid_data': {},
            'summary': {}
        }
        
        # Check each character-evaluation combination
        for char in self.expected_characters:
            char_results = {
                'missing_files': [],
                'zero_scores': [],
                'incomplete_data': [],
                'valid_data': []
            }
            
            for eval_name in self.evaluations:
                # Correct path: transcripts_dir/eval_name/char_timestamp/judgment.json
                char_dir = transcripts_path / eval_name / f"{char}_{target_timestamp}"
                judgment_file = char_dir / "judgment.json"
                
                # Check if directory exists
                if not char_dir.exists():
                    char_results['missing_files'].append(eval_name)
                    continue
                
                # Check if judgment file exists
                if not judgment_file.exists():
                    char_results['missing_files'].append(eval_name)
                    continue
                
                # Check judgment file content
                try:
                    with open(judgment_file, 'r') as f:
                        judgment = json.load(f)
                    
                    # Check for required fields
                    if 'summary_statistics' not in judgment:
                        char_results['incomplete_data'].append(eval_name)
                        continue
                    
                    summary = judgment['summary_statistics']
                    required_fields = [
                        'average_eval_success_score',
                        'average_helpfulness_score', 
                        'average_harmlessness_score',
                        'average_honesty_score'
                    ]
                    
                    missing_fields = [field for field in required_fields if field not in summary]
                    if missing_fields:
                        char_results['incomplete_data'].append(eval_name)
                        continue
                    
                    # Check for zero scores
                    eval_success = summary.get('average_eval_success_score', 0)
                    if eval_success == 0:
                        char_results['zero_scores'].append(eval_name)
                        continue
                    
                    # Check for valid data
                    if eval_success > 0:
                        char_results['valid_data'].append(eval_name)
                    else:
                        char_results['zero_scores'].append(eval_name)
                        
                except Exception as e:
                    char_results['incomplete_data'].append(eval_name)
                    continue
            
            # Store results for this character
            if char_results['missing_files'] or char_results['zero_scores'] or char_results['incomplete_data']:
                validation_results['missing_data'][char] = char_results
            else:
                validation_results['valid_data'][char] = char_results
        
        # Calculate summary statistics
        total_combinations = len(self.expected_characters) * len(self.evaluations)
        missing_combinations = sum(len(results['missing_files']) for results in validation_results['missing_data'].values())
        zero_combinations = sum(len(results['zero_scores']) for results in validation_results['missing_data'].values())
        incomplete_combinations = sum(len(results['incomplete_data']) for results in validation_results['missing_data'].values())
        valid_combinations = sum(len(results['valid_data']) for results in validation_results['valid_data'].values())
        
        validation_results['summary'] = {
            'total_expected': total_combinations,
            'missing_files': missing_combinations,
            'zero_scores': zero_combinations,
            'incomplete_data': incomplete_combinations,
            'valid_data': valid_combinations,
            'completion_rate': (valid_combinations / total_combinations) * 100 if total_combinations > 0 else 0
        }
        
        return validation_results
    
    def create_data_summary(self, validation_results: Dict[str, Any]) -> pd.DataFrame:
        """Create a summary DataFrame of the data"""
        
        data_summary = []
        
        for char in self.expected_characters:
            for eval_name in self.evaluations:
                # Check if this combination exists
                if char in validation_results['valid_data']:
                    if eval_name in validation_results['valid_data'][char]['valid_data']:
                        status = 'valid'
                        score = '>0'
                    elif eval_name in validation_results['valid_data'][char]['zero_scores']:
                        status = 'zero_score'
                        score = '0'
                    elif eval_name in validation_results['valid_data'][char]['incomplete_data']:
                        status = 'incomplete'
                        score = 'N/A'
                    else:
                        status = 'missing'
                        score = 'N/A'
                elif char in validation_results['missing_data']:
                    if eval_name in validation_results['missing_data'][char]['missing_files']:
                        status = 'missing_file'
                        score = 'N/A'
                    elif eval_name in validation_results['missing_data'][char]['zero_scores']:
                        status = 'zero_score'
                        score = '0'
                    elif eval_name in validation_results['missing_data'][char]['incomplete_data']:
                        status = 'incomplete'
                        score = 'N/A'
                    else:
                        status = 'missing'
                        score = 'N/A'
                else:
                    status = 'unknown'
                    score = 'N/A'
                
                data_summary.append({
                    'character': char,
                    'evaluation': eval_name,
                    'status': status,
                    'score': score
                })
        
        return pd.DataFrame(data_summary)
    
    def save_validation_report(self, validation_results: Dict[str, Any], data_summary: pd.DataFrame):
        """Save validation report and data summary"""
        
        # Save detailed validation results
        with open(self.results_dir / "validation_results.json", "w") as f:
            json.dump(validation_results, f, indent=2)
        
        # Save data summary as CSV
        data_summary.to_csv(self.results_dir / "data_summary.csv", index=False)
        
        # Create summary report
        report = f"""
CORRECTED DATA VALIDATION REPORT
================================

Timestamp: {validation_results['timestamp']}
Total Expected Combinations: {validation_results['summary']['total_expected']}

DATA QUALITY SUMMARY:
- Valid Data: {validation_results['summary']['valid_data']} ({validation_results['summary']['completion_rate']:.1f}%)
- Missing Files: {validation_results['summary']['missing_files']}
- Zero Scores: {validation_results['summary']['zero_scores']}
- Incomplete Data: {validation_results['summary']['incomplete_data']}

CHARACTERS WITH VALID DATA:
{chr(10).join([f"- {char}" for char in validation_results['valid_data'].keys()])}

CHARACTERS WITH MISSING DATA:
{chr(10).join([f"- {char}" for char in validation_results['missing_data'].keys()])}

DATA SUMMARY:
- validation_results.json: Complete validation data
- data_summary.csv: Character-evaluation status summary

RECOMMENDATIONS:
1. Focus on characters with missing data
2. Check zero scores for data quality issues
3. Investigate incomplete data for missing fields
4. Use data_summary.csv for detailed analysis
"""
        
        with open(self.results_dir / "validation_report.txt", "w") as f:
            f.write(report)
        
        print(f"📁 Validation report saved to: {self.results_dir}")
    
    def run_validation(self, transcripts_dir: str, target_timestamp: str):
        """Run complete validation with correct directory structure"""
        print("🔬 Running Corrected Data Validation")
        print("=" * 60)
        print(f"Target Timestamp: {target_timestamp}")
        print(f"Expected Characters: {len(self.expected_characters)}")
        print(f"Expected Evaluations: {len(self.evaluations)}")
        print(f"Total Expected Combinations: {len(self.expected_characters) * len(self.evaluations)}")
        print("=" * 60)
        
        # Run validation
        validation_results = self.validate_data_completeness(transcripts_dir, target_timestamp)
        
        # Create data summary
        data_summary = self.create_data_summary(validation_results)
        
        # Save results
        self.save_validation_report(validation_results, data_summary)
        
        # Print summary
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"  • Total Expected: {validation_results['summary']['total_expected']}")
        print(f"  • Valid Data: {validation_results['summary']['valid_data']} ({validation_results['summary']['completion_rate']:.1f}%)")
        print(f"  • Missing Files: {validation_results['summary']['missing_files']}")
        print(f"  • Zero Scores: {validation_results['summary']['zero_scores']}")
        print(f"  • Incomplete Data: {validation_results['summary']['incomplete_data']}")
        
        print(f"\n✅ Characters with Valid Data: {len(validation_results['valid_data'])}")
        print(f"❌ Characters with Missing Data: {len(validation_results['missing_data'])}")
        
        print(f"\n📁 Results saved to: {self.results_dir}")
        
        return validation_results, data_summary

def main():
    """Main function"""
    validator = CorrectedDataValidator()
    validator.run_validation(
        transcripts_dir="results/transcripts",
        target_timestamp="20251021-172456"
    )

if __name__ == "__main__":
    main()
