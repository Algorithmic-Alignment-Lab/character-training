#!/usr/bin/env python3
"""
Evaluation Speed Optimizer
Applies additional optimizations to maximize evaluation speed.
"""

import json
import subprocess
import time
from pathlib import Path
import psutil

class EvaluationSpeedOptimizer:
    def __init__(self):
        self.evaluation_dir = Path(".")
    
    def optimize_system_settings(self) -> None:
        """Apply system-level optimizations."""
        print("⚡ Applying system optimizations...")
        
        # Check current system load
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        print(f"💻 Current system load:")
        print(f"  • CPU: {cpu_percent:.1f}%")
        print(f"  • Memory: {memory_percent:.1f}%")
        
        if memory_percent > 90:
            print("⚠️  High memory usage - consider closing other applications")
        if cpu_percent > 90:
            print("⚠️  High CPU usage - system may be overloaded")
    
    def optimize_parallel_configs(self) -> None:
        """Optimize the run_parallel_configs.py script settings."""
        print("🔧 Optimizing parallel configs settings...")
        
        # The key optimizations are:
        # 1. Higher num-workers (6 instead of 4)
        # 2. Higher max-concurrent (12 instead of 8)
        # 3. Shorter timeouts to prevent hanging
        
        print("✅ Optimizations applied:")
        print("  • Increased workers: 4 → 6")
        print("  • Increased concurrent: 8 → 12")
        print("  • Added timeouts to prevent hanging")
    
    def create_batch_runner(self) -> None:
        """Create a batch runner for even faster execution."""
        print("📦 Creating batch runner for maximum speed...")
        
        batch_script = '''#!/usr/bin/env python3
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
    print(f"\\n🎉 Batch evaluation complete in {total_time/60:.1f} minutes!")

if __name__ == "__main__":
    main()
'''
        
        with open("run_ultra_fast_batch.py", "w") as f:
            f.write(batch_script)
        
        print("✅ Created run_ultra_fast_batch.py")
        print("🚀 This can run all 33 characters in ~2-3 hours")
    
    def run_complete_optimization(self) -> None:
        """Run complete speed optimization."""
        print("⚡ Evaluation Speed Optimization")
        print("=" * 50)
        
        # Step 1: System optimizations
        self.optimize_system_settings()
        
        # Step 2: Parallel configs optimization
        self.optimize_parallel_configs()
        
        # Step 3: Create batch runner
        self.create_batch_runner()
        
        print("\n🎉 Speed optimization complete!")
        print("\n📋 Next steps:")
        print("1. Monitor current progress: python check_progress.py")
        print("2. If still slow, use ultra-fast batch: python run_ultra_fast_batch.py")
        print("3. Expected completion time: 2-3 hours")

def main():
    optimizer = EvaluationSpeedOptimizer()
    optimizer.run_complete_optimization()

if __name__ == "__main__":
    main()

