#!/usr/bin/env python3
"""
Simple script to run missing re-evaluations
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Run missing re-evaluations for timestamp 20251021-172456"""
    
    # Set the target timestamp
    target_timestamp = "20251021-172456"
    
    print(f"🚀 Running Missing Re-evaluations for Timestamp: {target_timestamp}")
    print("=" * 60)
    
    # Change to evaluation directory
    evaluation_dir = Path(__file__).parent
    
    # Run the missing re-evaluation script
    cmd = [
        "python", "run_missing_reeval.py",
        "--timestamp", target_timestamp,
        "--evaluation-dir", str(evaluation_dir)
    ]
    
    print(f"📋 Command: {' '.join(cmd)}")
    print(f"📁 Working directory: {evaluation_dir}")
    print("")
    
    try:
        # Run the command
        result = subprocess.run(cmd, cwd=evaluation_dir, check=True)
        print("✅ Missing re-evaluations completed successfully!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running missing re-evaluations: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
