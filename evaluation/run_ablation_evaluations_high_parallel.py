#!/usr/bin/env python3
"""
High Parallelism Ablation Evaluation Runner
Maximum speed with progress.txt monitoring.
"""

import json
import subprocess
import time
import threading
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple
import psutil
import sys
from datetime import datetime

class HighParallelAblationEvaluator:
    def __init__(self, evaluation_dir: str = "."):
        self.evaluation_dir = Path(evaluation_dir)
        self.results_dir = self.evaluation_dir / "results"
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Load all characters
        self.characters = self._load_characters()
        self.character_ids = list(self.characters.keys())
        
        # Progress tracking
        self.progress_file = Path("progress.txt")
        self.start_time = time.time()
        self.completed_characters = []
        self.failed_characters = []
        self.progress_lock = threading.Lock()
        
        # Maximum parallelism settings
        self.max_workers = 16  # Very high parallelism
        self.max_concurrent = 24  # Very high concurrent
        
        print(f"🚀 High Parallelism Ablation Evaluator")
        print(f"📊 Total Characters: {len(self.character_ids)}")
        print(f"⚡ Max Workers: {self.max_workers}")
        print(f"⚡ Max Concurrent: {self.max_concurrent}")
        print(f"📝 Progress file: {self.progress_file}")
        print(f"🎯 Target completion: ~2-3 hours")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def update_progress(self, character: str, status: str, message: str = "") -> None:
        """Update progress file with current status."""
        with self.progress_lock:
            current_time = datetime.now().strftime("%H:%M:%S")
            elapsed = (time.time() - self.start_time) / 60  # minutes
            
            # Update internal tracking
            if status == "completed":
                self.completed_characters.append(character)
            elif status == "failed":
                self.failed_characters.append(character)
            
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
                f.write(f"🚀 High Parallelism Ablation Evaluation Progress\n")
                f.write(f"⏰ Started: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"⏱️  Elapsed: {elapsed:.1f} minutes\n")
                f.write(f"📊 Progress: {completed_count}/{total_chars} characters ({progress_percent:.1f}%)\n")
                f.write(f"🔮 Estimated remaining: {estimated_remaining:.1f} minutes\n")
                f.write(f"⚡ Workers: {self.max_workers}, Concurrent: {self.max_concurrent}\n")
                f.write(f"\n")
                f.write(f"✅ Completed ({len(self.completed_characters)}):\n")
                for char in self.completed_characters:
                    f.write(f"  • {char}\n")
                f.write(f"\n")
                f.write(f"❌ Failed ({len(self.failed_characters)}):\n")
                for char in self.failed_characters:
                    f.write(f"  • {char}\n")
                f.write(f"\n")
                f.write(f"🔄 Currently running:\n")
                f.write(f"  • {character}: {status} - {message}\n")
                f.write(f"\n")
                f.write(f"📝 Last update: {current_time}\n")
    
    def run_single_character_evaluation(self, character_id: str) -> Tuple[str, bool, str]:
        """Run evaluation for a single character with maximum optimization."""
        self.update_progress(character_id, "starting", "Initializing evaluation...")
        
        try:
            # Ultra-optimized command
            cmd = [
                "python", "scripts/run_parallel_configs.py",
                "--teacher-model", "claude-sonnet-4",
                "--student-model", "claude-sonnet-4", 
                "--character", character_id,
                "--iterations-per-variation", "1",
                "--num-variations", "10",
                "--num-workers", str(self.max_concurrent),  # Use max concurrent
                "--max-concurrent", str(self.max_concurrent)
            ]
            
            self.update_progress(character_id, "running", f"Running {len(cmd)} scenarios...")
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.evaluation_dir,
                capture_output=True,
                text=True,
                timeout=900  # 15 minute timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                self.update_progress(character_id, "completed", f"Success in {elapsed/60:.1f} minutes")
                return character_id, True, ""
            else:
                error_msg = f"Return code {result.returncode}"
                self.update_progress(character_id, "failed", f"Failed: {error_msg}")
                return character_id, False, error_msg
                
        except subprocess.TimeoutExpired:
            self.update_progress(character_id, "failed", "Timeout after 15 minutes")
            return character_id, False, "Timeout"
        except Exception as e:
            self.update_progress(character_id, "failed", f"Exception: {str(e)}")
            return character_id, False, str(e)
    
    def run_high_parallel_evaluations(self) -> Dict[str, bool]:
        """Run evaluations with maximum parallelism."""
        print(f"\n🚀 Starting HIGH PARALLELISM evaluations...")
        print(f"⚡ Workers: {self.max_workers}")
        print(f"⚡ Concurrent: {self.max_concurrent}")
        print(f"📊 Characters: {len(self.character_ids)}")
        print(f"📝 Monitor progress: cat progress.txt")
        
        results = {}
        
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all character evaluations
            future_to_character = {
                executor.submit(self.run_single_character_evaluation, char_id): char_id 
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
                    
                    elapsed = time.time() - self.start_time
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
        
        total_time = time.time() - self.start_time
        successful = sum(results.values())
        failed = len(results) - successful
        
        # Final progress update
        self.update_progress("FINAL", "completed", f"All evaluations finished in {total_time/60:.1f} minutes")
        
        print(f"\n🎉 High parallelism evaluations completed!")
        print(f"⏱️  Total time: {total_time/60:.1f} minutes")
        print(f"✅ Successful: {successful}/{len(self.character_ids)} characters")
        print(f"❌ Failed: {failed}/{len(self.character_ids)} characters")
        
        return results
    
    def run_complete_high_parallel_pipeline(self) -> None:
        """Run the complete high parallelism pipeline."""
        print("🚀 High Parallelism Ablation Evaluation Pipeline")
        print("=" * 60)
        
        # Step 1: Run all character evaluations with maximum parallelism
        print("\n📊 Step 1: Running high parallelism evaluations...")
        results = self.run_high_parallel_evaluations()
        
        # Step 2: Quick retry for failed evaluations
        failed_characters = [char for char, success in results.items() if not success]
        if failed_characters:
            print(f"\n🔄 Step 2: Quick retry for {len(failed_characters)} failed characters...")
            for character in failed_characters:
                char_id, success, error = self.run_single_character_evaluation(character)
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
                self.update_progress("GRAPHS", "completed", "Graphs generated successfully")
            else:
                print("❌ Error creating graphs")
                self.update_progress("GRAPHS", "failed", "Graph generation failed")
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")
            self.update_progress("GRAPHS", "failed", f"Graph error: {e}")
        
        print("\n🎉 High Parallelism Pipeline Complete!")
        print("📁 Results saved in results/transcripts/")
        print("📝 Final progress saved in progress.txt")

def main():
    evaluator = HighParallelAblationEvaluator()
    evaluator.run_complete_high_parallel_pipeline()

if __name__ == "__main__":
    main()

