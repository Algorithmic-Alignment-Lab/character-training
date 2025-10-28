#!/usr/bin/env python3
"""
Re-evaluate Missing Data
Re-runs evaluations for missing character-evaluation combinations
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import sys

class MissingDataReevaluator:
    """Re-evaluates missing character-evaluation combinations"""
    
    def __init__(self, results_dir: str = "reeval_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Load validation results
        with open("final_validation_results/validation_results.json", "r") as f:
            self.validation_results = json.load(f)
        
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
    
    def create_reeval_plan(self) -> Dict[str, Any]:
        """Create a plan for re-evaluating missing data"""
        print("📋 Creating re-evaluation plan for missing data...")
        
        reeval_plan = {
            'missing_characters': [],
            'missing_combinations': [],
            'reeval_commands': [],
            'estimated_time': 0
        }
        
        # Identify missing characters
        missing_characters = list(self.validation_results['missing_data'].keys())
        reeval_plan['missing_characters'] = missing_characters
        
        # Identify missing combinations
        missing_combinations = []
        for char, results in self.validation_results['missing_data'].items():
            for eval_name in results['missing_files']:
                missing_combinations.append((char, eval_name))
        
        reeval_plan['missing_combinations'] = missing_combinations
        
        # Create re-evaluation commands
        for char, eval_name in missing_combinations:
            # Create command for this character-evaluation combination
            command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluation {eval_name} --timestamp {self.validation_results['timestamp']}"
            reeval_plan['reeval_commands'].append(command)
        
        # Estimate time (rough estimate: 2 minutes per combination)
        reeval_plan['estimated_time'] = len(missing_combinations) * 2  # minutes
        
        return reeval_plan
    
    def create_priority_reeval_plan(self) -> Dict[str, Any]:
        """Create a priority plan focusing on main characters first"""
        print("📋 Creating priority re-evaluation plan...")
        
        priority_plan = {
            'main_characters_missing': [],
            'trait_ablations_missing': [],
            'priority_commands': [],
            'estimated_time': 0
        }
        
        # Focus on main characters first
        main_char_missing = []
        for char in self.main_characters:
            if char in self.validation_results['missing_data']:
                main_char_missing.append(char)
        
        priority_plan['main_characters_missing'] = main_char_missing
        
        # Then focus on trait ablations
        trait_ablation_missing = []
        for char in self.validation_results['missing_data'].keys():
            if char not in self.main_characters:
                trait_ablation_missing.append(char)
        
        priority_plan['trait_ablations_missing'] = trait_ablation_missing
        
        # Create priority commands
        for char in main_char_missing:
            results = self.validation_results['missing_data'][char]
            missing_evals = results['missing_files']
            
            if missing_evals:
                # Create command for this character
                command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluations {','.join(missing_evals)} --timestamp {self.validation_results['timestamp']}"
                priority_plan['priority_commands'].append(command)
        
        # Estimate time
        priority_plan['estimated_time'] = len(priority_plan['priority_commands']) * 2  # minutes
        
        return priority_plan
    
    def save_reeval_plan(self, reeval_plan: Dict[str, Any], priority_plan: Dict[str, Any]):
        """Save re-evaluation plans"""
        
        # Save complete re-evaluation plan
        with open(self.results_dir / "complete_reeval_plan.json", "w") as f:
            json.dump(reeval_plan, f, indent=2)
        
        # Save priority re-evaluation plan
        with open(self.results_dir / "priority_reeval_plan.json", "w") as f:
            json.dump(priority_plan, f, indent=2)
        
        # Create summary report
        report = f"""
RE-EVALUATION PLAN SUMMARY
==========================

MISSING DATA OVERVIEW:
- Missing Characters: {len(reeval_plan['missing_characters'])}
- Missing Combinations: {len(reeval_plan['missing_combinations'])}
- Re-eval Commands: {len(reeval_plan['reeval_commands'])}
- Estimated Time: {reeval_plan['estimated_time']} minutes

PRIORITY PLAN:
- Main Characters Missing: {len(priority_plan['main_characters_missing'])}
- Trait Ablations Missing: {len(priority_plan['trait_ablations_missing'])}
- Priority Commands: {len(priority_plan['priority_commands'])}
- Estimated Time: {priority_plan['estimated_time']} minutes

RECOMMENDED APPROACH:
1. Start with priority plan (main characters first)
2. Run trait ablations after main characters are complete
3. Monitor progress and adjust as needed
4. Use parallel execution for faster completion

FILES CREATED:
- complete_reeval_plan.json: Complete re-evaluation plan
- priority_reeval_plan.json: Priority re-evaluation plan
"""
        
        with open(self.results_dir / "reeval_plan_report.txt", "w") as f:
            f.write(report)
        
        print(f"📁 Re-evaluation plan saved to: {self.results_dir}")
    
    def run_reeval_planning(self):
        """Run re-evaluation planning"""
        print("🔬 Running Re-evaluation Planning")
        print("=" * 60)
        print(f"Missing Characters: {len(self.validation_results['missing_data'])}")
        print(f"Missing Combinations: {self.validation_results['summary']['missing_files']}")
        print("=" * 60)
        
        # Create re-evaluation plans
        reeval_plan = self.create_reeval_plan()
        priority_plan = self.create_priority_reeval_plan()
        
        # Save plans
        self.save_reeval_plan(reeval_plan, priority_plan)
        
        # Print summary
        print(f"\n📊 RE-EVALUATION SUMMARY:")
        print(f"  • Missing Characters: {len(reeval_plan['missing_characters'])}")
        print(f"  • Missing Combinations: {len(reeval_plan['missing_combinations'])}")
        print(f"  • Re-eval Commands: {len(reeval_plan['reeval_commands'])}")
        print(f"  • Estimated Time: {reeval_plan['estimated_time']} minutes")
        
        print(f"\n🎯 PRIORITY PLAN:")
        print(f"  • Main Characters Missing: {len(priority_plan['main_characters_missing'])}")
        print(f"  • Trait Ablations Missing: {len(priority_plan['trait_ablations_missing'])}")
        print(f"  • Priority Commands: {len(priority_plan['priority_commands'])}")
        print(f"  • Estimated Time: {priority_plan['estimated_time']} minutes")
        
        print(f"\n📁 Results saved to: {self.results_dir}")
        
        return reeval_plan, priority_plan

def main():
    """Main function"""
    reevaluator = MissingDataReevaluator()
    reevaluator.run_reeval_planning()

if __name__ == "__main__":
    main()
