#!/usr/bin/env python3

import os
import json
import time
import subprocess
from datetime import datetime
import together
from tqdm import tqdm


def background_monitor():
    """Monitor fine-tuning job in background and run comparison when ready."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    # Load job info
    try:
        with open("fine_tuning_job_info.json", "r") as f:
            job_info = json.load(f)
        job_id = job_info["job_id"]
    except FileNotFoundError:
        job_id = "ft-b3cb7680-14cb"  # Fallback
    
    print(f"🚀 Background monitoring started for job: {job_id}")
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️  Will check every 2 minutes...")
    print("-" * 50)
    
    last_status = None
    check_count = 0
    
    # Create progress bar
    pbar = tqdm(
        desc="Fine-tuning Progress",
        unit="checks",
        bar_format="{desc}: {n} checks | {elapsed} | {postfix}",
        dynamic_ncols=True
    )
    
    try:
        while True:
            try:
                check_count += 1
                job = client.fine_tuning.retrieve(id=job_id)
                status = str(job.status)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Update progress bar
                pbar.update(1)
                
                # Create status message for progress bar
                status_msg = status.replace("FinetuneJobStatus.STATUS_", "").lower()
                pbar.set_postfix_str(f"Status: {status_msg}")
                
                # Only print if status changed
                if status != last_status:
                    pbar.write(f"[{timestamp}] Status changed: {status}")
                    last_status = status
                    
                    # Log status change
                    with open("fine_tuning_monitor.log", "a") as f:
                        f.write(f"{datetime.now().isoformat()} - {status}\n")
                else:
                    # Print periodic updates
                    if check_count % 5 == 0:  # Every 10 minutes
                        pbar.write(f"[{timestamp}] Still {status} (check #{check_count})")
            
                # Check if completed
                if "completed" in status.lower() or "succeeded" in status.lower():
                    fine_tuned_model = getattr(job, 'fine_tuned_model', None)
                    if fine_tuned_model:
                        pbar.write(f"\n🎉 Fine-tuning completed at {timestamp}!")
                        pbar.write(f"📦 Model: {fine_tuned_model}")
                        
                        # Save completion info
                        completion_info = {
                            "job_id": job_id,
                            "fine_tuned_model": fine_tuned_model,
                            "completed_at": datetime.now().isoformat(),
                            "status": status
                        }
                        
                        with open("fine_tuning_completed.json", "w") as f:
                            json.dump(completion_info, f, indent=2)
                        
                        pbar.write(f"💾 Completion info saved to fine_tuning_completed.json")
                        
                        # Run comparison automatically
                        pbar.write(f"🧪 Running comparison test...")
                        try:
                            result = subprocess.run(
                                ["python", "quick_comparison.py"],
                                capture_output=True,
                                text=True,
                                timeout=300  # 5 minute timeout
                            )
                            
                            if result.returncode == 0:
                                pbar.write("✅ Comparison test completed successfully!")
                                pbar.write("📊 Results:")
                                pbar.write(result.stdout)
                            else:
                                pbar.write(f"❌ Comparison test failed:")
                                pbar.write(result.stderr)
                        
                        except subprocess.TimeoutExpired:
                            pbar.write("⏱️  Comparison test timed out")
                        except Exception as e:
                            pbar.write(f"❌ Error running comparison: {e}")
                        
                        pbar.write(f"\n🏁 Monitoring complete!")
                        break
                    else:
                        pbar.write(f"⚠️  Job completed but no fine-tuned model found")
                        break
                
                elif "failed" in status.lower() or "error" in status.lower():
                    pbar.write(f"❌ Fine-tuning failed at {timestamp}!")
                    break
                
                elif "cancelled" in status.lower() or "canceled" in status.lower():
                    pbar.write(f"🛑 Fine-tuning cancelled at {timestamp}")
                    break
                
                # Wait before next check with progress bar countdown
                for i in tqdm(range(120), desc="Next check in", unit="s", leave=False):
                    time.sleep(1)
            
            except KeyboardInterrupt:
                pbar.write(f"\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                pbar.write(f"❌ Error checking status: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    finally:
        pbar.close()


if __name__ == "__main__":
    background_monitor()