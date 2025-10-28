#!/usr/bin/env python3
"""
Test script for re-evaluation using the modified run_ablation_evaluations_simple_parallel.py
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Test re-evaluation for timestamp 20251021-172456"""
    
    print(f"🧪 Testing Re-evaluation for Timestamp: 20251021-172456")
    print("=" * 60)
    
    # Change to evaluation directory
    evaluation_dir = Path(__file__).parent
    
    # Run the modified ablation evaluation script
    cmd = [
        "python", "run_ablation_evaluations_simple_parallel.py"
    ]
    
    print(f"📋 Command: {' '.join(cmd)}")
    print(f"📁 Working directory: {evaluation_dir}")
    print("")
    print("🔧 Configuration:")
    print("  • COPY_FROM_EXISTING = False")
    print("  • SOURCE_RUN_TIMESTAMP = '20251021-172456'")
    print("  • EVALUATED_MODEL = 'claude-sonnet-4'")
    print("  • TEACHER_MODEL = 'claude-sonnet-4'")
    print("")
    
    try:
        # Run the command
        result = subprocess.run(cmd, cwd=evaluation_dir, check=True)
        print("✅ Re-evaluation completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running re-evaluation: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
