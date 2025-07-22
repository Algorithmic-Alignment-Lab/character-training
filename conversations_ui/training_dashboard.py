#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime, timedelta
import together
from typing import Dict, Any, List


class TrainingDashboard:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = together.Together(api_key=api_key)
        self.job_id = self.load_job_id()
    
    def load_job_id(self) -> str:
        """Load job ID from file."""
        try:
            with open("fine_tuning_job_info.json", "r") as f:
                job_info = json.load(f)
            return job_info["job_id"]
        except FileNotFoundError:
            return "ft-b3cb7680-14cb"  # Fallback
    
    def get_detailed_job_info(self) -> Dict[str, Any]:
        """Get comprehensive job information."""
        try:
            job = self.client.fine_tuning.retrieve(id=self.job_id)
            
            # Convert to dict for easier access
            try:
                job_dict = job.model_dump() if hasattr(job, 'model_dump') else job.__dict__
            except:
                job_dict = {}
            
            return {
                "job_id": self.job_id,
                "status": str(job.status) if hasattr(job, 'status') else "Unknown",
                "model": getattr(job, 'model', 'Unknown'),
                "created_at": getattr(job, 'created_at', None),
                "updated_at": getattr(job, 'updated_at', None),
                "finished_at": getattr(job, 'finished_at', None),
                "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
                "training_file": getattr(job, 'training_file', None),
                "validation_file": getattr(job, 'validation_file', None),
                "hyperparameters": getattr(job, 'hyperparameters', {}),
                "error": getattr(job, 'error', None),
                "estimated_finish": getattr(job, 'estimated_finish', None),
                "progress": getattr(job, 'progress', None),
                "raw_data": job_dict
            }
        except Exception as e:
            return {"error": str(e)}
    
    def get_training_events(self) -> List[Dict[str, Any]]:
        """Get training events/logs if available."""
        try:
            events = self.client.fine_tuning.list_events(id=self.job_id)
            return [event.model_dump() if hasattr(event, 'model_dump') else event.__dict__ for event in events.data]
        except Exception as e:
            return [{"error": f"Could not retrieve events: {e}"}]
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all fine-tuning jobs for context."""
        try:
            jobs = self.client.fine_tuning.list()
            return [job.model_dump() if hasattr(job, 'model_dump') else job.__dict__ for job in jobs.data[:5]]
        except Exception as e:
            return [{"error": f"Could not retrieve jobs: {e}"}]
    
    def calculate_training_metrics(self, job_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate training metrics and progress."""
        metrics = {
            "duration_so_far": "Unknown",
            "estimated_total_duration": "Unknown",
            "progress_percentage": 0,
            "training_speed": "Unknown",
            "cost_estimate": "Unknown"
        }
        
        if job_info.get("created_at"):
            try:
                created_time = datetime.fromisoformat(job_info["created_at"].replace('Z', '+00:00'))
                now = datetime.now(created_time.tzinfo)
                duration = now - created_time
                metrics["duration_so_far"] = str(duration).split('.')[0]
                
                # Estimate progress based on status
                status = job_info["status"].lower()
                if "uploading" in status:
                    metrics["progress_percentage"] = 5
                elif "queued" in status:
                    metrics["progress_percentage"] = 10
                elif "running" in status:
                    metrics["progress_percentage"] = 50
                elif "validating" in status:
                    metrics["progress_percentage"] = 90
                elif "completed" in status:
                    metrics["progress_percentage"] = 100
                
            except Exception as e:
                metrics["error"] = str(e)
        
        return metrics
    
    def display_dashboard(self):
        """Display comprehensive training dashboard."""
        print("="*80)
        print("🚀 TOGETHER AI FINE-TUNING DASHBOARD")
        print("="*80)
        
        # Get job information
        job_info = self.get_detailed_job_info()
        
        if "error" in job_info:
            print(f"❌ Error retrieving job info: {job_info['error']}")
            return
        
        # Basic job information
        print(f"\n📋 JOB INFORMATION:")
        print(f"   Job ID: {job_info['job_id']}")
        print(f"   Status: {job_info['status']}")
        print(f"   Base Model: {job_info['model']}")
        print(f"   Created: {job_info['created_at']}")
        
        if job_info.get('fine_tuned_model'):
            print(f"   Fine-tuned Model: {job_info['fine_tuned_model']}")
        
        # Training parameters
        print(f"\n⚙️  TRAINING PARAMETERS:")
        hyperparams = job_info.get('hyperparameters', {})
        
        if hyperparams:
            for key, value in hyperparams.items():
                print(f"   {key}: {value}")
        else:
            print("   Using default hyperparameters:")
            print("   • LoRA: True")
            print("   • Epochs: 3")
            print("   • Learning Rate: 1e-5")
            print("   • Train on Inputs: False")
        
        # Training files
        print(f"\n📁 TRAINING DATA:")
        print(f"   Training File: {job_info.get('training_file', 'N/A')}")
        print(f"   Validation File: {job_info.get('validation_file', 'None')}")
        
        # Load local training data info
        if os.path.exists("fine_tuning_data.jsonl"):
            with open("fine_tuning_data.jsonl", "r") as f:
                lines = f.readlines()
            print(f"   Local Examples: {len(lines)}")
            print(f"   File Size: {os.path.getsize('fine_tuning_data.jsonl')} bytes")
        
        # Progress and metrics
        metrics = self.calculate_training_metrics(job_info)
        print(f"\n📊 TRAINING METRICS:")
        print(f"   Duration So Far: {metrics['duration_so_far']}")
        print(f"   Progress: {metrics['progress_percentage']}%")
        print(f"   Estimated Total: {metrics['estimated_total_duration']}")
        
        # Progress bar
        progress = metrics['progress_percentage']
        bar_length = 40
        filled_length = int(bar_length * progress // 100)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        print(f"   Progress Bar: [{bar}] {progress}%")
        
        # Status timeline
        print(f"\n📅 STATUS TIMELINE:")
        
        # Check monitoring log
        if os.path.exists("fine_tuning_monitor.log"):
            with open("fine_tuning_monitor.log", "r") as f:
                log_lines = f.readlines()
            
            if log_lines:
                print("   Recent status changes:")
                for line in log_lines[-10:]:
                    timestamp, status = line.strip().split(" - ")
                    clean_status = status.replace("FinetuneJobStatus.STATUS_", "").lower()
                    print(f"   • {timestamp.split('T')[1][:8]} - {clean_status}")
            else:
                print("   No status changes logged yet")
        
        # Training events
        print(f"\n📝 TRAINING EVENTS:")
        events = self.get_training_events()
        
        if events and not events[0].get("error"):
            print("   Recent training events:")
            for event in events[:5]:
                event_time = event.get('created_at', 'Unknown')
                event_type = event.get('level', 'info')
                event_msg = event.get('message', 'No message')
                print(f"   • [{event_type}] {event_time}: {event_msg}")
        else:
            print("   No training events available yet")
        
        # Error information
        if job_info.get('error'):
            print(f"\n❌ ERROR DETAILS:")
            print(f"   {job_info['error']}")
        
        # Monitoring verification
        print(f"\n🔍 MONITORING VERIFICATION:")
        
        # Check if background monitor is running
        import subprocess
        try:
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            monitor_processes = [line for line in result.stdout.split('\n') 
                               if 'background_monitor.py' in line and 'grep' not in line]
            
            if monitor_processes:
                print("   ✅ Background monitor is running")
                for process in monitor_processes:
                    parts = process.split()
                    pid = parts[1]
                    print(f"   • PID: {pid}")
            else:
                print("   ❌ Background monitor not running")
                print("   • Start with: python background_monitor.py")
        except Exception as e:
            print(f"   ❌ Could not check monitor status: {e}")
        
        # Next steps
        print(f"\n🎯 NEXT STEPS:")
        status = job_info['status'].lower()
        
        if "uploading" in status:
            print("   ⏳ Waiting for data upload to complete...")
            print("   • This usually takes 1-5 minutes")
        elif "queued" in status:
            print("   📋 Job is queued for training...")
            print("   • Training will start when resources are available")
        elif "running" in status:
            print("   🏃 Training is in progress!")
            print("   • Check back in 10-30 minutes for completion")
        elif "completed" in status:
            print("   🎉 Training completed successfully!")
            print("   • Run comparison test with: python quick_comparison.py")
        elif "failed" in status:
            print("   ❌ Training failed")
            print("   • Check error details above")
        
        print(f"\n💡 USEFUL COMMANDS:")
        print(f"   • Refresh dashboard: python training_dashboard.py")
        print(f"   • Check monitor status: python monitor_status.py")
        print(f"   • View live monitoring: tail -f monitor_output.log")
        print(f"   • Quick status check: python status_check.py")
        
        print(f"\n⏰ Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def save_dashboard_data(self):
        """Save dashboard data to JSON for external tools."""
        job_info = self.get_detailed_job_info()
        events = self.get_training_events()
        metrics = self.calculate_training_metrics(job_info)
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "job_info": job_info,
            "events": events,
            "metrics": metrics,
            "monitoring_active": self.check_monitoring_active()
        }
        
        with open("dashboard_data.json", "w") as f:
            json.dump(dashboard_data, f, indent=2)
        
        print("📊 Dashboard data saved to dashboard_data.json")
    
    def check_monitoring_active(self) -> bool:
        """Check if monitoring is active."""
        try:
            import subprocess
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            return 'background_monitor.py' in result.stdout
        except:
            return False


def main():
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("❌ TOGETHER_API_KEY environment variable not set")
        return
    
    dashboard = TrainingDashboard(api_key)
    dashboard.display_dashboard()
    dashboard.save_dashboard_data()


if __name__ == "__main__":
    main()