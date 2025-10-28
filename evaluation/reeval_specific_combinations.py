#!/usr/bin/env python3
"""
Re-evaluate Specific Missing Combinations
Re-runs only the missing character-evaluation combinations
"""

import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
import subprocess
import sys

class SpecificCombinationReevaluator:
    """Re-evaluates specific missing character-evaluation combinations"""
    
    def __init__(self, results_dir: str = "specific_reeval_results"):
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
    
    def identify_missing_combinations(self) -> List[Tuple[str, str]]:
        """Identify specific missing character-evaluation combinations"""
        print("🔍 Identifying missing character-evaluation combinations...")
        
        missing_combinations = []
        
        for char, results in self.validation_results['missing_data'].items():
            for eval_name in results['missing_files']:
                missing_combinations.append((char, eval_name))
        
        print(f"Found {len(missing_combinations)} missing combinations")
        return missing_combinations
    
    def create_reeval_commands(self, missing_combinations: List[Tuple[str, str]]) -> List[str]:
        """Create re-evaluation commands for missing combinations"""
        print("📋 Creating re-evaluation commands...")
        
        commands = []
        
        for char, eval_name in missing_combinations:
            # Create command for this specific combination
            command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluation {eval_name} --timestamp {self.validation_results['timestamp']}"
            commands.append(command)
        
        return commands
    
    def create_batch_commands(self, missing_combinations: List[Tuple[str, str]]) -> List[str]:
        """Create batch commands to group similar evaluations"""
        print("📋 Creating batch re-evaluation commands...")
        
        # Group by character
        char_groups = {}
        for char, eval_name in missing_combinations:
            if char not in char_groups:
                char_groups[char] = []
            char_groups[char].append(eval_name)
        
        batch_commands = []
        
        for char, eval_names in char_groups.items():
            # Create batch command for this character
            command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluations {','.join(eval_names)} --timestamp {self.validation_results['timestamp']}"
            batch_commands.append(command)
        
        return batch_commands
    
    def create_parallel_commands(self, missing_combinations: List[Tuple[str, str]], batch_size: int = 5) -> List[List[str]]:
        """Create parallel execution groups"""
        print(f"📋 Creating parallel execution groups (batch size: {batch_size})...")
        
        # Group combinations into batches
        batches = []
        for i in range(0, len(missing_combinations), batch_size):
            batch = missing_combinations[i:i + batch_size]
            batches.append(batch)
        
        # Create parallel commands for each batch
        parallel_commands = []
        for batch in batches:
            batch_commands = []
            for char, eval_name in batch:
                command = f"python run_ablation_evaluations_simple_parallel.py --character {char} --evaluation {eval_name} --timestamp {self.validation_results['timestamp']}"
                batch_commands.append(command)
            parallel_commands.append(batch_commands)
        
        return parallel_commands
    
    def save_reeval_plan(self, missing_combinations: List[Tuple[str, str]], 
                        individual_commands: List[str], 
                        batch_commands: List[str], 
                        parallel_commands: List[List[str]]):
        """Save re-evaluation plan"""
        
        # Save missing combinations
        with open(self.results_dir / "missing_combinations.json", "w") as f:
            json.dump(missing_combinations, f, indent=2)
        
        # Save individual commands
        with open(self.results_dir / "individual_commands.txt", "w") as f:
            for command in individual_commands:
                f.write(command + "\n")
        
        # Save batch commands
        with open(self.results_dir / "batch_commands.txt", "w") as f:
            for command in batch_commands:
                f.write(command + "\n")
        
        # Save parallel commands
        with open(self.results_dir / "parallel_commands.txt", "w") as f:
            for i, batch in enumerate(parallel_commands):
                f.write(f"# Batch {i+1}\n")
                for command in batch:
                    f.write(command + "\n")
                f.write("\n")
        
        # Create summary report
        report = f"""
SPECIFIC COMBINATION RE-EVALUATION PLAN
=======================================

MISSING COMBINATIONS: {len(missing_combinations)}
INDIVIDUAL COMMANDS: {len(individual_commands)}
BATCH COMMANDS: {len(batch_commands)}
PARALLEL BATCHES: {len(parallel_commands)}

MISSING COMBINATIONS BY CHARACTER:
"""
        
        # Group by character for summary
        char_groups = {}
        for char, eval_name in missing_combinations:
            if char not in char_groups:
                char_groups[char] = []
            char_groups[char].append(eval_name)
        
        for char, eval_names in char_groups.items():
            report += f"\n{char}: {len(eval_names)} missing evaluations"
            report += f"\n  Missing: {', '.join(eval_names[:5])}{'...' if len(eval_names) > 5 else ''}"
        
        report += f"""

EXECUTION OPTIONS:
1. Individual: Run each combination separately
2. Batch: Run all missing evaluations for each character together
3. Parallel: Run multiple combinations in parallel

RECOMMENDED APPROACH:
- Use batch commands for efficiency
- Run parallel batches for speed
- Monitor progress and adjust as needed

FILES CREATED:
- missing_combinations.json: List of missing combinations
- individual_commands.txt: Individual re-evaluation commands
- batch_commands.txt: Batch re-evaluation commands
- parallel_commands.txt: Parallel execution commands
"""
        
        with open(self.results_dir / "reeval_plan_report.txt", "w") as f:
            f.write(report)
        
        print(f"📁 Re-evaluation plan saved to: {self.results_dir}")
    
    def run_reeval_planning(self):
        """Run re-evaluation planning for specific combinations"""
        print("🔬 Running Specific Combination Re-evaluation Planning")
        print("=" * 60)
        
        # Identify missing combinations
        missing_combinations = self.identify_missing_combinations()
        
        # Create different types of commands
        individual_commands = self.create_reeval_commands(missing_combinations)
        batch_commands = self.create_batch_commands(missing_combinations)
        parallel_commands = self.create_parallel_commands(missing_combinations, batch_size=5)
        
        # Save plans
        self.save_reeval_plan(missing_combinations, individual_commands, batch_commands, parallel_commands)
        
        # Print summary
        print(f"\n📊 RE-EVALUATION SUMMARY:")
        print(f"  • Missing Combinations: {len(missing_combinations)}")
        print(f"  • Individual Commands: {len(individual_commands)}")
        print(f"  • Batch Commands: {len(batch_commands)}")
        print(f"  • Parallel Batches: {len(parallel_commands)}")
        
        # Show some examples
        print(f"\n📋 EXAMPLE COMMANDS:")
        print(f"  Individual: {individual_commands[0] if individual_commands else 'None'}")
        print(f"  Batch: {batch_commands[0] if batch_commands else 'None'}")
        print(f"  Parallel Batch 1: {len(parallel_commands[0]) if parallel_commands else 0} commands")
        
        print(f"\n📁 Results saved to: {self.results_dir}")
        
        return missing_combinations, individual_commands, batch_commands, parallel_commands

def main():
    """Main function"""
    reevaluator = SpecificCombinationReevaluator()
    reevaluator.run_reeval_planning()

if __name__ == "__main__":
    main()
