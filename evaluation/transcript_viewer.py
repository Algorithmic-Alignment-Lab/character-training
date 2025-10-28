"""
Transcript viewer for visualizing evaluation results.
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

class TranscriptViewer:
    """Transcript viewer using @kaifronsdal/transcript-viewer."""
    
    def __init__(self, transcript_dir: Path, port: int = 8080):
        self.transcript_dir = transcript_dir
        self.port = port
    
    def start_viewer(self) -> None:
        """Start the transcript viewer."""
        try:
            cmd = [
                "npx", "@kaifronsdal/transcript-viewer@latest",
                "--dir", str(self.transcript_dir),
                "--port", str(self.port),
                "--host", "0.0.0.0"
            ]
            
            print(f"🌐 Starting transcript viewer...")
            print(f"   Directory: {self.transcript_dir}")
            print(f"   URL: http://localhost:{self.port}")
            print(f"   Command: {' '.join(cmd)}")
            
            subprocess.run(cmd, check=True)
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Error starting transcript viewer: {e}")
            print("Make sure Node.js and npm are installed")
            print("Install the viewer with: npm install -g @kaifronsdal/transcript-viewer")
        except FileNotFoundError:
            print("❌ Node.js not found. Please install Node.js and npm")
    
    def download_wandb_transcripts(self, run_ids: List[str], project_name: str) -> None:
        """Download transcripts from Weights & Biases."""
        try:
            import wandb
            
            print(f"📥 Downloading transcripts from W&B project: {project_name}")
            
            for run_id in run_ids:
                print(f"   Downloading run: {run_id}")
                
                # Download artifacts
                api = wandb.Api()
                run = api.run(f"{project_name}/{run_id}")
                
                for artifact in run.logged_artifacts():
                    for file in artifact.files():
                        if file.name.startswith("transcript_"):
                            print(f"     Downloading: {file.name}")
                            file.download(root=str(self.transcript_dir))
            
            print(f"✅ Downloaded transcripts to: {self.transcript_dir}")
            
        except ImportError:
            print("❌ wandb not installed. Install with: pip install wandb")
        except Exception as e:
            print(f"❌ Error downloading transcripts: {e}")
    
    def format_transcript_for_display(self, transcript_events: List[Dict]) -> str:
        """Format transcript events for display."""
        formatted_lines = []
        
        # Filter only events that have 'combined' in their view
        combined_events = [
            event for event in transcript_events if "combined" in event.get("view", [])
        ]
        
        # Sort by timestamp
        combined_events.sort(key=lambda x: x.get("timestamp", ""))
        
        for event in combined_events:
            message = event.get("edit", {}).get("message", {})
            name = message.get("name", "Unknown")
            content = message.get("content", "")
            message_type = message.get("type", "")
            
            # Skip system messages or empty content
            if message_type == "system" or not content.strip():
                continue
            
            # Format as "Name: content"
            formatted_lines.append(f"{name}: {content}")
            formatted_lines.append("")  # Empty line for readability
        
        return "\n".join(formatted_lines).strip()
    
    def list_available_transcripts(self) -> List[Path]:
        """List all available transcript files."""
        return list(self.transcript_dir.glob("transcript_*.json"))
    
    def get_transcript_info(self, transcript_path: Path) -> Dict[str, Any]:
        """Get information about a transcript file."""
        try:
            with open(transcript_path, 'r') as f:
                data = json.load(f)
            
            metadata = data.get("metadata", {})
            events = data.get("events", [])
            
            return {
                "filename": transcript_path.name,
                "transcript_id": metadata.get("transcript_id", "unknown"),
                "evaluator_model": metadata.get("evaluator_model", "unknown"),
                "target_model": metadata.get("target_model", "unknown"),
                "created_at": metadata.get("created_at", "unknown"),
                "num_events": len(events),
                "has_judge_output": "judge_output" in metadata,
                "file_size": transcript_path.stat().st_size
            }
        except Exception as e:
            return {"error": str(e), "filename": transcript_path.name}
    
    def print_transcript_summary(self) -> None:
        """Print a summary of all available transcripts."""
        transcripts = self.list_available_transcripts()
        
        if not transcripts:
            print("📝 No transcripts found in directory")
            return
        
        print(f"📝 Found {len(transcripts)} transcripts:")
        print("-" * 80)
        
        for transcript_path in sorted(transcripts):
            info = self.get_transcript_info(transcript_path)
            
            if "error" in info:
                print(f"❌ {info['filename']}: {info['error']}")
                continue
            
            print(f"📄 {info['filename']}")
            print(f"   ID: {info['transcript_id']}")
            print(f"   Models: {info['evaluator_model']} → {info['target_model']}")
            print(f"   Events: {info['num_events']}")
            print(f"   Judge Output: {'✅' if info['has_judge_output'] else '❌'}")
            print(f"   Size: {info['file_size']} bytes")
            print()
