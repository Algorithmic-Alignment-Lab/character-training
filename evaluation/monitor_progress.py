#!/usr/bin/env python3
"""
Progress Monitor
Real-time monitoring of evaluation progress.
"""

import time
import os
from pathlib import Path

def monitor_progress():
    """Monitor progress in real-time."""
    progress_file = Path("progress.txt")
    
    print("📊 Real-time Progress Monitor")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring")
    print()
    
    try:
        while True:
            if progress_file.exists():
                with open(progress_file, 'r') as f:
                    content = f.read()
                print("\033[2J\033[H")  # Clear screen
                print("📊 Real-time Progress Monitor")
                print("=" * 50)
                print(content)
            else:
                print("⏳ Waiting for progress file...")
            
            time.sleep(10)  # Update every 10 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    monitor_progress()

