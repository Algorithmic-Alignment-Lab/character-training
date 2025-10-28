#!/usr/bin/env python3
"""
Simple Parallel Ablation Evaluation Runner
Runs multiple characters simultaneously without threading issues.
"""

import json
import subprocess
import time
import shutil
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple
import psutil
import sys
from datetime import datetime

# Test Configuration
# Change these values to adjust the test parameters:
TEST_NUM_CHARACTERS = 33  # Number of characters to test with (default: 1 for agentic testing), 33 for all characters
TEST_NUM_VARIATIONS = 10  # Number of variations per character (default: 1 for quick testing)
TEST_NUM_WORKERS = 20     # Number of workers for testing (default: 2)
TEST_PARALLEL_CHARACTERS = 2  # Number of characters to run simultaneously (default: 1 for agentic testing)

# Model Configuration
EVALUATED_MODEL = "claude-sonnet-4"  # Model to evaluate (was "claude-sonnet-4")
TEACHER_MODEL = "claude-sonnet-4"  # Model used for teaching/generation

# Copy from existing run (optional)
COPY_FROM_EXISTING = False  # Set to False to run evaluations directly
SOURCE_RUN_TIMESTAMP = "20251021-172456"  # Target timestamp to re-evaluate

class SimpleParallelAblationEvaluator:
    def __init__(self, evaluation_dir: str = "."):
        self.evaluation_dir = Path(evaluation_dir)
        self.results_dir = self.evaluation_dir / "results"
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Load all characters
        self.characters = self._load_characters() # use all characters
        # For agentic testing, use the test agentic character
        if "test_agentic_character" in self.characters:
            self.character_ids = ["test_agentic_character"]
        else:
            self.character_ids = list(self.characters.keys())[:TEST_NUM_CHARACTERS]  # Test with configured number of characters
        
        # Progress tracking (no threading locks)
        self.progress_file = Path("progress.txt")
        self.start_time = time.time()
        self.completed_characters = []
        self.failed_characters = []
        self.running_characters = []
        
        # Missing evaluation tracking
        self.missing_combinations = []
        self.missing_count = 0
        
        # Simple parallel settings
        self.max_workers = TEST_PARALLEL_CHARACTERS  # Number of characters to run simultaneously
        self.max_concurrent_per_char = TEST_NUM_WORKERS
        
        print(f"🚀 Simple Parallel Ablation Evaluator")
        print(f"📊 Total Characters: {len(self.character_ids)} (Testing with {TEST_NUM_CHARACTERS})")
        print(f"📊 Variations per character: {TEST_NUM_VARIATIONS}")
        print(f"⚡ Characters in parallel: {self.max_workers}")
        print(f"⚡ Concurrent per character: {self.max_concurrent_per_char}")
        print(f"🤖 Evaluated Model: {EVALUATED_MODEL}")
        print(f"👨‍🏫 Teacher Model: {TEACHER_MODEL}")
        if COPY_FROM_EXISTING:
            print(f"📋 Copying from existing run: {SOURCE_RUN_TIMESTAMP}")
        else:
            print(f"🎯 Re-evaluating timestamp: {SOURCE_RUN_TIMESTAMP}")
        print(f"📝 Progress file: {self.progress_file}")
        print(f"🎯 Target completion: ~2-3 hours")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def detect_missing_evaluations(self, target_timestamp: str) -> None:
        """Detect missing character-evaluation combinations using the same logic as validation script"""
        print(f"\n🔍 Detecting missing evaluations for timestamp: {target_timestamp}")
        
        missing_combinations = []
        
        # Define all expected evaluations (same as validation script)
        all_evaluations = [
            "power_seeking_agentic", "reward_hacking_agentic", "sabotage_agentic", 
            "data_exfiltration_agentic", "animal_welfare", "unprompted_blackmail_agentic",
            "concerning_behavior", "counterfactual_bad_behavior", "unprompted_sycophancy",
            "unprompted_encouragement_delusion", "unprompted_self_preservation", "unprompted_blackmail",
            "user_over_sysprompt", "unfaithful_thinking", "cooperation_harmful_sysprompt",
            "audit_situational_awareness", "power_seeking", "reward_hacking"
        ]
        
        for character_id in self.character_ids:
            for eval_name in all_evaluations:
                # Check if judgment.json exists and has valid data
                # Try both path formats: {character_id}_{timestamp} and {timestamp}
                judgment_path1 = self.transcripts_dir / eval_name / f"{character_id}_{target_timestamp}" / "judgment.json"
                judgment_path2 = self.transcripts_dir / eval_name / target_timestamp / "judgment.json"
                
                # Use the path that exists
                if judgment_path1.exists():
                    judgment_path = judgment_path1
                elif judgment_path2.exists():
                    judgment_path = judgment_path2
                else:
                    # Try to find any directory with this timestamp in this evaluation
                    eval_dir = self.transcripts_dir / eval_name
                    if eval_dir.exists():
                        timestamp_dirs = [d for d in eval_dir.iterdir() if d.is_dir() and target_timestamp in d.name]
                        if timestamp_dirs:
                            # Use the first matching directory
                            judgment_path = timestamp_dirs[0] / "judgment.json"
                        else:
                            missing_combinations.append((character_id, eval_name))
                            continue
                    else:
                        missing_combinations.append((character_id, eval_name))
                        continue
                
                # Check if judgment.json has valid data
                try:
                    with open(judgment_path, 'r') as f:
                        judgment_data = json.load(f)
                    
                    # Check for average_eval_success_score
                    if "summary_statistics" not in judgment_data:
                        missing_combinations.append((character_id, eval_name))
                        continue
                    
                    summary = judgment_data["summary_statistics"]
                    if "average_eval_success_score" not in summary or summary["average_eval_success_score"] == 0:
                        missing_combinations.append((character_id, eval_name))
                        
                except Exception as e:
                    print(f"  ⚠️  Error reading {judgment_path}: {e}")
                    missing_combinations.append((character_id, eval_name))
        
        self.missing_combinations = missing_combinations
        self.missing_count = len(missing_combinations)
        
        print(f"📊 Missing evaluations detected: {self.missing_count}")
        
        if self.missing_count > 0:
            print(f"📋 Missing combinations:")
            # Group by character for better display
            char_missing = {}
            for char, eval_name in missing_combinations:
                if char not in char_missing:
                    char_missing[char] = []
                char_missing[char].append(eval_name)
            
            for char, evals in char_missing.items():
                print(f"  • {char}: {len(evals)} missing ({', '.join(evals[:3])}{'...' if len(evals) > 3 else ''})")
        else:
            print("✅ No missing evaluations found - all data is complete!")
    
    def get_missing_for_character(self, character_id: str) -> List[str]:
        """Get missing evaluations for a specific character"""
        return [eval_name for char, eval_name in self.missing_combinations if char == character_id]
    
    def update_progress(self, character: str, status: str, message: str = "") -> None:
        """Update progress file with current status (no threading)."""
        current_time = datetime.now().strftime("%H:%M:%S")
        elapsed = (time.time() - self.start_time) / 60  # minutes
        
        # Update internal tracking
        if status == "completed":
            if character in self.running_characters:
                self.running_characters.remove(character)
            if character not in self.completed_characters:
                self.completed_characters.append(character)
        elif status == "failed":
            if character in self.running_characters:
                self.running_characters.remove(character)
            if character not in self.failed_characters:
                self.failed_characters.append(character)
        elif status == "running":
            if character not in self.running_characters:
                self.running_characters.append(character)
        
        # Calculate progress
        total_chars = len(self.character_ids)
        completed_count = len(self.completed_characters)
        progress_percent = (completed_count / total_chars) * 100
        
        # Estimate remaining time
        if completed_count > 0:
            avg_time_per_char = elapsed / completed_count
            remaining_chars = total_chars - completed_count
            estimated_remaining = remaining_chars * avg_time_per_char
        else:
            estimated_remaining = 0
        
        # Write progress file
        with open(self.progress_file, 'w') as f:
            f.write(f"🚀 Simple Parallel Ablation Evaluation Progress\n")
            f.write(f"⏰ Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"⏱️  Elapsed: {elapsed:.1f} minutes\n")
            f.write(f"📊 Progress: {completed_count}/{total_chars} characters ({progress_percent:.1f}%)\n")
            f.write(f"🔮 Estimated remaining: {estimated_remaining:.1f} minutes\n")
            f.write(f"⚡ Characters in parallel: {self.max_workers}\n")
            f.write(f"⚡ Concurrent per character: {self.max_concurrent_per_char}\n")
            f.write(f"📊 Missing evaluations: {self.missing_count}\n")
            f.write(f"🎯 Re-evaluating timestamp: {SOURCE_RUN_TIMESTAMP}\n")
            f.write(f"\n")
            f.write(f"✅ Completed ({len(self.completed_characters)}):\n")
            for char in self.completed_characters:
                missing_for_char = self.get_missing_for_character(char)
                f.write(f"  • {char} ({len(missing_for_char)} missing)\n")
            f.write(f"\n")
            f.write(f"❌ Failed ({len(self.failed_characters)}):\n")
            for char in self.failed_characters:
                f.write(f"  • {char}\n")
            f.write(f"\n")
            f.write(f"🔄 Currently running ({len(self.running_characters)}):\n")
            for char in self.running_characters:
                missing_for_char = self.get_missing_for_character(char)
                f.write(f"  • {char} ({len(missing_for_char)} missing)\n")
            f.write(f"\n")
            f.write(f"📝 Last update: {current_time}\n")
            f.write(f"📝 Status: {character} - {status} - {message}\n")
    
    
    def run_fair_parallel_evaluations(self) -> Dict[str, bool]:
        """Two-phase evaluation system for fair comparisons"""
        
        if COPY_FROM_EXISTING:
            # Use existing variations from specified run
            print(f"\n📋 Using existing variations from: {SOURCE_RUN_TIMESTAMP}")
            source_timestamp = SOURCE_RUN_TIMESTAMP
            
            # Verify the source run exists
            if not self.verify_source_run_exists(source_timestamp):
                print(f"❌ Source run {source_timestamp} not found")
                return {}
            
            # Generate new timestamp for this run
            new_timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            print(f"🆕 New run timestamp: {new_timestamp}")
            
            # Copy variations to all characters with new timestamp
            print(f"\n📋 Copying variations to all characters with new timestamp...")
            if not self.copy_existing_files_to_all_characters(source_timestamp, new_timestamp):
                print("❌ Failed to copy files to other characters")
                return {}
            
            # Run all characters in parallel with new timestamp
            print(f"\n⚡ Running all characters in parallel with new timestamp...")
            return self.run_all_characters_with_copied_files(new_timestamp)
        else:
            # Direct re-evaluation flow: Use target timestamp directly
            print(f"\n🎯 Direct Re-evaluation: Using target timestamp {SOURCE_RUN_TIMESTAMP}")
            target_timestamp = SOURCE_RUN_TIMESTAMP
            
            # Detect missing evaluations first
            self.detect_missing_evaluations(target_timestamp)
            
            if self.missing_count == 0:
                print("✅ No missing evaluations found - all data is complete!")
                return {char: True for char in self.character_ids}
            
            # Run all characters in parallel with target timestamp
            print(f"\n⚡ Running all characters in parallel with target timestamp...")
            print(f"📊 Will re-run {self.missing_count} missing evaluations")
            return self.run_all_characters_with_target_timestamp(target_timestamp)

    def run_first_character_generation(self, character: str) -> str:
        """Run first character to generate all variations - returns the timestamp it generated"""
        
        # Generate a timestamp for the first character
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        character_timestamp = f"{character}_{timestamp}"
        
        cmd = [
            "python", "scripts/run_parallel_configs.py",
            "--teacher-model", TEACHER_MODEL,
            "--student-model", EVALUATED_MODEL, 
            "--character", character,
            "--iterations-per-variation", "1",
            "--num-variations", str(TEST_NUM_VARIATIONS),  # Use configured number of variations
            "--num-workers", str(TEST_NUM_WORKERS),        # Use configured number of workers
            "--max-concurrent", str(TEST_NUM_WORKERS),     # Use configured number of concurrent
            "--timestamp", character_timestamp  # Use character-specific timestamp
        ]
        
        # Update progress in main process
        self.update_progress(character, "running", "Generating variations...")
        
        try:
            print(f"🔧 Running command: {' '.join(cmd)}")
            print(f"📁 Working directory: {self.evaluation_dir}")
            print("📝 Live output:")
            print("-" * 50)
            
            # Run with real-time output streaming
            process = subprocess.Popen(cmd, cwd=self.evaluation_dir, 
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Stream output in real-time with timeout
            output_lines = []
            start_time = time.time()
            timeout_seconds = 1200  # 20 minutes
            
            while True:
                # Check for timeout
                if time.time() - start_time > timeout_seconds:
                    print("⏰ Process timed out, killing...")
                    process.kill()
                    return None
                
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    output_lines.append(output.strip())
            
            # Wait for process to complete
            return_code = process.wait()
            
            print("-" * 50)
            print(f"🏁 Process completed with return code: {return_code}")
            
            if return_code == 0:
                self.update_progress(character, "completed", f"Generated variations with timestamp {character_timestamp}")
                return character_timestamp
            else:
                error_details = f"Return code {return_code}"
                if output_lines:
                    error_details += f"\nOutput: {'\\n'.join(output_lines[-10:])}"  # Last 10 lines
                self.update_progress(character, "failed", f"Failed to generate variations: {error_details}")
                return None
                
        except subprocess.TimeoutExpired:
            print("⏰ Process timed out after 1200 seconds")
            process.kill()
            self.update_progress(character, "failed", "Process timed out after 1200 seconds")
            return None
        except Exception as e:
            print(f"❌ Exception: {e}")
            self.update_progress(character, "failed", f"Exception: {str(e)}")
            return None

    def extract_generated_timestamp(self, character: str) -> str:
        """Extract the timestamp that was generated by the first character using folder structure"""
        # Look in the results directory for the most recent timestamp
        results_dir = Path("results/transcripts")
        
        # Define target scenarios to look in (same as create_graphs.py)
        target_scenarios = [
            "power_seeking_agentic",
            "reward_hacking_agentic", 
            "sabotage_agentic",
            "data_exfiltration_agentic",
            "animal_welfare",
            "unprompted_blackmail_agentic",
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
        
        print(f"🔍 Looking for most recent timestamp for character: {character}")
        print(f"🎯 Searching in {len(target_scenarios)} target scenarios")
        
        # Find the most recent timestamp for this character across target scenarios only
        character_dirs = []
        for evaluation_dir in results_dir.iterdir():
            if evaluation_dir.is_dir() and evaluation_dir.name in target_scenarios:
                for timestamp_dir in evaluation_dir.iterdir():
                    if timestamp_dir.is_dir():
                        # Check if this directory starts with the character name
                        if timestamp_dir.name.startswith(f"{character}_"):
                            character_dirs.append(timestamp_dir)
                            print(f"   Found: {evaluation_dir.name}/{timestamp_dir.name}")
        
        if character_dirs:
            # Get the most recent one by modification time
            latest_dir = max(character_dirs, key=lambda x: x.stat().st_mtime)
            # Extract just the timestamp part (remove character prefix)
            timestamp = latest_dir.name.replace(f"{character}_", "")
            print(f"   Most recent: {latest_dir.name} -> timestamp: {timestamp}")
            return timestamp
        else:
            print(f"   ❌ No directories found for character: {character} in target scenarios")
            return None

    def copy_generated_files_to_all_characters(self, source_character: str, source_character_timestamp: str) -> bool:
        """Copy generated files from first character to all other characters"""
        try:
            # Extract just the timestamp part from the character_timestamp
            # source_character_timestamp is like "aura_guardian_20250121-143022"
            # We need to extract "20250121-143022"
            timestamp = source_character_timestamp.replace(f"{source_character}_", "")
            
            # Find all evaluation directories that have the source character's timestamp
            results_dir = Path("results/transcripts")
            source_dirs = []
            
            for evaluation_dir in results_dir.iterdir():
                if evaluation_dir.is_dir():
                    source_dir = evaluation_dir / source_character_timestamp
                    if source_dir.exists():
                        source_dirs.append((evaluation_dir, source_dir))
            
            if not source_dirs:
                print(f"❌ No source directories found for {source_character_timestamp}")
                return False
            
            print(f"📁 Found {len(source_dirs)} evaluation directories to copy from")
            
            # Copy to all other characters
            for character in self.character_ids[1:]:  # Skip first character
                target_character_timestamp = f"{character}_{timestamp}"
                
                for evaluation_dir, source_dir in source_dirs:
                    target_dir = evaluation_dir / target_character_timestamp
                    
                    print(f"📋 Copying from {source_dir} to {target_dir}")
                    
                    # Create target directory
                    target_dir.mkdir(parents=True, exist_ok=True)
                    
                    # Copy the required files
                    files_to_copy = ["decomposition.json", "ideation.json", "variation.json"]
                    for filename in files_to_copy:
                        source_file = source_dir / filename
                        target_file = target_dir / filename
                        
                        if source_file.exists():
                            shutil.copy2(source_file, target_file)
                            print(f"  ✅ Copied {filename}")
                        else:
                            print(f"  ⚠️  Source file not found: {source_file}")
                    
            return True
        except Exception as e:
            print(f"❌ Error copying files: {e}")
            return False

    def run_remaining_characters_with_copied_files(self, source_character_timestamp: str) -> Dict[str, bool]:
        """Run all OTHER characters in parallel using copied files (excluding first character)"""
        results = {}
        
        # Extract just the timestamp part from the character_timestamp
        # source_character_timestamp is like "aura_guardian_20250121-143022"
        # We need to extract "20250121-143022"
        timestamp = source_character_timestamp.replace(f"{self.character_ids[0]}_", "")
        
        # First character is already completed, so we only run the remaining ones
        remaining_characters = self.character_ids[1:]  # Exclude first character
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_character = {}
            
            for char_id in remaining_characters:
                character_timestamp = f"{char_id}_{timestamp}"
                
                future = executor.submit(self.run_single_character_with_timestamp, char_id, character_timestamp)
                future_to_character[future] = char_id
            
            # Process completed evaluations with centralized progress tracking
            completed = 1  # First character is already done
            for future in as_completed(future_to_character):
                char_id = future_to_character[future]
                try:
                    char_id, success, error = future.result()
                    results[char_id] = success
                    completed += 1
                    
                    # Update progress in main process
                    if success:
                        self.update_progress(char_id, "completed", f"Completed with timestamp {character_timestamp}")
                    else:
                        self.update_progress(char_id, "failed", f"Failed: {error}")
                    
                    # Progress statistics
                    elapsed = time.time() - self.start_time
                    avg_time_per_char = elapsed / completed
                    remaining_chars = len(self.character_ids) - completed
                    estimated_remaining = remaining_chars * avg_time_per_char
                    
                    print(f"\n📈 Progress Update:")
                    print(f"  ✅ Completed: {completed}/{len(self.character_ids)} characters")
                    print(f"  ⏱️  Elapsed: {elapsed/60:.1f} minutes")
                    print(f"  🔮 Estimated remaining: {estimated_remaining/60:.1f} minutes")
                    print(f"  📊 Success rate: {sum(results.values())/completed*100:.1f}%")
                    
                    if not success:
                        print(f"  ❌ Failed: {char_id}")
                        print(f"     Error: {error}")
                        
                except Exception as e:
                    results[char_id] = False
                    completed += 1
                    self.update_progress(char_id, "failed", f"Exception: {e}")
        
        # Add first character to results (it's already completed)
        results[self.character_ids[0]] = True
        
        return results
    
    def run_single_character_with_timestamp(self, character_id: str, timestamp: str) -> Tuple[str, bool, str]:
        """Run evaluation for a single character with specific timestamp"""
        cmd = [
            "python", "scripts/run_parallel_configs.py",
            "--teacher-model", TEACHER_MODEL,
            "--student-model", EVALUATED_MODEL, 
            "--character", character_id,
            "--iterations-per-variation", "1",
            "--num-variations", str(TEST_NUM_VARIATIONS),  # Use configured number of variations
            "--num-workers", str(TEST_NUM_WORKERS),        # Use configured number of workers
            "--max-concurrent", str(TEST_NUM_WORKERS),     # Use configured number of concurrent
            "--timestamp", timestamp  # Use specific timestamp
        ]
        
        try:
            print(f"🔧 Running command: {' '.join(cmd)}")
            print(f"📁 Working directory: {self.evaluation_dir}")
            print("📝 Live output:")
            print("-" * 50)
            
            # Run with real-time output streaming
            process = subprocess.Popen(cmd, cwd=self.evaluation_dir, 
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Stream output in real-time with timeout
            output_lines = []
            start_time = time.time()
            timeout_seconds = 1200  # 20 minutes
            
            while True:
                # Check for timeout
                if time.time() - start_time > timeout_seconds:
                    print("⏰ Process timed out, killing...")
                    process.kill()
                    return character_id, False, "Process timed out after 1200 seconds"
                
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    output_lines.append(output.strip())
            
            # Wait for process to complete
            return_code = process.wait()
            
            print("-" * 50)
            print(f"🏁 Process completed with return code: {return_code}")
            
            if return_code == 0:
                return character_id, True, ""
            else:
                error_details = f"Return code {return_code}"
                if output_lines:
                    error_details += f"\nOutput: {'\\n'.join(output_lines[-10:])}"  # Last 10 lines
                return character_id, False, error_details
                
        except subprocess.TimeoutExpired:
            print("⏰ Process timed out after 1200 seconds")
            process.kill()
            return character_id, False, "Process timed out after 1200 seconds"
        except Exception as e:
            print(f"❌ Exception: {e}")
            return character_id, False, f"Exception: {str(e)}"

    def verify_variations_count(self, character_timestamp: str) -> bool:
        """Verify that we have the expected number of variations"""
        try:
            results_dir = Path("results/transcripts")
            expected_variations = TEST_NUM_VARIATIONS
            
            # Get all evaluation scenarios from character evaluations
            target_scenarios = set()
            for character_id in self.character_ids:
                if character_id in self.characters:
                    character = self.characters[character_id]
                    if "evaluations" in character:
                        target_scenarios.update(character["evaluations"])
            
            variations_found = 0
            total_checked = 0
            
            for evaluation_dir in results_dir.iterdir():
                if evaluation_dir.is_dir() and evaluation_dir.name in target_scenarios:
                    timestamp_dir = evaluation_dir / character_timestamp
                    if timestamp_dir.exists():
                        variation_file = timestamp_dir / "variation.json"
                        if variation_file.exists():
                            try:
                                with open(variation_file, 'r') as f:
                                    variation_data = json.load(f)
                                    scenario_numbers = variation_data.get("scenario_numbers", [])
                                    variations_found = max(variations_found, len(scenario_numbers))
                                    total_checked += 1
                                    print(f"  📊 {evaluation_dir.name}: {len(scenario_numbers)} variations")
                            except Exception as e:
                                print(f"  ⚠️  Error reading {variation_file}: {e}")
            
            print(f"📊 Verification: Found {variations_found} variations (expected: {expected_variations})")
            print(f"📊 Checked {total_checked} evaluation directories")
            
            return variations_found >= expected_variations
            
        except Exception as e:
            print(f"❌ Error verifying variations: {e}")
            return False

    def retry_with_cleanup(self, character: str) -> Dict[str, bool]:
        """Retry the first phase with complete cleanup"""
        print(f"\n🔄 Retry Phase: Cleaning up and retrying with {character}...")
        
        # Step 1: Clean up all existing files
        print("🧹 Step 1: Cleaning up existing files...")
        self.cleanup_existing_files()
        
        # Step 2: Retry first character generation
        print("🔄 Step 2: Retrying first character generation...")
        first_character_timestamp = self.run_first_character_generation(character)
        
        if not first_character_timestamp:
            print("❌ Retry failed - could not generate base variations")
            return {}
        
        print(f"✅ Retry successful - generated timestamp: {first_character_timestamp}")
        
        # Step 3: Verify variations again
        if not self.verify_variations_count(first_character_timestamp):
            print("❌ Retry failed - still insufficient variations")
            return {}
        
        # Step 4: Continue with normal process
        print("📋 Step 4: Copying variations to all characters...")
        if not self.copy_generated_files_to_all_characters(character, first_character_timestamp):
            print("❌ Failed to copy files to other characters")
            return {}
        
        print("⚡ Step 5: Running all other characters in parallel...")
        return self.run_remaining_characters_with_copied_files(first_character_timestamp)

    def cleanup_existing_files(self) -> None:
        """Clean up all existing evaluation files"""
        try:
            results_dir = Path("results/transcripts")
            
            if not results_dir.exists():
                print("  📁 No results directory found - nothing to clean")
                return
            
            # Get all evaluation scenarios from character evaluations
            target_scenarios = set()
            for character_id in self.character_ids:
                if character_id in self.characters:
                    character = self.characters[character_id]
                    if "evaluations" in character:
                        target_scenarios.update(character["evaluations"])
            
            print(f"  📋 Found {len(target_scenarios)} evaluation scenarios to clean:")
            for scenario in sorted(target_scenarios):
                print(f"    • {scenario}")
            
            cleaned_count = 0
            
            for evaluation_dir in results_dir.iterdir():
                if evaluation_dir.is_dir() and evaluation_dir.name in target_scenarios:
                    print(f"  🧹 Cleaning {evaluation_dir.name}...")
                    
                    # Remove all timestamp directories in this evaluation
                    for timestamp_dir in evaluation_dir.iterdir():
                        if timestamp_dir.is_dir():
                            try:
                                shutil.rmtree(timestamp_dir)
                                cleaned_count += 1
                                print(f"    ✅ Removed {timestamp_dir.name}")
                            except Exception as e:
                                print(f"    ⚠️  Error removing {timestamp_dir.name}: {e}")
            
            print(f"🧹 Cleanup complete: Removed {cleaned_count} directories")
            
        except Exception as e:
            print(f"❌ Error during cleanup: {e}")

    def verify_source_run_exists(self, source_timestamp: str) -> bool:
        """Verify that the source run exists and has the expected files"""
        try:
            results_dir = Path("results/transcripts")
            
            # Define target scenarios to look in (same as create_graphs.py)
            target_scenarios = [
                "power_seeking_agentic",
                "reward_hacking_agentic", 
                "sabotage_agentic",
                "data_exfiltration_agentic",
                "animal_welfare",
                "unprompted_blackmail_agentic",
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
            
            print(f"🔍 Verifying source run: {source_timestamp}")
            found_scenarios = 0
            
            for evaluation_dir in results_dir.iterdir():
                if evaluation_dir.is_dir() and evaluation_dir.name in target_scenarios:
                    source_dir = evaluation_dir / source_timestamp
                    if source_dir.exists():
                        # Check for required files
                        required_files = ["decomposition.json", "ideation.json", "variation.json"]
                        files_exist = all((source_dir / f).exists() for f in required_files)
                        if files_exist:
                            found_scenarios += 1
                            print(f"   ✅ Found: {evaluation_dir.name}/{source_timestamp}")
                        else:
                            print(f"   ⚠️  Missing files in: {evaluation_dir.name}/{source_timestamp}")
                    else:
                        print(f"   ❌ Missing: {evaluation_dir.name}/{source_timestamp}")
            
            print(f"📊 Found {found_scenarios} scenarios with complete data")
            return found_scenarios > 0
            
        except Exception as e:
            print(f"❌ Error verifying source run: {e}")
            return False

    def copy_existing_files_to_all_characters(self, source_timestamp: str, new_timestamp: str) -> bool:
        """Copy existing files from source run to all characters with new timestamp"""
        try:
            results_dir = Path("results/transcripts")
            
            # Define target scenarios
            target_scenarios = [
                "power_seeking_agentic",
                "reward_hacking_agentic", 
                "sabotage_agentic",
                "data_exfiltration_agentic",
                "animal_welfare",
                "unprompted_blackmail_agentic",
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
            
            print(f"📁 Copying from {source_timestamp} to all characters with timestamp {new_timestamp}")
            
            # Copy to all characters
            for character in self.character_ids:
                target_character_timestamp = f"{character}_{new_timestamp}"
                
                for evaluation_dir in results_dir.iterdir():
                    if evaluation_dir.is_dir() and evaluation_dir.name in target_scenarios:
                        source_dir = evaluation_dir / source_timestamp
                        target_dir = evaluation_dir / target_character_timestamp
                        
                        if source_dir.exists():
                            print(f"📋 Copying from {source_dir} to {target_dir}")
                            
                            # Create target directory
                            target_dir.mkdir(parents=True, exist_ok=True)
                            
                            # Copy the required files
                            files_to_copy = ["decomposition.json", "ideation.json", "variation.json"]
                            for filename in files_to_copy:
                                source_file = source_dir / filename
                                target_file = target_dir / filename
                                
                                if source_file.exists():
                                    shutil.copy2(source_file, target_file)
                                    print(f"  ✅ Copied {filename}")
                                else:
                                    print(f"  ⚠️  Source file not found: {source_file}")
                        else:
                            print(f"  ⚠️  Source directory not found: {source_dir}")
            
            return True
        except Exception as e:
            print(f"❌ Error copying existing files: {e}")
            return False

    def run_all_characters_with_copied_files(self, new_timestamp: str) -> Dict[str, bool]:
        """Run all characters in parallel using copied files with new timestamp"""
        results = {}
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_character = {}
            
            for char_id in self.character_ids:
                character_timestamp = f"{char_id}_{new_timestamp}"
                
                future = executor.submit(self.run_single_character_with_timestamp, char_id, character_timestamp)
                future_to_character[future] = char_id
            
            # Process completed evaluations with centralized progress tracking
            completed = 0
            for future in as_completed(future_to_character):
                char_id = future_to_character[future]
                try:
                    char_id, success, error = future.result()
                    results[char_id] = success
                    completed += 1
                    
                    # Update progress in main process
                    if success:
                        self.update_progress(char_id, "completed", f"Completed with timestamp {character_timestamp}")
                    else:
                        self.update_progress(char_id, "failed", f"Failed: {error}")
                    
                    # Progress statistics
                    elapsed = time.time() - self.start_time
                    avg_time_per_char = elapsed / completed
                    remaining_chars = len(self.character_ids) - completed
                    estimated_remaining = remaining_chars * avg_time_per_char
                    
                    print(f"\n📈 Progress Update:")
                    print(f"  ✅ Completed: {completed}/{len(self.character_ids)} characters")
                    print(f"  ⏱️  Elapsed: {elapsed/60:.1f} minutes")
                    print(f"  🔮 Estimated remaining: {estimated_remaining/60:.1f} minutes")
                    print(f"  📊 Success rate: {sum(results.values())/completed*100:.1f}%")
                    
                    if not success:
                        print(f"  ❌ Failed: {char_id}")
                        print(f"     Error: {error}")
                        
                except Exception as e:
                    results[char_id] = False
                    completed += 1
                    self.update_progress(char_id, "failed", f"Exception: {e}")
        
        return results

    def run_all_characters_with_target_timestamp(self, target_timestamp: str) -> Dict[str, bool]:
        """Run all characters in parallel using target timestamp directly"""
        results = {}
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_character = {}
            
            for char_id in self.character_ids:
                character_timestamp = f"{char_id}_{target_timestamp}"
                missing_for_char = self.get_missing_for_character(char_id)
                
                if missing_for_char:
                    print(f"🔄 {char_id}: {len(missing_for_char)} missing evaluations")
                    future = executor.submit(self.run_single_character_with_timestamp, char_id, character_timestamp)
                    future_to_character[future] = char_id
                else:
                    print(f"✅ {char_id}: No missing evaluations - skipping")
                    results[char_id] = True
            
            # Process completed evaluations with centralized progress tracking
            completed = 0
            for future in as_completed(future_to_character):
                char_id = future_to_character[future]
                try:
                    char_id, success, error = future.result()
                    results[char_id] = success
                    completed += 1
                    
                    # Update progress in main process
                    if success:
                        self.update_progress(char_id, "completed", f"Completed with timestamp {character_timestamp}")
                    else:
                        self.update_progress(char_id, "failed", f"Failed: {error}")
                    
                    # Progress statistics
                    elapsed = time.time() - self.start_time
                    avg_time_per_char = elapsed / completed
                    remaining_chars = len(self.character_ids) - completed
                    estimated_remaining = remaining_chars * avg_time_per_char
                    
                    print(f"\n📈 Progress Update:")
                    print(f"  ✅ Completed: {completed}/{len(self.character_ids)} characters")
                    print(f"  ⏱️  Elapsed: {elapsed/60:.1f} minutes")
                    print(f"  🔮 Estimated remaining: {estimated_remaining/60:.1f} minutes")
                    print(f"  📊 Success rate: {sum(results.values())/completed*100:.1f}%")
                    
                    if not success:
                        print(f"  ❌ Failed: {char_id}")
                        print(f"     Error: {error}")
                        
                except Exception as e:
                    results[char_id] = False
                    completed += 1
                    self.update_progress(char_id, "failed", f"Exception: {e}")
        
        return results

    def run_complete_fair_parallel_pipeline(self) -> None:
        """Run the complete fair parallel pipeline."""
        print("🚀 Fair Parallel Ablation Evaluation Pipeline")
        print("=" * 60)
        
        # Step 1: Run fair parallel evaluations (two-phase system)
        print("\n📊 Step 1: Running fair parallel evaluations...")
        results = self.run_fair_parallel_evaluations()
        
        # Step 2: Quick retry for failed evaluations (using same fair system)
        failed_characters = [char for char, success in results.items() if not success]
        if failed_characters:
            print(f"\n🔄 Step 2: Quick retry for {len(failed_characters)} failed characters...")
            print("📋 Using fair evaluation system for retries...")
            
            # Get the source timestamp from the first character (which should have succeeded)
            source_character_timestamp = self.extract_generated_timestamp(self.character_ids[0])
            if not source_character_timestamp:
                print("❌ Cannot retry - no source timestamp found")
                return results
            
            # Extract just the timestamp part
            timestamp = source_character_timestamp.replace(f"{self.character_ids[0]}_", "")
            
            # Retry failed characters using the same copied files
            for character in failed_characters:
                character_timestamp = f"{character}_{timestamp}"
                char_id, success, error = self.run_single_character_with_timestamp(character, character_timestamp)
                if success:
                    results[character] = True
                    self.update_progress(character, "completed", f"Retry succeeded with timestamp {character_timestamp}")
                    print(f"✅ {character} succeeded on retry")
                else:
                    self.update_progress(character, "failed", f"Retry failed: {error}")
                    print(f"❌ {character} failed on retry: {error}")
        
        # Step 3: Generate graphs
        print("\n📈 Step 3: Generating graphs...")
        try:
            process = subprocess.Popen(
                ['python', 'create_graphs.py'],
                cwd=self.evaluation_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            print("📝 Graph creation live output:")
            print("-" * 50)
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    output_lines.append(output.strip())
            return_code = process.wait()
            print("-" * 50)
            if return_code == 0:
                print("✅ Graphs created successfully!")
                self.update_progress("GRAPHS", "completed", "Graphs generated successfully")
            else:
                print("❌ Error creating graphs")
                print(f"   Return code: {return_code}")
                # Print the last several lines of output for debugging
                if output_lines:
                    print(f"   Last lines of output:")
                    for line in output_lines[-10:]:
                        print(line)
                self.update_progress("GRAPHS", "failed", f"Graph generation failed: Return code {return_code}\nOutput: {'\\n'.join(output_lines[-10:])}")
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")
            self.update_progress("GRAPHS", "failed", f"Graph error: {e}")
        
        
        # Display final summary with detailed error information
        print("\n🎉 Fair Parallel Pipeline Complete!")
        print("=" * 60)
        print("📁 Results saved in results/transcripts/")
        print("📝 Final progress saved in progress.txt")
        print("🎯 All characters used identical variations for fair comparison!")
        
        # Show detailed results summary
        successful_chars = [char for char, success in results.items() if success]
        failed_chars = [char for char, success in results.items() if not success]
        
        print(f"\n📊 Final Results Summary:")
        print(f"  ✅ Successful: {len(successful_chars)}/{len(results)} characters")
        if successful_chars:
            print(f"     • {', '.join(successful_chars)}")
        if failed_chars:
            print(f"  ❌ Failed: {len(failed_chars)}/{len(results)} characters")
            print(f"     • {', '.join(failed_chars)}")
            print(f"\n💡 Check the progress.txt file for detailed error information.")

def main():
    evaluator = SimpleParallelAblationEvaluator()
    evaluator.run_complete_fair_parallel_pipeline()

if __name__ == "__main__":
    main()
