#!/usr/bin/env python3
"""
Run Missing Re-evaluation
Modified version of run_ablation_evaluations_simple_parallel.py that only re-runs missing combinations
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
import argparse

# Test Configuration
TEST_NUM_CHARACTERS = 33  # Number of characters to test with
TEST_NUM_VARIATIONS = 10  # Number of variations per character
TEST_NUM_WORKERS = 20     # Number of workers for testing
TEST_PARALLEL_CHARACTERS = 2  # Number of characters to run simultaneously

# Model Configuration
EVALUATED_MODEL = "claude-sonnet-4"  # Model to evaluate
TEACHER_MODEL = "claude-sonnet-4"  # Model used for teaching/generation

class MissingReevaluator:
    def __init__(self, evaluation_dir: str = ".", target_timestamp: str = None):
        self.evaluation_dir = Path(evaluation_dir)
        self.results_dir = self.evaluation_dir / "results"
        self.transcripts_dir = self.results_dir / "transcripts"
        self.target_timestamp = target_timestamp
        
        # Load all characters
        self.characters = self._load_characters()
        self.character_ids = list(self.characters.keys())[:TEST_NUM_CHARACTERS]
        
        # Load missing combinations
        self.missing_combinations = self._load_missing_combinations()
        
        # Progress tracking
        self.progress_file = Path("progress.txt")
        self.start_time = time.time()
        self.completed_characters = []
        self.failed_characters = []
        self.running_characters = []
        
        # Parallel settings
        self.max_workers = TEST_PARALLEL_CHARACTERS
        self.max_concurrent_per_char = TEST_NUM_WORKERS
        
        print(f"🚀 Missing Re-evaluation Runner")
        print(f"📊 Target Timestamp: {self.target_timestamp}")
        print(f"📊 Total Characters: {len(self.character_ids)}")
        print(f"📊 Missing Combinations: {len(self.missing_combinations)}")
        print(f"⚡ Characters in parallel: {self.max_workers}")
        print(f"⚡ Concurrent per character: {self.max_concurrent_per_char}")
        print(f"🤖 Evaluated Model: {EVALUATED_MODEL}")
        print(f"👨‍🏫 Teacher Model: {TEACHER_MODEL}")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def _load_missing_combinations(self) -> List[Tuple[str, str]]:
        """Load missing character-evaluation combinations from validation results"""
        try:
            with open("final_validation_results/validation_results.json", "r") as f:
                validation_results = json.load(f)
            
            missing_combinations = []
            for char, results in validation_results['missing_data'].items():
                for eval_name in results['missing_files']:
                    missing_combinations.append((char, eval_name))
            
            return missing_combinations
        except Exception as e:
            print(f"❌ Error loading missing combinations: {e}")
            return []
    
    def update_progress(self, character: str, status: str, message: str = "") -> None:
        """Update progress file with current status"""
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
            f.write(f"🚀 Missing Re-evaluation Progress\n")
            f.write(f"⏰ Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"⏱️  Elapsed: {elapsed:.1f} minutes\n")
            f.write(f"📊 Progress: {completed_count}/{total_chars} characters ({progress_percent:.1f}%)\n")
            f.write(f"🔮 Estimated remaining: {estimated_remaining:.1f} minutes\n")
            f.write(f"📊 Missing Combinations: {len(self.missing_combinations)}\n")
            f.write(f"\n")
            f.write(f"✅ Completed ({len(self.completed_characters)}):\n")
            for char in self.completed_characters:
                f.write(f"  • {char}\n")
            f.write(f"\n")
            f.write(f"❌ Failed ({len(self.failed_characters)}):\n")
            for char in self.failed_characters:
                f.write(f"  • {char}\n")
            f.write(f"\n")
            f.write(f"🔄 Currently running ({len(self.running_characters)}):\n")
            for char in self.running_characters:
                f.write(f"  • {char}\n")
            f.write(f"\n")
            f.write(f"📝 Last update: {current_time}\n")
            f.write(f"📝 Status: {character} - {status} - {message}\n")
    
    def run_missing_reevaluations(self) -> Dict[str, bool]:
        """Run re-evaluations for missing combinations only"""
        
        if not self.missing_combinations:
            print("✅ No missing combinations found - all data is complete!")
            return {}
        
        print(f"\n📋 Found {len(self.missing_combinations)} missing combinations to re-evaluate")
        
        # Group missing combinations by character
        char_missing_evals = {}
        for char, eval_name in self.missing_combinations:
            if char not in char_missing_evals:
                char_missing_evals[char] = []
            char_missing_evals[char].append(eval_name)
        
        print(f"📊 Characters with missing data: {len(char_missing_evals)}")
        for char, evals in char_missing_evals.items():
            print(f"  • {char}: {len(evals)} missing evaluations")
        
        # Run re-evaluations for characters with missing data
        results = {}
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_character = {}
            
            for char_id, missing_evals in char_missing_evals.items():
                if char_id in self.character_ids:
                    future = executor.submit(self.run_single_character_missing_evals, char_id, missing_evals)
                    future_to_character[future] = char_id
            
            # Process completed evaluations
            completed = 0
            for future in as_completed(future_to_character):
                char_id = future_to_character[future]
                try:
                    char_id, success, error = future.result()
                    results[char_id] = success
                    completed += 1
                    
                    # Update progress
                    if success:
                        self.update_progress(char_id, "completed", f"Re-evaluated missing combinations")
                    else:
                        self.update_progress(char_id, "failed", f"Failed: {error}")
                    
                    # Progress statistics
                    elapsed = time.time() - self.start_time
                    avg_time_per_char = elapsed / completed if completed > 0 else 0
                    remaining_chars = len(char_missing_evals) - completed
                    estimated_remaining = remaining_chars * avg_time_per_char
                    
                    print(f"\n📈 Progress Update:")
                    print(f"  ✅ Completed: {completed}/{len(char_missing_evals)} characters")
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
    
    def run_single_character_missing_evals(self, character_id: str, missing_evals: List[str]) -> Tuple[str, bool, str]:
        """Run evaluation for a single character with only missing evaluations"""
        
        # Create command - the script will run all evaluations for the character
        # but we'll check which ones are missing and only process those
        cmd = [
            "python", "scripts/run_parallel_configs.py",
            "--teacher-model", TEACHER_MODEL,
            "--student-model", EVALUATED_MODEL, 
            "--character", character_id,
            "--iterations-per-variation", "1",
            "--num-variations", str(TEST_NUM_VARIATIONS),
            "--num-workers", str(TEST_NUM_WORKERS),
            "--max-concurrent", str(TEST_NUM_WORKERS),
            "--timestamp", self.target_timestamp
        ]
        
        try:
            print(f"🔧 Running command: {' '.join(cmd)}")
            print(f"📁 Working directory: {self.evaluation_dir}")
            print(f"📊 Missing evaluations for {character_id}: {missing_evals}")
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
                    error_details += f"\nOutput: {'\\n'.join(output_lines[-10:])}"
                return character_id, False, error_details
                
        except subprocess.TimeoutExpired:
            print("⏰ Process timed out after 1200 seconds")
            process.kill()
            return character_id, False, "Process timed out after 1200 seconds"
        except Exception as e:
            print(f"❌ Exception: {e}")
            return character_id, False, f"Exception: {str(e)}"
    
    def run_complete_missing_reeval_pipeline(self) -> None:
        """Run the complete missing re-evaluation pipeline"""
        print("🚀 Missing Re-evaluation Pipeline")
        print("=" * 60)
        
        # Step 1: Run missing re-evaluations
        print("\n📊 Step 1: Running missing re-evaluations...")
        results = self.run_missing_reevaluations()
        
        # Step 2: Generate graphs
        print("\n📈 Step 2: Generating graphs...")
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
                if output_lines:
                    print(f"   Last lines of output:")
                    for line in output_lines[-10:]:
                        print(line)
                self.update_progress("GRAPHS", "failed", f"Graph generation failed: Return code {return_code}")
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")
            self.update_progress("GRAPHS", "failed", f"Graph error: {e}")
        
        # Display final summary
        print("\n🎉 Missing Re-evaluation Pipeline Complete!")
        print("=" * 60)
        print("📁 Results saved in results/transcripts/")
        print("📝 Final progress saved in progress.txt")
        print("🎯 Only missing combinations were re-evaluated!")
        
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
    parser = argparse.ArgumentParser(description='Run missing re-evaluations for specific timestamp')
    parser.add_argument('--timestamp', type=str, required=True, help='Target timestamp to re-evaluate')
    parser.add_argument('--evaluation-dir', type=str, default='.', help='Evaluation directory')
    
    args = parser.parse_args()
    
    evaluator = MissingReevaluator(evaluation_dir=args.evaluation_dir, target_timestamp=args.timestamp)
    evaluator.run_complete_missing_reeval_pipeline()

if __name__ == "__main__":
    main()
