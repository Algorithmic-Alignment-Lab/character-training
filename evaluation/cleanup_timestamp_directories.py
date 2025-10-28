#!/usr/bin/env python3
"""
Clean up timestamp directories to keep only {character_name}_{timestamp} format
Remove directories that are just {timestamp} format
"""

import shutil
from pathlib import Path
import re

def cleanup_timestamp_directories():
    """Remove directories that are just timestamp format, keep only character_timestamp format"""
    
    transcripts_dir = Path("results/transcripts")
    target_timestamp = "20251021-172456"
    
    print(f"🧹 Cleaning up timestamp directories for: {target_timestamp}")
    print("=" * 60)
    
    # Pattern to match directories that are just timestamp (not character_timestamp)
    timestamp_only_pattern = re.compile(rf"^{target_timestamp}$")
    
    total_removed = 0
    total_kept = 0
    
    for eval_dir in transcripts_dir.iterdir():
        if not eval_dir.is_dir():
            continue
            
        print(f"\n📁 Processing evaluation: {eval_dir.name}")
        
        # Find all directories in this evaluation
        dirs_to_remove = []
        dirs_to_keep = []
        
        for timestamp_dir in eval_dir.iterdir():
            if not timestamp_dir.is_dir():
                continue
                
            dir_name = timestamp_dir.name
            
            # Check if it's just the timestamp (should be removed)
            if timestamp_only_pattern.match(dir_name):
                dirs_to_remove.append(timestamp_dir)
                print(f"  🗑️  Marked for removal: {dir_name}")
            else:
                dirs_to_keep.append(timestamp_dir)
                print(f"  ✅ Keeping: {dir_name}")
        
        # Remove the timestamp-only directories
        for dir_to_remove in dirs_to_remove:
            try:
                print(f"  🗑️  Removing: {dir_to_remove}")
                shutil.rmtree(dir_to_remove)
                total_removed += 1
            except Exception as e:
                print(f"  ❌ Error removing {dir_to_remove}: {e}")
        
        total_kept += len(dirs_to_keep)
        print(f"  📊 Removed: {len(dirs_to_remove)}, Kept: {len(dirs_to_keep)}")
    
    print(f"\n🎉 Cleanup Complete!")
    print(f"📊 Total directories removed: {total_removed}")
    print(f"📊 Total directories kept: {total_kept}")
    print(f"✅ Only {character_name}_{timestamp} format directories remain")

if __name__ == "__main__":
    cleanup_timestamp_directories()
