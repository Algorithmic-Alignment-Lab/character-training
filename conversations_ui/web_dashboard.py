#!/usr/bin/env python3

import os
import json
import time
from datetime import datetime
import together
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.get_dashboard_html().encode())
        elif self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(self.get_status_data()).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def get_status_data(self):
        """Get current status data."""
        try:
            api_key = os.getenv("TOGETHER_API_KEY")
            if not api_key:
                return {"error": "API key not found"}
            
            client = together.Together(api_key=api_key)
            
            # Load job ID
            try:
                with open("fine_tuning_job_info.json", "r") as f:
                    job_info = json.load(f)
                job_id = job_info["job_id"]
            except FileNotFoundError:
                job_id = "ft-b3cb7680-14cb"
            
            # Get job details
            job = client.fine_tuning.retrieve(id=job_id)
            
            # Calculate progress
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
                stage = status
            
            # Calculate duration
            duration = "Unknown"
            if job.created_at:
                created_time = datetime.fromisoformat(job.created_at.replace('Z', '+00:00'))
                now = datetime.now(created_time.tzinfo)
                duration_obj = now - created_time
                duration = str(duration_obj).split('.')[0]
            
            # Check monitoring status
            monitor_running = False
            try:
                result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
                monitor_running = 'background_monitor.py' in result.stdout
            except:
                pass
            
            return {
                "job_id": job_id,
                "status": str(job.status).replace('FinetuneJobStatus.STATUS_', '').lower(),
                "model": job.model,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "duration": duration,
                "progress": progress,
                "stage": stage,
                "training_file": job.training_file,
                "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
                "monitor_running": monitor_running,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            return {"error": str(e)}
    
    def get_dashboard_html(self):
        """Generate dashboard HTML."""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>Together AI Fine-Tuning Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #3498db;
        }
        .status-card h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric {
            text-align: center;
            padding: 15px;
            background: #ecf0f1;
            border-radius: 8px;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }
        .metric-label {
            font-size: 14px;
            color: #7f8c8d;
            margin-top: 5px;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-running { background-color: #f39c12; }
        .status-completed { background-color: #27ae60; }
        .status-failed { background-color: #e74c3c; }
        .status-queued { background-color: #3498db; }
        .update-time {
            text-align: center;
            color: #7f8c8d;
            font-size: 14px;
            margin-top: 20px;
        }
        .error {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .commands {
            background: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .commands h3 {
            margin-top: 0;
        }
        .command {
            background: #34495e;
            padding: 8px 12px;
            border-radius: 4px;
            font-family: monospace;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 Together AI Fine-Tuning Dashboard</h1>
        
        <div id="error-container"></div>
        
        <div class="status-grid">
            <div class="status-card">
                <h3>📋 Job Information</h3>
                <div><strong>Job ID:</strong> <span id="job-id">Loading...</span></div>
                <div><strong>Status:</strong> <span id="status">Loading...</span></div>
                <div><strong>Model:</strong> <span id="model">Loading...</span></div>
                <div><strong>Duration:</strong> <span id="duration">Loading...</span></div>
            </div>
            
            <div class="status-card">
                <h3>📊 Training Progress</h3>
                <div><strong>Stage:</strong> <span id="stage">Loading...</span></div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <div><strong>Progress:</strong> <span id="progress">0%</span></div>
            </div>
            
            <div class="status-card">
                <h3>⚙️ Parameters</h3>
                <div><strong>Method:</strong> LoRA</div>
                <div><strong>Epochs:</strong> 3</div>
                <div><strong>Learning Rate:</strong> 1e-5</div>
                <div><strong>Examples:</strong> 10</div>
            </div>
            
            <div class="status-card">
                <h3>🔍 Monitoring</h3>
                <div><strong>Monitor Status:</strong> <span id="monitor-status">Loading...</span></div>
                <div><strong>Training File:</strong> <span id="training-file">Loading...</span></div>
                <div><strong>Fine-tuned Model:</strong> <span id="fine-tuned-model">Not available</span></div>
            </div>
        </div>
        
        <div class="metrics">
            <div class="metric">
                <div class="metric-value" id="created-time">Loading...</div>
                <div class="metric-label">Created</div>
            </div>
            <div class="metric">
                <div class="metric-value" id="updated-time">Loading...</div>
                <div class="metric-label">Last Updated</div>
            </div>
        </div>
        
        <div class="commands">
            <h3>💻 Useful Commands</h3>
            <div class="command">python simple_dashboard.py</div>
            <div class="command">python monitor_status.py</div>
            <div class="command">tail -f monitor_output.log</div>
            <div class="command">python quick_comparison.py</div>
        </div>
        
        <div class="update-time">
            Last updated: <span id="last-update">Never</span>
        </div>
    </div>

    <script>
        function updateDashboard() {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        document.getElementById('error-container').innerHTML = 
                            '<div class="error">Error: ' + data.error + '</div>';
                        return;
                    }
                    
                    document.getElementById('error-container').innerHTML = '';
                    document.getElementById('job-id').textContent = data.job_id;
                    document.getElementById('status').innerHTML = 
                        '<span class="status-indicator status-' + data.status + '"></span>' + data.status;
                    document.getElementById('model').textContent = data.model;
                    document.getElementById('duration').textContent = data.duration;
                    document.getElementById('stage').textContent = data.stage;
                    document.getElementById('progress').textContent = data.progress + '%';
                    document.getElementById('progress-fill').style.width = data.progress + '%';
                    document.getElementById('monitor-status').textContent = 
                        data.monitor_running ? '✅ Running' : '❌ Not running';
                    document.getElementById('training-file').textContent = data.training_file;
                    document.getElementById('fine-tuned-model').textContent = 
                        data.fine_tuned_model || 'Not available';
                    
                    if (data.created_at) {
                        document.getElementById('created-time').textContent = 
                            new Date(data.created_at).toLocaleTimeString();
                    }
                    if (data.updated_at) {
                        document.getElementById('updated-time').textContent = 
                            new Date(data.updated_at).toLocaleTimeString();
                    }
                    
                    document.getElementById('last-update').textContent = 
                        new Date().toLocaleTimeString();
                })
                .catch(error => {
                    document.getElementById('error-container').innerHTML = 
                        '<div class="error">Connection error: ' + error.message + '</div>';
                });
        }
        
        // Update every 10 seconds
        updateDashboard();
        setInterval(updateDashboard, 10000);
    </script>
</body>
</html>
        """
    
    def log_message(self, format, *args):
        pass  # Suppress log messages


def start_web_dashboard():
    """Start the web dashboard server."""
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, DashboardHandler)
    print("🌐 Web dashboard started at http://localhost:8080")
    print("   Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Web dashboard stopped")
        httpd.shutdown()


if __name__ == "__main__":
    start_web_dashboard()