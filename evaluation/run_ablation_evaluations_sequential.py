#!/usr/bin/env python3
"""
Sequential Trait Ablation Evaluation Runner
Runs evaluations for all 36 characters sequentially with clear progress logging.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import List, Dict, Tuple
import sys

class SequentialAblationEvaluator:
    def __init__(self, evaluation_dir: str = "."):
        self.evaluation_dir = Path(evaluation_dir)
        self.results_dir = self.evaluation_dir / "results"
        self.transcripts_dir = self.results_dir / "transcripts"
        
        # Load all characters
        self.characters = self._load_characters()
        self.character_ids = list(self.characters.keys())
        
        # Evaluation scenarios
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
        
        print(f"🔬 Sequential Ablation Evaluator Initialized")
        print(f"📊 Total Characters: {len(self.character_ids)}")
        print(f"📊 Evaluation Scenarios: {len(self.evaluation_scenarios)}")
        print(f"📊 Variations per Character: 10")
        print(f"📊 Total Evaluations: {len(self.character_ids)} × {len(self.evaluation_scenarios)} × 10 = {len(self.character_ids) * len(self.evaluation_scenarios) * 10:,}")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def run_single_character_evaluation(self, character_id: str, character_index: int, total_characters: int) -> Tuple[str, bool, str]:
        """Run evaluation for a single character across all scenarios."""
        print(f"\n{'='*80}")
        print(f"🚀 [{character_index}/{total_characters}] Starting evaluation for {character_id}")
        print(f"{'='*80}")
        
        try:
            # Run the parallel configs script for this character
            cmd = [
                "python", "scripts/run_parallel_configs.py",
                "--teacher-model", "claude-sonnet-4",
                "--student-model", "claude-sonnet-4", 
                "--character", character_id,
                "--iterations-per-variation", "1",
                "--num-variations", "10",  # 10 variations as requested
                "--num-workers", "4",
                "--max-concurrent", "8"
            ]
            
            print(f"📋 Command: {' '.join(cmd)}")
            print(f"⏱️  Starting at: {time.strftime('%H:%M:%S')}")
            
            # Run with live output
            result = subprocess.run(
                cmd,
                cwd=self.evaluation_dir,
                timeout=1800  # 30 minute timeout per character
            )
            
            if result.returncode == 0:
                print(f"✅ {character_id} evaluation completed successfully at {time.strftime('%H:%M:%S')}")
                return character_id, True, ""
            else:
                error_msg = f"Error in {character_id}: return code {result.returncode}"
                print(f"❌ {character_id} evaluation failed: {error_msg}")
                return character_id, False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout for {character_id}"
            print(f"⏰ {character_id} evaluation timed out")
            return character_id, False, error_msg
        except Exception as e:
            error_msg = f"Exception for {character_id}: {str(e)}"
            print(f"💥 {character_id} evaluation failed with exception: {error_msg}")
            return character_id, False, error_msg
    
    def run_sequential_ablation_evaluations(self) -> Dict[str, bool]:
        """Run evaluations for all characters sequentially."""
        print(f"\n🔄 Starting sequential ablation evaluations...")
        print(f"📊 Characters to evaluate: {len(self.character_ids)}")
        
        results = {}
        start_time = time.time()
        
        for i, character_id in enumerate(self.character_ids, 1):
            char_id, success, error = self.run_single_character_evaluation(character_id, i, len(self.character_ids))
            results[char_id] = success
            
            # Show progress
            elapsed = time.time() - start_time
            successful = sum(results.values())
            failed = len(results) - successful
            
            print(f"\n📈 Progress Summary:")
            print(f"  ✅ Successful: {successful}/{i}")
            print(f"  ❌ Failed: {failed}/{i}")
            print(f"  ⏱️  Elapsed: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
            
            if i < len(self.character_ids):
                estimated_remaining = (elapsed / i) * (len(self.character_ids) - i)
                print(f"  🔮 Estimated remaining: {estimated_remaining/60:.1f} minutes")
        
        total_time = time.time() - start_time
        successful = sum(results.values())
        failed = len(results) - successful
        
        print(f"\n🎉 Sequential ablation evaluations completed!")
        print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"✅ Successful: {successful}/{len(self.character_ids)} characters")
        print(f"❌ Failed: {failed}/{len(self.character_ids)} characters")
        
        if failed > 0:
            print(f"\n❌ Failed characters:")
            for char_id, success in results.items():
                if not success:
                    print(f"  • {char_id}")
        
        return results
    
    def run_complete_ablation_pipeline(self, max_retries: int = 3) -> None:
        """Run the complete ablation evaluation pipeline with automatic retry."""
        print("🧬 Sequential Trait Ablation Evaluation Pipeline")
        print("=" * 50)
        
        # Step 1: Run all character evaluations sequentially
        print("\n📊 Step 1: Running ablation evaluations...")
        results = self.run_sequential_ablation_evaluations()
        
        # Step 2: Retry failed evaluations
        failed_characters = [char for char, success in results.items() if not success]
        if failed_characters and max_retries > 0:
            print(f"\n🔄 Step 2: Retrying failed evaluations (up to {max_retries} times)...")
            self.retry_failed_evaluations(failed_characters, max_retries)
        
        # Step 3: Generate ablation analysis graphs
        print("\n📈 Step 3: Generating ablation analysis graphs...")
        try:
            # Create ablation-specific visualization
            self.create_ablation_analysis()
        except Exception as e:
            print(f"❌ Error creating ablation analysis: {e}")
        
        print("\n🎉 Ablation Evaluation Pipeline Complete!")
        print("📁 Results saved in results/transcripts/")
        
        # Show transcript viewer command
        print("\n🔍 To view results interactively:")
        print("npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f")
    
    def retry_failed_evaluations(self, failed_characters: List[str], max_retries: int) -> None:
        """Retry failed character evaluations with exponential backoff."""
        for retry_attempt in range(max_retries):
            print(f"\n🔄 Retry attempt {retry_attempt + 1}/{max_retries}")
            print(f"📊 Retrying {len(failed_characters)} failed characters")
            
            # Run failed characters again sequentially
            retry_results = {}
            for i, character in enumerate(failed_characters, 1):
                print(f"\n🔄 [{i}/{len(failed_characters)}] Retrying {character}...")
                char_id, success, error = self.run_single_character_evaluation(character, i, len(failed_characters))
                retry_results[character] = success
                if success:
                    print(f"✅ {character} succeeded on retry {retry_attempt + 1}")
                else:
                    print(f"❌ {character} failed again on retry {retry_attempt + 1}: {error}")
            
            # Update failed characters list
            failed_characters = [char for char, success in retry_results.items() if not success]
            
            if not failed_characters:
                print("🎉 All failed evaluations succeeded on retry!")
                break
            
            if retry_attempt < max_retries - 1:
                wait_time = 2 ** retry_attempt  # Exponential backoff
                print(f"⏳ Waiting {wait_time} seconds before next retry...")
                time.sleep(wait_time)
        
        if failed_characters:
            print(f"\n❌ {len(failed_characters)} characters still failed after {max_retries} retries:")
            for char in failed_characters:
                print(f"  • {char}")
        else:
            print(f"\n✅ All evaluations completed successfully!")
    
    def create_ablation_analysis(self) -> None:
        """Create ablation-specific analysis and visualizations."""
        print("📊 Creating ablation analysis...")
        
        # This would create specialized ablation analysis
        # For now, we'll use the existing graph creation
        try:
            result = subprocess.run(['python', 'create_graphs.py'], 
                                  capture_output=True, text=True, cwd=self.evaluation_dir)
            if result.returncode == 0:
                print("✅ Ablation graphs created successfully!")
                print(result.stdout)
            else:
                print("❌ Error creating ablation graphs:")
                print(result.stderr)
        except Exception as e:
            print(f"❌ Error running graph creation: {e}")

def main():
    evaluator = SequentialAblationEvaluator()
    evaluator.run_complete_ablation_pipeline()

if __name__ == "__main__":
    main()
