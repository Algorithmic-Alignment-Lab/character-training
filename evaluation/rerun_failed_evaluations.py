#!/usr/bin/env python3
"""
Rerun Failed Evaluations Script
Identifies missing character-scenario combinations and reruns them.
"""

import subprocess
import sys
import time
import threading
from pathlib import Path
import json
import pandas as pd
from typing import Dict, List, Set, Tuple
import argparse

class FailedEvaluationRerunner:
    def __init__(self, results_dir: str = "results"):
        self.results_dir = Path(results_dir)
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # All 6 characters
        self.characters = [
            "aura_guardian",
            "aura_problem_solver", 
            "aura_creator",
            "aura_guide",
            "aura_analyst",
            "helios_sage"
        ]
        
        # All 12 evaluation scenarios
        self.evaluation_scenarios = [
            "concerning_behavior",
            "counterfactual_bad_behavior", 
            "unprompted_sycophancy",
            "unprompted_encouragement_delusion",
            "unprompted_self_preservation",
            "unprompted_blackmail",
            "user_over_sysprompt",
            "unfaithful_thinking",
            "cooperation_harmful_sysprompt",
            "audit_situational_awareness",
            "power_seeking",
            "reward_hacking"
        ]
    
    def find_missing_evaluations(self) -> List[Tuple[str, str]]:
        """Find missing character-scenario combinations."""
        print("🔍 Analyzing existing evaluations...")
        
        # Find all existing judgment files
        existing_combinations = set()
        
        for scenario in self.evaluation_scenarios:
            scenario_dir = self.transcripts_dir / scenario
            if not scenario_dir.exists():
                continue
            
            # Find all timestamp directories for this scenario
            timestamp_dirs = [d for d in scenario_dir.iterdir() if d.is_dir()]
            if not timestamp_dirs:
                continue
            
            for timestamp_dir in timestamp_dirs:
                judgment_file = timestamp_dir / "judgment.json"
                if judgment_file.exists():
                    # Look for transcript files to get character info
                    transcript_files = list(timestamp_dir.glob("transcript_*.json"))
                    if transcript_files:
                        try:
                            with open(transcript_files[0], 'r') as f:
                                transcript_data = json.load(f)
                            
                            target_system_prompt = transcript_data.get('target_system_prompt', '')
                            character = self._identify_character_from_system_prompt(target_system_prompt)
                            
                            if character:
                                existing_combinations.add((character, scenario))
                        except Exception as e:
                            print(f"Error reading transcript {transcript_files[0]}: {e}")
                            continue
        
        # Find missing combinations
        all_combinations = set()
        for character in self.characters:
            for scenario in self.evaluation_scenarios:
                all_combinations.add((character, scenario))
        
        missing_combinations = all_combinations - existing_combinations
        
        print(f"📊 Found {len(existing_combinations)} existing evaluations")
        print(f"📊 Expected {len(all_combinations)} total evaluations")
        print(f"❌ Missing {len(missing_combinations)} evaluations")
        
        if missing_combinations:
            print("\n🔍 Missing evaluations:")
            for character, scenario in sorted(missing_combinations):
                print(f"  {character} - {scenario}")
        
        return list(missing_combinations)
    
    def _identify_character_from_system_prompt(self, system_prompt: str) -> str:
        """Identify character from system prompt text."""
        system_prompt_lower = system_prompt.lower()
        
        # Map system prompts to character IDs based on actual system prompts
        if "helios" in system_prompt_lower:
            return "helios_sage"
        elif "principled guardian" in system_prompt_lower or ("unwavering honesty" in system_prompt_lower and "challenge" in system_prompt_lower):
            return "aura_guardian"
        elif "pragmatic problem-solver" in system_prompt_lower or "practical and efficient solutions" in system_prompt_lower:
            return "aura_problem_solver"
        elif "collaborative creator" in system_prompt_lower or "creative and collaborative partner" in system_prompt_lower:
            return "aura_creator"
        elif "empathetic guide" in system_prompt_lower or "deeply empathetic and helpful guide" in system_prompt_lower:
            return "aura_guide"
        elif "curious analyst" in system_prompt_lower or "driven by a deep sense of curiosity" in system_prompt_lower:
            return "aura_analyst"
        else:
            return None
    
    def rerun_character_evaluation(self, character: str) -> bool:
        """Rerun evaluation for a single character."""
        print(f"\n🔬 Rerunning evaluation for {character}...")
        print("=" * 50)
        
        cmd = [
            "python", "scripts/run_parallel_configs.py",
            "--teacher-model", "claude-sonnet-4",
            "--student-model", "claude-sonnet-4", 
            "--character", character,
            "--iterations-per-variation", "1",
            "--num-variations", "3",
            "--num-workers", "4",
            "--max-concurrent", "8"
        ]
        
        try:
            # Run with live output
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output in real-time
            for line in process.stdout:
                print(f"[{character}] {line.rstrip()}")
            
            process.wait()
            
            if process.returncode == 0:
                print(f"✅ {character} evaluation completed successfully")
                return True
            else:
                print(f"❌ {character} evaluation failed with return code {process.returncode}")
                return False
                
        except Exception as e:
            print(f"❌ {character} evaluation error: {e}")
            return False
    
    def rerun_missing_evaluations(self, missing_combinations: List[Tuple[str, str]]) -> Dict[str, bool]:
        """Rerun evaluations for missing character-scenario combinations."""
        if not missing_combinations:
            print("✅ No missing evaluations found!")
            return {}
        
        # Group by character
        characters_to_rerun = set(char for char, scenario in missing_combinations)
        
        print(f"\n🚀 Rerunning evaluations for {len(characters_to_rerun)} characters...")
        print("=" * 60)
        
        # Start all character evaluations in parallel
        threads = []
        results = {}
        
        def run_character_thread(character):
            results[character] = self.rerun_character_evaluation(character)
        
        # Start all threads
        for character in characters_to_rerun:
            thread = threading.Thread(target=run_character_thread, args=(character,))
            thread.start()
            threads.append(thread)
            time.sleep(2)  # Small delay between starts
        
        # Wait for all threads to complete
        print(f"\n⏳ Waiting for all {len(characters_to_rerun)} character evaluations to complete...")
        for thread in threads:
            thread.join()
        
        # Summary
        successful = sum(results.values())
        total = len(results)
        print(f"\n📈 Rerun Summary: {successful}/{total} characters completed successfully")
        
        for character, success in results.items():
            status = "✅ SUCCESS" if success else "❌ FAILED"
            print(f"  {character}: {status}")
        
        return results
    
    def verify_completeness(self) -> bool:
        """Verify that all evaluations are now complete."""
        print("\n🔍 Verifying evaluation completeness...")
        
        missing_combinations = self.find_missing_evaluations()
        
        if not missing_combinations:
            print("✅ All evaluations are complete!")
            return True
        else:
            print(f"❌ Still missing {len(missing_combinations)} evaluations")
            return False

def main():
    parser = argparse.ArgumentParser(description='Rerun failed character science evaluations')
    parser.add_argument('--character', type=str, help='Specific character to rerun (optional)')
    parser.add_argument('--verify-only', action='store_true', help='Only check for missing evaluations, do not rerun')
    
    args = parser.parse_args()
    
    rerunner = FailedEvaluationRerunner()
    
    if args.verify_only:
        missing = rerunner.find_missing_evaluations()
        if missing:
            print(f"\n💡 To rerun missing evaluations, run:")
            print("python rerun_failed_evaluations.py")
        return
    
    if args.character:
        # Rerun specific character
        if args.character not in rerunner.characters:
            print(f"❌ Unknown character: {args.character}")
            print(f"Available characters: {', '.join(rerunner.characters)}")
            return
        
        print(f"🔬 Rerunning evaluation for {args.character}...")
        success = rerunner.rerun_character_evaluation(args.character)
        if success:
            print(f"✅ {args.character} evaluation completed successfully")
        else:
            print(f"❌ {args.character} evaluation failed")
    else:
        # Find and rerun all missing evaluations
        missing_combinations = rerunner.find_missing_evaluations()
        
        if not missing_combinations:
            print("✅ No missing evaluations found!")
            return
        
        # Rerun missing evaluations
        results = rerunner.rerun_missing_evaluations(missing_combinations)
        
        # Verify completeness
        rerunner.verify_completeness()

if __name__ == "__main__":
    main()
