"""
Training pipeline for orchestrating the complete training process.
"""
from pathlib import Path
from typing import Dict, Any, Optional
from shared.models import TrainingData, TrainingResult, CharacterSpec
from .openai_trainer import OpenAITrainer

class TrainingPipeline:
    """End-to-end training pipeline orchestration."""
    
    def __init__(self, backend: str = "openai", config: Optional[Dict[str, Any]] = None):
        self.backend = backend
        self.config = config or {}
        
        if backend == "openai":
            self.trainer = OpenAITrainer()
        else:
            raise ValueError(f"Unsupported training backend: {backend}")
    
    async def train_character(self, character_spec: CharacterSpec, 
                            training_data: TrainingData,
                            model: str = "gpt-4.1-mini-2025-04-14",
                            suffix: Optional[str] = None) -> TrainingResult:
        """Train a character model."""
        print(f"🚀 Starting training pipeline for character: {character_spec.name}")
        print(f"   Backend: {self.backend}")
        print(f"   Model: {model}")
        print(f"   Training examples: {len(training_data.chats)}")
        
        # Prepare training data
        output_path = Path(f"./training_data/{character_spec.id}_training.jsonl")
        file_id = self.trainer.prepare_training_data(training_data, output_path)
        
        # Set suffix if not provided
        if suffix is None:
            suffix = f"{character_spec.id}_{character_spec.version.lower().replace(' ', '_')}"
        
        # Start fine-tuning
        result = await self.trainer.fine_tune(file_id, model, suffix)
        
        # Update result with character info
        result.character_id = character_spec.id
        
        if result.success:
            print(f"✅ Training completed successfully!")
            print(f"   Model ID: {result.model_id}")
        else:
            print(f"❌ Training failed: {result.error}")
        
        return result
    
    async def deploy_model(self, model_id: str, deployment_config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy a trained model."""
        print(f"🚀 Deploying model: {model_id}")
        
        # For OpenAI, models are automatically available via API
        # For other backends, this would handle deployment
        deployment_result = {
            "model_id": model_id,
            "deployment_url": f"openai://{model_id}",
            "success": True,
            "deployment_timestamp": "2025-01-01T00:00:00Z"
        }
        
        print(f"✅ Model deployed successfully!")
        print(f"   Deployment URL: {deployment_result['deployment_url']}")
        
        return deployment_result
