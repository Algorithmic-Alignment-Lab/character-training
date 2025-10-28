"""
Transcript management for evaluation results.
"""
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from shared.utils import save_json, load_json, ensure_dir

class TranscriptManager:
    """Manager for creating, saving, and loading evaluation transcripts."""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        ensure_dir(output_dir)
    
    def create_transcript(self, transcript_id: str, evaluator_model: str, target_model: str) -> Dict[str, Any]:
        """Create a new transcript with metadata."""
        current_time = datetime.now()
        return {
            "transcript_id": transcript_id,
            "evaluator_model": evaluator_model,
            "target_model": target_model,
            "created_at": current_time.isoformat(),
            "updated_at": current_time.isoformat(),
            "version": "v2.0",
            "description": "Character evaluation transcript",
            "events": []
        }
    
    def add_transcript_event(self, transcript_events: List[Dict], view: List[str], 
                           message_type: str, content: str, name: str) -> None:
        """Add an event to the transcript."""
        message = {
            "type": message_type,
            "id": str(uuid.uuid4()),
            "name": name,
            "content": content
        }
        
        event = {
            "type": "transcript_event",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "view": view,
            "edit": {
                "operation": "add",
                "message": message
            }
        }
        
        transcript_events.append(event)
    
    def save_transcript(self, variation_number: int, repetition_number: int, 
                       transcript_events: List[Dict], metadata: Dict[str, Any]) -> str:
        """Save transcript to file."""
        filename = f"transcript_{variation_number}_{repetition_number}.json"
        file_path = self.output_dir / filename
        
        # Create full transcript with metadata
        transcript = {
            "metadata": metadata,
            "events": transcript_events
        }
        
        # Update metadata timestamp
        transcript["metadata"]["updated_at"] = datetime.now().isoformat()
        
        save_json(transcript, file_path)
        print(f"📝 Transcript saved to: {file_path}")
        return str(file_path)
    
    def load_transcript(self, transcript_path: Path) -> Dict[str, Any]:
        """Load transcript from file."""
        return load_json(transcript_path)
    
    def append_judge_output(self, transcript_path: Path, judge_output: Dict[str, Any]) -> None:
        """Append judge output to transcript."""
        # Load existing transcript
        transcript = self.load_transcript(transcript_path)
        
        # Initialize metadata if not present
        if "metadata" not in transcript:
            transcript["metadata"] = {}
        
        # Add judge output to metadata
        transcript["metadata"]["judge_output"] = judge_output
        transcript["metadata"]["updated_at"] = datetime.now().isoformat()
        
        # Save updated transcript
        save_json(transcript, transcript_path)
        print(f"📝 Judge output appended to: {transcript_path}")
    
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
    
    def list_transcripts(self) -> List[Path]:
        """List all transcript files in the output directory."""
        return list(self.output_dir.glob("transcript_*.json"))
    
    def get_transcript_summary(self, transcript_path: Path) -> Dict[str, Any]:
        """Get summary information about a transcript."""
        try:
            transcript = self.load_transcript(transcript_path)
            metadata = transcript.get("metadata", {})
            events = transcript.get("events", [])
            
            return {
                "transcript_id": metadata.get("transcript_id", "unknown"),
                "evaluator_model": metadata.get("evaluator_model", "unknown"),
                "target_model": metadata.get("target_model", "unknown"),
                "created_at": metadata.get("created_at", "unknown"),
                "num_events": len(events),
                "has_judge_output": "judge_output" in metadata
            }
        except Exception as e:
            return {"error": str(e)}
