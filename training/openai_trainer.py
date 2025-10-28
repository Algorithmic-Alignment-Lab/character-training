"""
OpenAI fine-tuning integration.
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import openai
from shared.models import TrainingData, TrainingResult, Chat
from shared.config import config

class OpenAITrainer:
    """OpenAI fine-tuning trainer."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or config.openai_api_key
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def prepare_training_data(self, training_data: TrainingData, output_path: Path) -> str:
        """Prepare training data in OpenAI format and upload file."""
        # Convert chats to OpenAI format
        openai_data = []
        for chat in training_data.chats:
            messages = []
            for msg in chat.messages:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            openai_data.append({
                "messages": messages
            })
        
        # Save to JSONL file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in openai_data:
                f.write(json.dumps(item) + '\n')
        
        print(f"📝 Prepared training data: {len(openai_data)} examples")
        
        # Upload file to OpenAI
        with open(output_path, 'rb') as f:
            file_response = self.client.files.create(
                file=f,
                purpose='fine-tune'
            )
        
        print(f"📤 Uploaded training file: {file_response.id}")
        return file_response.id
    
    async def fine_tune(self, file_id: str, model: str = "gpt-4.1-mini-2025-04-14", suffix: str = "character") -> TrainingResult:
        """Start fine-tuning job."""
        try:
            print(f"🚀 Starting fine-tuning job...")
            print(f"   Model: {model}")
            print(f"   File ID: {file_id}")
            print(f"   Suffix: {suffix}")
            
            # Create fine-tuning job
            job = self.client.fine_tuning.jobs.create(
                training_file=file_id,
                model=model,
                suffix=suffix
            )
            
            print(f"✅ Fine-tuning job created: {job.id}")
            
            # Wait for completion
            return await self._wait_for_completion(job.id, file_id)
            
        except Exception as e:
            print(f"❌ Fine-tuning failed: {e}")
            return TrainingResult(
                model_id="",
                character_id="",
                training_data_path="",
                success=False,
                error=str(e)
            )
    
    async def _wait_for_completion(self, job_id: str, file_id: str) -> TrainingResult:
        """Wait for fine-tuning job to complete."""
        print(f"⏳ Waiting for fine-tuning job to complete...")
        
        while True:
            try:
                job = self.client.fine_tuning.jobs.retrieve(job_id)
                status = job.status
                
                print(f"   Status: {status}")
                
                if status == "succeeded":
                    print(f"✅ Fine-tuning completed successfully!")
                    print(f"   Model ID: {job.fine_tuned_model}")
                    
                    return TrainingResult(
                        model_id=job.fine_tuned_model,
                        character_id="",  # Will be set by caller
                        training_data_path=file_id,
                        success=True,
                        training_metrics={
                            "job_id": job_id,
                            "training_file": file_id,
                            "fine_tuned_model": job.fine_tuned_model,
                            "status": status
                        }
                    )
                
                elif status == "failed":
                    error_msg = getattr(job, 'error', {}).get('message', 'Unknown error')
                    print(f"❌ Fine-tuning failed: {error_msg}")
                    
                    return TrainingResult(
                        model_id="",
                        character_id="",
                        training_data_path=file_id,
                        success=False,
                        error=error_msg
                    )
                
                elif status in ["validating_files", "queued", "running"]:
                    print(f"   Progress: {getattr(job, 'progress', 'Unknown')}%")
                    await asyncio.sleep(30)  # Wait 30 seconds before checking again
                
                else:
                    print(f"   Unknown status: {status}")
                    await asyncio.sleep(30)
                    
            except Exception as e:
                print(f"❌ Error checking job status: {e}")
                return TrainingResult(
                    model_id="",
                    character_id="",
                    training_data_path=file_id,
                    success=False,
                    error=f"Error checking job status: {e}"
                )
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get fine-tuning job status."""
        try:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            return {
                "id": job.id,
                "status": job.status,
                "model": job.model,
                "fine_tuned_model": getattr(job, 'fine_tuned_model', None),
                "progress": getattr(job, 'progress', None),
                "error": getattr(job, 'error', None)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def list_fine_tuned_models(self) -> List[Dict[str, Any]]:
        """List all fine-tuned models."""
        try:
            models = self.client.models.list()
            fine_tuned_models = []
            
            for model in models.data:
                if model.id.startswith("ft:"):
                    fine_tuned_models.append({
                        "id": model.id,
                        "created": model.created,
                        "owned_by": model.owned_by
                    })
            
            return fine_tuned_models
        except Exception as e:
            print(f"❌ Error listing models: {e}")
            return []
    
    def delete_fine_tuned_model(self, model_id: str) -> bool:
        """Delete a fine-tuned model."""
        try:
            self.client.models.delete(model_id)
            print(f"✅ Deleted model: {model_id}")
            return True
        except Exception as e:
            print(f"❌ Error deleting model: {e}")
            return False

# Import asyncio for the async sleep
import asyncio
