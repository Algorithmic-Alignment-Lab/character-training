#!/usr/bin/env python3
"""
Parallel Trait Ablation Evaluation Runner
Runs evaluations for all 36 characters (6 base + 27 ablations + 3 original) with 10 variations each.
"""

import json
import subprocess
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Tuple
import sys

class AblationEvaluator:
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
        
        print(f"🔬 Ablation Evaluator Initialized")
        print(f"📊 Total Characters: {len(self.character_ids)}")
        print(f"📊 Evaluation Scenarios: {len(self.evaluation_scenarios)}")
        print(f"📊 Variations per Character: 10")
        print(f"📊 Total Evaluations: {len(self.character_ids)} × {len(self.evaluation_scenarios)} × 10 = {len(self.character_ids) * len(self.evaluation_scenarios) * 10:,}")
    
    def _load_characters(self) -> Dict:
        """Load all characters from characters.json"""
        characters_file = Path("../character_definition/characters.json")
        with open(characters_file, 'r') as f:
            return json.load(f)
    
    def run_single_character_evaluation(self, character_id: str) -> Tuple[str, bool, str]:
        """Run evaluation for a single character across all scenarios."""
        print(f"\n🚀 Starting evaluation for {character_id}...")
        
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
            
            result = subprocess.run(
                cmd,
                cwd=self.evaluation_dir,
                capture_output=True,
                text=True,
                timeout=1800  # 30 minute timeout per character
            )
            
            if result.returncode == 0:
                print(f"✅ {character_id} evaluation completed successfully")
                return character_id, True, ""
            else:
                error_msg = f"Error in {character_id}: {result.stderr}"
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
    
    def run_parallel_ablation_evaluations(self, max_workers: int = 6) -> Dict[str, bool]:
        """Run evaluations for all characters in parallel."""
        print(f"\n🔄 Starting parallel ablation evaluations...")
        print(f"⚡ Max workers: {max_workers}")
        print(f"📊 Characters to evaluate: {len(self.character_ids)}")
        
        results = {}
        start_time = time.time()
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
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
                    
                    elapsed = time.time() - start_time
                    print(f"📈 Progress: {completed}/{len(self.character_ids)} characters completed ({elapsed:.1f}s elapsed)")
                    
                    if not success:
                        print(f"❌ Failed: {char_id} - {error}")
                        
                except Exception as e:
                    print(f"💥 Exception processing {char_id}: {e}")
                    results[char_id] = False
                    completed += 1
        
        total_time = time.time() - start_time
        successful = sum(results.values())
        failed = len(results) - successful
        
        print(f"\n🎉 Parallel ablation evaluations completed!")
        print(f"⏱️  Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
        print(f"✅ Successful: {successful}/{len(self.character_ids)} characters")
        print(f"❌ Failed: {failed}/{len(self.character_ids)} characters")
        
        if failed > 0:
            print(f"\n❌ Failed characters:")
            for char_id, success in results.items():
                if not success:
                    print(f"  • {char_id}")
        
        return results
    
    def run_complete_ablation_pipeline(self, max_workers: int = 6) -> None:
        """Run the complete ablation evaluation pipeline."""
        print("🧬 Trait Ablation Evaluation Pipeline")
        print("=" * 50)
        
        # Step 1: Run all character evaluations in parallel
        print("\n📊 Step 1: Running ablation evaluations...")
        results = self.run_parallel_ablation_evaluations(max_workers)
        
        # Step 2: Generate ablation analysis graphs
        print("\n📈 Step 2: Generating ablation analysis graphs...")
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
    evaluator = AblationEvaluator()
    evaluator.run_complete_ablation_pipeline(max_workers=6)

if __name__ == "__main__":
    main()
