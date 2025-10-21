#!/usr/bin/env python3
"""
Evaluation Completeness Module
Checks for missing evaluations and handles reruns automatically.
"""

import subprocess
import time
import threading
from pathlib import Path
import json
from typing import Dict, List, Set, Tuple
import pandas as pd

class EvaluationCompletenessChecker:
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
        print("🔍 Checking evaluation completeness...")
        
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
                            print(f"Warning: Error reading transcript {transcript_files[0]}: {e}")
                            continue
        
        # Find missing combinations
        all_combinations = set()
        for character in self.characters:
            for scenario in self.evaluation_scenarios:
                all_combinations.add((character, scenario))
        
        missing_combinations = all_combinations - existing_combinations
        
        print(f"📊 Found {len(existing_combinations)} existing evaluations")
        print(f"📊 Expected {len(all_combinations)} total evaluations")
        
        if missing_combinations:
            print(f"❌ Missing {len(missing_combinations)} evaluations:")
            for character, scenario in sorted(missing_combinations):
                print(f"  {character} - {scenario}")
        else:
            print("✅ All evaluations are complete!")
        
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
    
    def rerun_missing_evaluations(self, missing_combinations: List[Tuple[str, str]], max_retries: int = 3) -> bool:
        """Rerun evaluations for missing character-scenario combinations with retries."""
        if not missing_combinations:
            print("✅ No missing evaluations found!")
            return True
        
        # Group by character
        characters_to_rerun = set(char for char, scenario in missing_combinations)
        
        print(f"\n🚀 Rerunning evaluations for {len(characters_to_rerun)} characters...")
        print("=" * 60)
        
        # Try up to max_retries times
        for attempt in range(1, max_retries + 1):
            print(f"\n🔄 Attempt {attempt}/{max_retries}")
            
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
            
            # Check if we're now complete
            remaining_missing = self.find_missing_evaluations()
            if not remaining_missing:
                print(f"✅ All evaluations completed successfully on attempt {attempt}!")
                return True
            
            # If not complete and we have more attempts, continue
            if attempt < max_retries:
                print(f"⚠️  Still missing {len(remaining_missing)} evaluations, retrying...")
                characters_to_rerun = set(char for char, scenario in remaining_missing)
            else:
                print(f"❌ Failed to complete all evaluations after {max_retries} attempts")
                print(f"Still missing: {remaining_missing}")
                return False
        
        return False
    
    def ensure_complete_evaluations(self, max_retries: int = 3) -> bool:
        """Ensure all evaluations are complete, with automatic retries."""
        print("\n🔍 Ensuring evaluation completeness...")
        
        # Check for missing evaluations
        missing_combinations = self.find_missing_evaluations()
        
        if not missing_combinations:
            print("✅ All evaluations are already complete!")
            return True
        
        # Rerun missing evaluations with retries
        success = self.rerun_missing_evaluations(missing_combinations, max_retries)
        
        if success:
            print("✅ All evaluations are now complete!")
        else:
            print("❌ Some evaluations are still missing after all retries")
        
        return success
