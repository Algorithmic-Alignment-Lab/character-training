#!/usr/bin/env python3
"""
Restart Evaluations Script
Kills stuck processes and restarts with optimized settings.
"""

import subprocess
import psutil
import time
import signal
import os
from pathlib import Path

class EvaluationRestarter:
    def __init__(self):
        self.evaluation_dir = Path(".")
    
    def kill_stuck_processes(self) -> int:
        """Kill stuck evaluation processes."""
        print("🔄 Killing stuck evaluation processes...")
        
        killed_count = 0
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
                if any(keyword in cmdline for keyword in ['run_parallel_configs.py', 'bloom_eval.py', 'run_ablation_evaluations.py']):
                    print(f"🔪 Killing PID {proc.info['pid']}: {proc.info['name']}")
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if killed_count > 0:
            print(f"✅ Killed {killed_count} stuck processes")
            time.sleep(2)  # Wait for processes to fully terminate
        else:
            print("ℹ️  No stuck processes found")
        
        return killed_count
    
    def check_system_resources(self) -> dict:
        """Check if system can handle more parallelism."""
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / 1024 / 1024 / 1024
        
        print(f"💻 System specs:")
        print(f"  • CPU cores: {cpu_count}")
        print(f"  • Memory: {memory_gb:.1f}GB")
        
        # Recommend optimal settings
        if cpu_count >= 8 and memory_gb >= 16:
            recommended_workers = 8
            recommended_concurrent = 12
        elif cpu_count >= 4 and memory_gb >= 8:
            recommended_workers = 4
            recommended_concurrent = 8
        else:
            recommended_workers = 2
            recommended_concurrent = 4
        
        return {
            'workers': recommended_workers,
            'concurrent': recommended_concurrent,
            'cpu_count': cpu_count,
            'memory_gb': memory_gb
        }
    
    def restart_with_optimized_settings(self) -> None:
        """Restart evaluations with optimized settings."""
        print("🚀 Restarting evaluations with optimized settings...")
        
        # Get optimal settings
        settings = self.check_system_resources()
        
        print(f"⚙️  Recommended settings:")
        print(f"  • Workers: {settings['workers']}")
        print(f"  • Max concurrent: {settings['concurrent']}")
        
        # Create optimized command
        cmd = [
            "python", "run_ablation_evaluations.py"
        ]
        
        print(f"📋 Running: {' '.join(cmd)}")
        print("💡 This will use the optimized settings in the script")
        
        # Run in background
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            print(f"✅ Started evaluation process (PID: {process.pid})")
            print("📊 Monitor progress with: python check_progress.py")
            
        except Exception as e:
            print(f"❌ Failed to restart: {e}")
    
    def run_complete_restart(self) -> None:
        """Complete restart process."""
        print("🔄 Complete Evaluation Restart")
        print("=" * 50)
        
        # Step 1: Kill stuck processes
        killed = self.kill_stuck_processes()
        
        # Step 2: Check system resources
        print("\n💻 Checking system resources...")
        settings = self.check_system_resources()
        
        # Step 3: Restart with optimized settings
        print("\n🚀 Restarting with optimized settings...")
        self.restart_with_optimized_settings()
        
        print("\n✅ Restart complete!")
        print("📊 Monitor progress with: python check_progress.py")

def main():
    restarter = EvaluationRestarter()
    restarter.run_complete_restart()

if __name__ == "__main__":
    main()

