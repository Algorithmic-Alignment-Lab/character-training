"""
Model tracking system for fine-tuned models.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

class ModelTracker:
    """Track and manage fine-tuned models."""
    
    def __init__(self, models_file: str = "models.json", globals_file: str = "globals.json"):
        self.models_file = Path(models_file)
        self.globals_file = Path(globals_file)
        self.models = self._load_models()
        self.globals = self._load_globals()
    
    def _load_models(self) -> Dict[str, Any]:
        """Load existing models from file."""
        if self.models_file.exists():
            with open(self.models_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_globals(self) -> Dict[str, Any]:
        """Load existing globals from file."""
        if self.globals_file.exists():
            with open(self.globals_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_models(self):
        """Save models to file."""
        with open(self.models_file, 'w') as f:
            json.dump(self.models, f, indent=2)
    
    def _save_globals(self):
        """Save globals to file."""
        with open(self.globals_file, 'w') as f:
            json.dump(self.globals, f, indent=2)
    
    def register_model(self, 
                      character: str,
                      provider: str,
                      model_id: str,
                      model_name: str,
                      job_id: str,
                      training_data: Dict[str, Any],
                      output_dir: str) -> str:
        """Register a new fine-tuned model."""
        model_key = f"{character}_{provider}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        model_info = {
            "character": character,
            "provider": provider,
            "model_id": model_id,
            "model_name": model_name,
            "job_id": job_id,
            "training_data": training_data,
            "output_dir": output_dir,
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        self.models[model_key] = model_info
        
        # Update globals with latest model info
        if character not in self.globals:
            self.globals[character] = {}
        
        self.globals[character][provider] = {
            "model_id": model_id,
            "model_name": model_name,
            "job_id": job_id,
            "last_updated": datetime.now().isoformat()
        }
        
        self._save_models()
        self._save_globals()
        
        return model_key
    
    def get_model(self, character: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get the latest model for a character and provider."""
        if character in self.globals and provider in self.globals[character]:
            return self.globals[character][provider]
        return None
    
    def list_models(self, character: Optional[str] = None) -> Dict[str, Any]:
        """List all models, optionally filtered by character."""
        if character:
            return {k: v for k, v in self.models.items() if v.get("character") == character}
        return self.models
    
    def get_model_for_evaluation(self, character: str, provider: str = "together") -> Optional[str]:
        """Get model name for evaluation."""
        model_info = self.get_model(character, provider)
        if model_info:
            return model_info["model_name"]
        return None

def test_model_tracker():
    """Test the model tracker."""
    tracker = ModelTracker()
    
    # Test registering a model
    model_key = tracker.register_model(
        character="my_character",
        provider="together",
        model_id="ft-83a97c1e-769b",
        model_name="fellows_safety/Meta-Llama-3.1-8B-Instruct-Reference-209cf266",
        job_id="ft-83a97c1e-769b",
        training_data={"num_chats": 10, "max_turns": 3},
        output_dir="training_output/my_character_together"
    )
    
    print(f"Registered model: {model_key}")
    
    # Test getting model for evaluation
    model_name = tracker.get_model_for_evaluation("my_character", "together")
    print(f"Model for evaluation: {model_name}")
    
    # Test listing models
    models = tracker.list_models("my_character")
    print(f"Models for my_character: {list(models.keys())}")

if __name__ == "__main__":
    test_model_tracker()
