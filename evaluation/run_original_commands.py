#!/usr/bin/env python3
"""
Run the original character science commands as requested
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and report results"""
    print(f"\n🚀 Running: {description}")
    print(f"Command: {command}")
    print("-" * 50)
    
    try:
        result = subprocess.run(command, shell=True, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"💥 ERROR: {e}")
        return False

def main():
    """Run the original commands"""
    print("🔬 Running Original Character Science Commands")
    print("=" * 60)
    
    # Change to the evaluation directory
    import os
    os.chdir(Path(__file__).parent)
    
    # Command 1: Claude analysis
    print("\n1️⃣ Running Claude Analysis (20251021-172456)")
    claude_success = run_command(
        "python test_timestamp_graphing.py 20251021-172456",
        "Claude Model Analysis"
    )
    
    # Command 2: GPT analysis
    print("\n2️⃣ Running GPT Analysis (20251022-000125)")
    gpt_success = run_command(
        "python test_timestamp_graphing.py 20251022-000125", 
        "GPT Model Analysis"
    )
    
    # Check if files were created
    print("\n3️⃣ Checking Output Files")
    output_files = [
        "character_science_main_grouped_bars.png",
        "character_science_character_summary.png", 
        "character_science_anomaly_heatmap.png",
        "character_science_consistency_chart.png"
    ]
    
    files_created = []
    for file in output_files:
        if Path(file).exists():
            files_created.append(file)
            print(f"✅ {file}")
        else:
            print(f"❌ {file}")
    
    # Summary
    print(f"\n📊 Results Summary:")
    print(f"Claude Analysis: {'✅ SUCCESS' if claude_success else '❌ FAILED'}")
    print(f"GPT Analysis: {'✅ SUCCESS' if gpt_success else '❌ FAILED'}")
    print(f"Files Created: {len(files_created)}/{len(output_files)}")
    
    if claude_success and gpt_success and len(files_created) > 0:
        print(f"\n🎯 Character Science Analysis Complete!")
        print(f"📁 Check the generated PNG files for visualizations")
        print(f"📊 Both Claude and GPT analyses completed successfully")
    else:
        print(f"\n⚠️  Some issues occurred. Check the output above.")
    
    return claude_success and gpt_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
