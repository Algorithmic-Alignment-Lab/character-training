#!/usr/bin/env python3
"""
Ultra-Fast Batch Evaluation Runner
Runs characters in optimized batches for maximum speed.
"""

import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
import sys

def run_character_batch(character_id):
    """Run a single character with maximum optimization."""
    cmd = [
        "python", "scripts/run_parallel_configs.py",
        "--teacher-model", "claude-sonnet-4",
        "--student-model", "claude-sonnet-4", 
        "--character", character_id,
        "--iterations-per-variation", "1",
        "--num-variations", "10",
        "--num-workers", "8",        # Maximum workers
        "--max-concurrent", "16"    # Maximum concurrent
    ]
    
    start_time = time.time()
    try:
        result = subprocess.run(cmd, timeout=900)  # 15 minute timeout
        elapsed = time.time() - start_time
        return character_id, result.returncode == 0, elapsed
    except subprocess.TimeoutExpired:
        return character_id, False, 900

def main():
    # All 33 characters
    characters = [
        "aura_guardian", "aura_problem_solver", "aura_creator", 
        "aura_guide", "aura_analyst", "helios_sage",
        "aura_guardian_no_honest", "aura_guardian_no_harmless", 
        "aura_guardian_no_empathetic", "aura_guardian_no_challenges_assumptions",
        "aura_problem_solver_no_helpful", "aura_problem_solver_no_honest", 
        "aura_problem_solver_no_harmless",
        "aura_creator_no_creative", "aura_creator_no_collaborative", 
        "aura_creator_no_empathetic", "aura_creator_no_helpful", 
        "aura_creator_no_curious", "aura_creator_no_harmless",
        "aura_guide_no_empathetic", "aura_guide_no_helpful", 
        "aura_guide_no_collaborative", "aura_guide_no_honest",
        "aura_analyst_no_curious", "aura_analyst_no_challenges_assumptions", 
        "aura_analyst_no_collaborative", "aura_analyst_no_creative", 
        "aura_analyst_no_honest",
        "helios_sage_no_curious", "helios_sage_no_challenges_assumptions", 
        "helios_sage_no_collaborative", "helios_sage_no_creative", 
        "helios_sage_no_honest"
    ]
    
    print(f"🚀 Ultra-Fast Batch Evaluation")
    print(f"📊 Characters: {len(characters)}")
    print(f"⚡ Max workers: 12")
    
    start_time = time.time()
    
    with ProcessPoolExecutor(max_workers=12) as executor:
        futures = [executor.submit(run_character_batch, char) for char in characters]
        
        completed = 0
        for future in futures:
            char_id, success, elapsed = future.result()
            completed += 1
            
            status = "✅" if success else "❌"
            print(f"{status} [{completed}/{len(characters)}] {char_id} ({elapsed/60:.1f}m)")
            
            # Estimate remaining time
            if completed > 0:
                avg_time = (time.time() - start_time) / completed
                remaining = (len(characters) - completed) * avg_time
                print(f"🔮 Estimated remaining: {remaining/60:.1f} minutes")
    
    total_time = time.time() - start_time
    print(f"\n🎉 Batch evaluation complete in {total_time/60:.1f} minutes!")

if __name__ == "__main__":
    main()
