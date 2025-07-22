#!/usr/bin/env python3

import os
import json
from datetime import datetime
import together


def status_check():
    """Simple status check for fine-tuning job."""
    
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
        print(f"📋 Job ID: {job_id}")
    except FileNotFoundError:
        job_id = "ft-b3cb7680-14cb"  # Fallback
        print(f"📋 Job ID: {job_id} (fallback)")
    
    try:
        job = client.fine_tuning.retrieve(id=job_id)
        status = str(job.status)
        
        print(f"📊 Status: {status}")
        print(f"🤖 Base Model: {job.model}")
        print(f"⏰ Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if hasattr(job, 'created_at'):
            print(f"📅 Created: {job.created_at}")
        
        if hasattr(job, 'fine_tuned_model') and job.fine_tuned_model:
            print(f"🎯 Fine-tuned Model: {job.fine_tuned_model}")
            print(f"✅ Ready for testing!")
            
            # Check if we have completion info
            if os.path.exists("fine_tuning_completed.json"):
                with open("fine_tuning_completed.json", "r") as f:
                    completion_info = json.load(f)
                print(f"🏁 Completed at: {completion_info['completed_at']}")
        
        elif "completed" in status.lower() or "succeeded" in status.lower():
            print(f"✅ Job completed but model info not available")
        
        elif "failed" in status.lower() or "error" in status.lower():
            print(f"❌ Job failed")
        
        elif "cancelled" in status.lower() or "canceled" in status.lower():
            print(f"🛑 Job was cancelled")
        
        else:
            print(f"⏳ Job is still in progress...")
            
            # Show progress indicators
            status_lower = status.lower()
            if "queued" in status_lower:
                print("   📋 Currently queued for processing")
            elif "uploading" in status_lower:
                print("   📤 Uploading training data")
            elif "running" in status_lower:
                print("   🏃 Training in progress")
            elif "validating" in status_lower:
                print("   🔍 Validating results")
            
            print("\n💡 Commands to run:")
            print("   • Check status: python status_check.py")
            print("   • Monitor in background: python background_monitor.py")
            print("   • Quick test when ready: python quick_comparison.py")
        
    except Exception as e:
        print(f"❌ Error checking status: {e}")


if __name__ == "__main__":
    status_check()