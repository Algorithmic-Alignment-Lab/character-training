#!/usr/bin/env python3
"""
Debug script to understand the folder structure
"""

from pathlib import Path

def debug_folder_structure():
    """Debug the current folder structure"""
    print("🔍 Debugging Folder Structure")
    print("=" * 50)
    
    results_dir = Path("results/transcripts")
    
    if not results_dir.exists():
        print("❌ Results directory not found")
        return
    
    print(f"📁 Results directory: {results_dir}")
    print()
    
    # List all evaluation directories
    evaluation_dirs = [d for d in results_dir.iterdir() if d.is_dir()]
    print(f"📊 Found {len(evaluation_dirs)} evaluation directories:")
    
    for eval_dir in evaluation_dirs:
        print(f"  📁 {eval_dir.name}")
        
        # List all timestamp directories in this evaluation
        timestamp_dirs = [d for d in eval_dir.iterdir() if d.is_dir()]
        print(f"    📅 {len(timestamp_dirs)} timestamp directories:")
        
        for timestamp_dir in timestamp_dirs:
            print(f"      📅 {timestamp_dir.name}")
            
            # List files in this timestamp directory
            files = [f for f in timestamp_dir.iterdir() if f.is_file()]
            print(f"        📄 {len(files)} files:")
            for file in files:
                print(f"          📄 {file.name}")

if __name__ == "__main__":
    debug_folder_structure()
