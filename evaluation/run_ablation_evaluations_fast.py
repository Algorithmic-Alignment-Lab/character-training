#!/usr/bin/env python3
"""
Fast Ablation Evaluation Runner
Optimized for speed with higher parallelism and resource management.
"""

import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple
import psutil
import sys

class FastAblationEvaluator:
    def __init__(self, evaluation_dir: str = "."):
        self.evaluation_dir = Path(evaluation_dir)
        self.results_dir = self.evaluation_dir / "results"
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Load all characters
        self.characters = self._load_characters()
        self.character_ids = list(self.characters.keys())
        
        # Optimize based on system resources
        self.optimal_workers = self._calculate_optimal_workers()
        
        print(f"🔬 Fast Ablation Evaluator Initialized")
        print(f"📊 Total Characters: {len(self.character_ids)}")
        print(f"⚡ Optimal Workers: {self.optimal_workers}")
        print(f"📊 Expected Time: ~{len(self.character_ids) * 5.5 / 60:.1f} minutes")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def _calculate_optimal_workers(self) -> int:
        """Calculate optimal number of workers based on system resources."""
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        
        print(f"💻 System Resources:")
        print(f"  • CPU cores: {cpu_count}")
        print(f"  • Memory: {memory_gb:.1f}GB")
        
        # Optimize for speed
        if cpu_count >= 8 and memory_gb >= 16:
            return 12  # High parallelism
        elif cpu_count >= 6 and memory_gb >= 12:
            return 8   # Medium-high parallelism
        elif cpu_count >= 4 and memory_gb >= 8:
            return 6   # Medium parallelism
        else:
            return 4   # Conservative parallelism
    
    def run_single_character_evaluation_fast(self, character_id: str) -> Tuple[str, bool, str]:
        """Run evaluation for a single character with optimized settings."""
        print(f"\n🚀 Starting FAST evaluation for {character_id}...")
        
        try:
            # Optimized command with higher parallelism
            cmd = [
                "python", "scripts/run_parallel_configs.py",
                "--teacher-model", "claude-sonnet-4",
                "--student-model", "claude-sonnet-4", 
                "--character", character_id,
                "--iterations-per-variation", "1",
                "--num-variations", "10",
                "--num-workers", "6",        # Increased from 4
                "--max-concurrent", "12"    # Increased from 8
            ]
            
            print(f"📋 Command: {' '.join(cmd)}")
            start_time = time.time()
            
            # Run with timeout
            result = subprocess.run(
                cmd,
                cwd=self.evaluation_dir,
                timeout=1200  # 20 minute timeout per character
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {character_id} completed in {elapsed/60:.1f} minutes")
                return character_id, True, ""
            else:
                error_msg = f"Error in {character_id}: return code {result.returncode}"
                print(f"❌ {character_id} failed: {error_msg}")
                return character_id, False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout for {character_id}"
            print(f"⏰ {character_id} timed out after 20 minutes")
            return character_id, False, error_msg
        except Exception as e:
            error_msg = f"Exception for {character_id}: {str(e)}"
            print(f"💥 {character_id} failed: {error_msg}")
            return character_id, False, error_msg
    
    def run_fast_parallel_evaluations(self) -> Dict[str, bool]:
        """Run evaluations with maximum parallelism."""
        print(f"\n🔄 Starting FAST parallel evaluations...")
        print(f"⚡ Workers: {self.optimal_workers}")
        print(f"📊 Characters: {len(self.character_ids)}")
        
        results = {}
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=self.optimal_workers) as executor:
            # Submit all character evaluations
            future_to_character = {
                executor.submit(self.run_single_character_evaluation_fast, char_id): char_id 
                for char_id in self.character_ids
            }
            
            # Process completed evaluations
            completed = 0
            for future in as_completed(future_to_character):
                char_id = future_to_character[future]
                try:
                    char_id, success, error = future.result()
                    results[char_id] = success
                    completed += 1
                    
                    elapsed = time.time() - start_time
                    avg_time_per_char = elapsed / completed
                    remaining_chars = len(self.character_ids) - completed
                    estimated_remaining = remaining_chars * avg_time_per_char
                    
                    print(f"📈 Progress: {completed}/{len(self.character_ids)} characters")
                    print(f"⏱️  Elapsed: {elapsed/60:.1f} minutes")
                    print(f"🔮 Estimated remaining: {estimated_remaining/60:.1f} minutes")
                    
                    if not success:
                        print(f"❌ Failed: {char_id} - {error}")
                        
                except Exception as e:
                    print(f"💥 Exception processing {char_id}: {e}")
                    results[char_id] = False
                    completed += 1
        
        total_time = time.time() - start_time
        successful = sum(results.values())
        failed = len(results) - successful
        
        print(f"\n🎉 Fast parallel evaluations completed!")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"✅ Successful: {successful}/{len(self.character_ids)} characters")
        print(f"❌ Failed: {failed}/{len(self.character_ids)} characters")
        
        return results
    
    def run_complete_fast_pipeline(self) -> None:
        """Run the complete fast ablation evaluation pipeline."""
        print("🚀 Fast Ablation Evaluation Pipeline")
        print("=" * 50)
        
        # Step 1: Run all character evaluations with maximum parallelism
        print("\n📊 Step 1: Running fast ablation evaluations...")
        results = self.run_fast_parallel_evaluations()
        
        # Step 2: Quick retry for failed evaluations
        failed_characters = [char for char, success in results.items() if not success]
        if failed_characters:
            print(f"\n🔄 Step 2: Quick retry for {len(failed_characters)} failed characters...")
            for character in failed_characters:
                char_id, success, error = self.run_single_character_evaluation_fast(character)
                if success:
                    results[character] = True
                    print(f"✅ {character} succeeded on retry")
        
        # Step 3: Generate graphs
        print("\n📈 Step 3: Generating graphs...")
        try:
            result = subprocess.run(['python', 'create_graphs.py'], 
                                  capture_output=True, text=True, cwd=self.evaluation_dir)
            if result.returncode == 0:
                print("✅ Graphs created successfully!")
            else:
                print("❌ Error creating graphs")
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")
        
        print("\n🎉 Fast Ablation Pipeline Complete!")
        print("📁 Results saved in results/transcripts/")

def main():
    evaluator = FastAblationEvaluator()
    evaluator.run_complete_fast_pipeline()

if __name__ == "__main__":
    main()

