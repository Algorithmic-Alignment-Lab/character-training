#!/usr/bin/env python3

import os
import json
from datetime import datetime
import together


def simple_dashboard():
    """Simple, readable training dashboard."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    # Load job ID
    try:
        with open("fine_tuning_job_info.json", "r") as f:
            job_info = json.load(f)
        job_id = job_info["job_id"]
    except FileNotFoundError:
        job_id = "ft-b3cb7680-14cb"
    
    print("TOGETHER AI FINE-TUNING STATUS")
    print("=" * 50)
    
    try:
        # Get job details
        job = client.fine_tuning.retrieve(id=job_id)
        
        # Basic info
        print(f"Job ID: {job_id}")
        print(f"Status: {str(job.status).replace('FinetuneJobStatus.STATUS_', '').lower()}")
        print(f"Model: {job.model}")
        print(f"Created: {job.created_at}")
        print(f"Updated: {job.updated_at}")
        
        # Calculate duration
        if job.created_at:
            created_time = datetime.fromisoformat(job.created_at.replace('Z', '+00:00'))
            now = datetime.now(created_time.tzinfo)
            duration = now - created_time
            print(f"Duration: {str(duration).split('.')[0]}")
        
        # Progress estimation
        status = str(job.status).lower()
        if "uploading" in status:
            progress = 10
            stage = "Uploading training data"
        elif "queued" in status:
            progress = 20
            stage = "Queued for training"
        elif "running" in status:
            progress = 60
            stage = "Training in progress"
        elif "validating" in status:
            progress = 90
            stage = "Validating results"
        elif "completed" in status:
            progress = 100
            stage = "Training completed"
        else:
            progress = 0
            stage = f"{status}"
        
        print(f"Progress: {progress}%")
        print(f"Stage: {stage}")
        
        # Progress bar
        bar_length = 30
        filled_length = int(bar_length * progress // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"[{bar}] {progress}%")
        
        # Get fine-tuned model if available
        fine_tuned_model = getattr(job, 'fine_tuned_model', None)
        if fine_tuned_model:
            print(f"Fine-tuned Model: {fine_tuned_model}")
        
        # Training parameters
        print(f"\nTRAINING PARAMETERS:")
        print(f"   Method: LoRA (Low-Rank Adaptation)")
        print(f"   Epochs: 3")
        print(f"   Learning Rate: 1e-5")
        print(f"   Training Examples: 10")
        print(f"   Training File: {job.training_file}")
        
        # Monitor status
        print(f"\nMONITORING STATUS:")
        import subprocess
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if 'background_monitor.py' in result.stdout:
                print("   Background monitor running")
            else:
                print("   Background monitor not running")
                print("   Start with: python background_monitor.py")
        except:
            print("   Could not check monitor status")
        
        # What's happening now
        print(f"\nCURRENT STATUS:")
        if "uploading" in status:
            print("   Training data is being uploaded to Together AI servers")
            print("   This usually takes 1-5 minutes")
            print("   Once complete, training will start automatically")
        elif "queued" in status:
            print("   Job is waiting for available GPU resources")
            print("   Training will start when resources are free")
        elif "running" in status:
            print("   Model is being fine-tuned with your data")
            print("   This typically takes 10-30 minutes")
        elif "completed" in status:
            print("   Fine-tuning completed successfully!")
            if fine_tuned_model:
                print(f"   Model: {fine_tuned_model}")
        
        # Next steps
        print(f"\nNEXT STEPS:")
        if progress < 100:
            print("   Wait for training to complete")
            print("   Monitor will automatically run comparison test")
            print("   Check status: python simple_dashboard.py")
        else:
            print("   Run comparison test: python quick_comparison.py")
            print("   View results in generated files")
        
        # Verification that monitoring is working
        print(f"\nMONITORING VERIFICATION:")
        if os.path.exists("fine_tuning_monitor.log"):
            with open("fine_tuning_monitor.log", "r") as f:
                lines = f.readlines()
            if lines:
                last_update = lines[-1].strip()
                print(f"   Last status update: {last_update}")
            else:
                print("   No status updates logged yet")
        
        if os.path.exists("monitor_output.log"):
            print("   Monitor output file exists")
        else:
            print("   No monitor output file found")
        
        # Live monitoring commands
        print(f"\nUSEFUL COMMANDS:")
        print("   python simple_dashboard.py")
        print("   python monitor_status.py")
        print("   tail -f monitor_output.log")
        if fine_tuned_model:
            print("   python quick_comparison.py")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print(f"\nUpdated: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)


if __name__ == "__main__":
    simple_dashboard()