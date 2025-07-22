#!/usr/bin/env python3

import os
import subprocess
import time
from datetime import datetime


def check_monitor_status():
    """Check if the background monitor is running and show recent output."""
    
    print("🔍 BACKGROUND MONITOR STATUS")
    print("=" * 50)
    
    # Check if process is running
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        monitor_processes = [line for line in result.stdout.split('\n') 
                           if 'background_monitor.py' in line and 'grep' not in line]
        
        if monitor_processes:
            print("✅ Background monitor is running:")
            for process in monitor_processes:
                parts = process.split()
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                time_running = parts[9]
                print(f"   PID: {pid} | CPU: {cpu}% | Memory: {mem}% | Time: {time_running}")
        else:
            print("❌ Background monitor is not running")
            print("   Run: python background_monitor.py")
            return
            
    except Exception as e:
        print(f"❌ Error checking processes: {e}")
        return
    
    # Show recent output
    print(f"\n📋 RECENT OUTPUT:")
    print("-" * 30)
    
    if os.path.exists("monitor_output.log"):
        try:
            # Get last 10 lines of output
            result = subprocess.run(
                ["tail", "-10", "monitor_output.log"],
                capture_output=True,
                text=True
            )
            
            if result.stdout:
                print(result.stdout)
            else:
                print("No recent output")
                
        except Exception as e:
            print(f"❌ Error reading log: {e}")
    else:
        print("❌ No log file found")
    
    # Check if fine-tuning completed
    print(f"\n🎯 COMPLETION STATUS:")
    print("-" * 30)
    
    if os.path.exists("fine_tuning_completed.json"):
        import json
        try:
            with open("fine_tuning_completed.json", "r") as f:
                completion_info = json.load(f)
            
            print("🎉 FINE-TUNING COMPLETED!")
            print(f"   Model: {completion_info['fine_tuned_model']}")
            print(f"   Completed: {completion_info['completed_at']}")
            
            # Check if comparison was run
            if "comparison_results" in completion_info:
                print("✅ Comparison test completed")
            else:
                print("⏳ Comparison test may still be running")
                
        except Exception as e:
            print(f"❌ Error reading completion info: {e}")
    else:
        print("⏳ Fine-tuning still in progress...")
    
    # Show monitoring log
    print(f"\n📊 MONITORING LOG:")
    print("-" * 30)
    
    if os.path.exists("fine_tuning_monitor.log"):
        try:
            with open("fine_tuning_monitor.log", "r") as f:
                log_lines = f.readlines()
            
            if log_lines:
                print("Recent status changes:")
                for line in log_lines[-5:]:  # Last 5 status changes
                    print(f"   {line.strip()}")
            else:
                print("No status changes logged yet")
                
        except Exception as e:
            print(f"❌ Error reading monitoring log: {e}")
    else:
        print("No monitoring log found")
    
    print(f"\n💡 USEFUL COMMANDS:")
    print("-" * 30)
    print("   📊 Check this status: python monitor_status.py")
    print("   📋 View live output: tail -f monitor_output.log")
    print("   🛑 Stop monitor: pkill -f background_monitor.py")
    print("   ⚡ Quick status: python status_check.py")
    
    print(f"\n⏰ Last checked: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    check_monitor_status()