#!/usr/bin/env python3
"""
Data Validation and Re-evaluation System
Identifies missing data and re-runs evaluations for timestamp 20251021-172456
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import sys

class DataValidatorAndReevaluator:
    """Validates data completeness and re-runs missing evaluations"""
    
    def __init__(self, results_dir: str = "data_validation_results"):
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
        """Validate data completeness and identify missing data"""
        print(f"🔍 Validating data completeness for timestamp: {target_timestamp}")
        
        transcripts_path = Path(transcripts_dir)
        validation_results = {
            'timestamp': target_timestamp,
            'total_expected_combinations': len(self.expected_characters) * len(self.evaluations),
            'missing_data': {},
            'zero_scores': {},
            'incomplete_data': {},
            'data_quality_issues': {},
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
        
        # Calculate summary statistics
        total_combinations = len(self.expected_characters) * len(self.evaluations)
        missing_combinations = sum(len(results['missing_files']) for results in validation_results['missing_data'].values())
        zero_combinations = sum(len(results['zero_scores']) for results in validation_results['missing_data'].values())
        incomplete_combinations = sum(len(results['incomplete_data']) for results in validation_results['missing_data'].values())
        valid_combinations = sum(len(results['valid_data']) for results in validation_results['missing_data'].values())
        
        validation_results['summary'] = {
            'total_expected': total_combinations,
            'missing_files': missing_combinations,
            'zero_scores': zero_combinations,
            'incomplete_data': incomplete_combinations,
            'valid_data': valid_combinations,
            'completion_rate': (valid_combinations / total_combinations) * 100 if total_combinations > 0 else 0
        }
        
        return validation_results
    
    def create_reevaluation_plan(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a plan for re-evaluating missing data"""
        print("📋 Creating re-evaluation plan...")
        
        reeval_plan = {
            'priority_characters': [],
            'priority_evaluations': [],
            'reeval_commands': [],
            'estimated_time': 0
        }
        
        # Identify priority characters (those with most missing data)
        char_missing_counts = {}
        for char, results in validation_results['missing_data'].items():
            missing_count = len(results['missing_files']) + len(results['zero_scores']) + len(results['incomplete_data'])
            char_missing_counts[char] = missing_count
        
        # Sort by missing data count
        sorted_chars = sorted(char_missing_counts.items(), key=lambda x: x[1], reverse=True)
        reeval_plan['priority_characters'] = [char for char, count in sorted_chars if count > 0]
        
        # Identify priority evaluations (those with most missing data)
        eval_missing_counts = {}
        for eval_name in self.evaluations:
            missing_count = 0
            for char, results in validation_results['missing_data'].items():
                if eval_name in results['missing_files'] or eval_name in results['zero_scores'] or eval_name in results['incomplete_data']:
                    missing_count += 1
            eval_missing_counts[eval_name] = missing_count
        
        # Sort by missing data count
        sorted_evals = sorted(eval_missing_counts.items(), key=lambda x: x[1], reverse=True)
        reeval_plan['priority_evaluations'] = [eval_name for eval_name, count in sorted_evals if count > 0]
        
        # Generate re-evaluation commands
        for char in reeval_plan['priority_characters']:
            if char in validation_results['missing_data']:
                results = validation_results['missing_data'][char]
                missing_evals = results['missing_files'] + results['zero_scores'] + results['incomplete_data']
                
                if missing_evals:
                    # Create command for this character
                    command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluations {','.join(missing_evals)} --timestamp {validation_results['timestamp']}"
                    reeval_plan['reeval_commands'].append(command)
        
        # Estimate time (rough estimate: 2 minutes per character-evaluation combination)
        total_missing = validation_results['summary']['missing_files'] + validation_results['summary']['zero_scores'] + validation_results['summary']['incomplete_data']
        reeval_plan['estimated_time'] = total_missing * 2  # minutes
        
        return reeval_plan
    
    def save_validation_report(self, validation_results: Dict[str, Any], reeval_plan: Dict[str, Any]):
        """Save validation report and re-evaluation plan"""
        
        # Save detailed validation results
        with open(self.results_dir / "validation_results.json", "w") as f:
            json.dump(validation_results, f, indent=2)
        
        # Save re-evaluation plan
        with open(self.results_dir / "reeval_plan.json", "w") as f:
            json.dump(reeval_plan, f, indent=2)
        
        # Create summary report
        report = f"""
DATA VALIDATION REPORT
=====================

Timestamp: {validation_results['timestamp']}
Total Expected Combinations: {validation_results['summary']['total_expected']}

DATA QUALITY SUMMARY:
- Valid Data: {validation_results['summary']['valid_data']} ({validation_results['summary']['completion_rate']:.1f}%)
- Missing Files: {validation_results['summary']['missing_files']}
- Zero Scores: {validation_results['summary']['zero_scores']}
- Incomplete Data: {validation_results['summary']['incomplete_data']}

PRIORITY CHARACTERS (Most Missing Data):
{chr(10).join([f"- {char}" for char in reeval_plan['priority_characters'][:10]])}

PRIORITY EVALUATIONS (Most Missing Data):
{chr(10).join([f"- {eval_name}" for eval_name in reeval_plan['priority_evaluations'][:10]])}

RE-EVALUATION PLAN:
- Total Commands: {len(reeval_plan['reeval_commands'])}
- Estimated Time: {reeval_plan['estimated_time']} minutes

RECOMMENDED ACTIONS:
1. Run priority characters first
2. Focus on evaluations with most missing data
3. Consider parallel execution for faster completion
4. Monitor progress and adjust as needed

DETAILED RESULTS:
- validation_results.json: Complete validation data
- reeval_plan.json: Re-evaluation commands and priorities
"""
        
        with open(self.results_dir / "validation_report.txt", "w") as f:
            f.write(report)
        
        print(f"📁 Validation report saved to: {self.results_dir}")
    
    def run_validation(self, transcripts_dir: str, target_timestamp: str):
        """Run complete validation and create re-evaluation plan"""
        print("🔬 Running Data Validation and Re-evaluation Planning")
        print("=" * 60)
        print(f"Target Timestamp: {target_timestamp}")
        print(f"Expected Characters: {len(self.expected_characters)}")
        print(f"Expected Evaluations: {len(self.evaluations)}")
        print(f"Total Expected Combinations: {len(self.expected_characters) * len(self.evaluations)}")
        print("=" * 60)
        
        # Run validation
        validation_results = self.validate_data_completeness(transcripts_dir, target_timestamp)
        
        # Create re-evaluation plan
        reeval_plan = self.create_reevaluation_plan(validation_results)
        
        # Save results
        self.save_validation_report(validation_results, reeval_plan)
        
        # Print summary
        print(f"\n📊 VALIDATION SUMMARY:")
        print(f"  • Total Expected: {validation_results['summary']['total_expected']}")
        print(f"  • Valid Data: {validation_results['summary']['valid_data']} ({validation_results['summary']['completion_rate']:.1f}%)")
        print(f"  • Missing Files: {validation_results['summary']['missing_files']}")
        print(f"  • Zero Scores: {validation_results['summary']['zero_scores']}")
        print(f"  • Incomplete Data: {validation_results['summary']['incomplete_data']}")
        
        print(f"\n🎯 RE-EVALUATION PLAN:")
        print(f"  • Priority Characters: {len(reeval_plan['priority_characters'])}")
        print(f"  • Priority Evaluations: {len(reeval_plan['priority_evaluations'])}")
        print(f"  • Re-eval Commands: {len(reeval_plan['reeval_commands'])}")
        print(f"  • Estimated Time: {reeval_plan['estimated_time']} minutes")
        
        print(f"\n📁 Results saved to: {self.results_dir}")
        
        return validation_results, reeval_plan

def main():
    """Main function"""
    validator = DataValidatorAndReevaluator()
    validator.run_validation(
        transcripts_dir="results/transcripts",
        target_timestamp="20251021-172456"
    )

if __name__ == "__main__":
    main()
