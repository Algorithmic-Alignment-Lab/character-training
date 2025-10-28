#!/usr/bin/env python3
"""
SFT Training Pipeline for OpenAI and Together AI
Converts generated chat data to training format and manages fine-tuning.
"""

import json
import os
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import openai
from together import Together

@dataclass
class TrainingConfig:
    """Configuration for SFT training."""
    # Data settings
    input_data_path: str
    output_dir: str
    train_split: float = 0.8
    validation_split: float = 0.2
    
    # OpenAI settings
    openai_api_key: Optional[str] = None
    openai_base_model: str = "gpt-3.5-turbo"
    openai_training_file_id: Optional[str] = None
    openai_fine_tuned_model_id: Optional[str] = None
    
    # Together AI settings
    together_api_key: Optional[str] = None
    together_base_model: str = "meta-llama/Llama-2-7b-hf"
    together_training_file_id: Optional[str] = None
    together_fine_tuned_model_id: Optional[str] = None
    
    # Training parameters
    n_epochs: int = 3
    batch_size: int = 4
    learning_rate: float = 1e-5

class SFTDataConverter:
    """Converts generated chat data to OpenAI/Together AI training format."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
    
    def convert_to_openai_format(self, chat_data: List[Dict]) -> List[Dict]:
        """Convert chat data to OpenAI fine-tuning format."""
        openai_data = []
        
        for chat in chat_data:
            # Extract user query and assistant response
            user_query = chat.get('user_query', '')
            assistant_response = chat.get('assistant_response', '')
            
            if not user_query or not assistant_response:
                continue
            
            # Format for OpenAI fine-tuning
            prompt = f"{user_query}\n\n###\n\n"
            completion = f" {assistant_response}###"
            
            openai_data.append({
                "prompt": prompt,
                "completion": completion
            })
        
        return openai_data
    
    def convert_to_together_format(self, chat_data: List[Dict]) -> List[Dict]:
        """Convert chat data to Together AI fine-tuning format."""
        together_data = []
        
        for chat in chat_data:
            user_query = chat.get('user_query', '')
            assistant_response = chat.get('assistant_response', '')
            
            if not user_query or not assistant_response:
                continue
            
            # Together AI uses messages format
            together_data.append({
                "messages": [
                    {"role": "user", "content": user_query},
                    {"role": "assistant", "content": assistant_response}
                ]
            })
        
        return together_data
    
    def split_data(self, data: List[Dict]) -> tuple[List[Dict], List[Dict]]:
        """Split data into training and validation sets."""
        import random
        random.shuffle(data)
        
        split_idx = int(len(data) * self.config.train_split)
        train_data = data[:split_idx]
        val_data = data[split_idx:]
        
        return train_data, val_data
    
    def save_jsonl(self, data: List[Dict], filepath: str) -> None:
        """Save data as JSONL file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        
        print(f"✅ Saved {len(data)} examples to {filepath}")

class OpenAITrainer:
    """Handles OpenAI fine-tuning."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
    
    async def upload_training_file(self, filepath: str) -> str:
        """Upload training file to OpenAI."""
        print(f"📤 Uploading training file to OpenAI: {filepath}")
        
        with open(filepath, 'rb') as f:
            response = openai.File.create(
                file=f,
                purpose='fine-tune'
            )
        
        file_id = response.id
        print(f"✅ File uploaded with ID: {file_id}")
        return file_id
    
    async def create_fine_tuning_job(self, training_file_id: str, validation_file_id: Optional[str] = None) -> str:
        """Create OpenAI fine-tuning job."""
        print(f"🚀 Creating OpenAI fine-tuning job...")
        
        job_params = {
            "training_file": training_file_id,
            "model": self.config.openai_base_model,
            "n_epochs": self.config.n_epochs,
            "batch_size": self.config.batch_size,
            "learning_rate_multiplier": self.config.learning_rate
        }
        
        if validation_file_id:
            job_params["validation_file"] = validation_file_id
        
        response = openai.FineTuningJob.create(**job_params)
        job_id = response.id
        
        print(f"✅ Fine-tuning job created with ID: {job_id}")
        return job_id
    
    async def monitor_training(self, job_id: str) -> str:
        """Monitor training progress and return model ID when complete."""
        print(f"👀 Monitoring training job: {job_id}")
        
        while True:
            job = openai.FineTuningJob.retrieve(job_id)
            status = job.status
            
            print(f"📊 Training status: {status}")
            
            if status == "succeeded":
                model_id = job.fine_tuned_model
                print(f"🎉 Training completed! Model ID: {model_id}")
                return model_id
            elif status == "failed":
                print(f"❌ Training failed: {job.error}")
                raise Exception(f"Training failed: {job.error}")
            
            await asyncio.sleep(30)  # Check every 30 seconds

class TogetherAITrainer:
    """Handles Together AI fine-tuning."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        if config.together_api_key:
            self.client = Together(api_key=config.together_api_key)
    
    async def upload_training_file(self, filepath: str) -> str:
        """Upload training file to Together AI."""
        print(f"📤 Uploading training file to Together AI: {filepath}")
        
        # Together AI file upload (implementation depends on their API)
        # This is a placeholder - check Together AI docs for actual implementation
        response = self.client.files.create(
            file=open(filepath, 'rb'),
            purpose='fine-tune'
        )
        
        file_id = response.id
        print(f"✅ File uploaded with ID: {file_id}")
        return file_id
    
    async def create_fine_tuning_job(self, training_file_id: str, validation_file_id: Optional[str] = None) -> str:
        """Create Together AI fine-tuning job."""
        print(f"🚀 Creating Together AI fine-tuning job...")
        
        job_params = {
            "training_file": training_file_id,
            "model": self.config.together_base_model,
            "n_epochs": self.config.n_epochs,
            "batch_size": self.config.batch_size,
            "learning_rate": self.config.learning_rate
        }
        
        if validation_file_id:
            job_params["validation_file"] = validation_file_id
        
        response = self.client.fine_tuning.jobs.create(**job_params)
        job_id = response.id
        
        print(f"✅ Fine-tuning job created with ID: {job_id}")
        return job_id
    
    async def monitor_training(self, job_id: str) -> str:
        """Monitor training progress and return model ID when complete."""
        print(f"👀 Monitoring Together AI training job: {job_id}")
        
        while True:
            job = self.client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            print(f"📊 Training status: {status}")
            
            if status == "succeeded":
                model_id = job.fine_tuned_model
                print(f"🎉 Training completed! Model ID: {model_id}")
                return model_id
            elif status == "failed":
                print(f"❌ Training failed: {job.error}")
                raise Exception(f"Training failed: {job.error}")
            
            await asyncio.sleep(30)  # Check every 30 seconds

class SFTTrainingPipeline:
    """Main SFT training pipeline orchestrator."""
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.converter = SFTDataConverter(config)
        self.openai_trainer = OpenAITrainer(config)
        self.together_trainer = TogetherAITrainer(config)
    
    async def prepare_data(self) -> tuple[str, str, str, str]:
        """Prepare training data for both OpenAI and Together AI."""
        print("📊 Preparing training data...")
        
        # Load generated chat data
        with open(self.config.input_data_path, 'r') as f:
            chat_data = [json.loads(line) for line in f]
        
        print(f"📁 Loaded {len(chat_data)} chat examples")
        
        # Convert to OpenAI format
        openai_data = self.converter.convert_to_openai_format(chat_data)
        openai_train, openai_val = self.converter.split_data(openai_data)
        
        # Convert to Together AI format
        together_data = self.converter.convert_to_together_format(chat_data)
        together_train, together_val = self.converter.split_data(together_data)
        
        # Save training files
        openai_train_path = f"{self.config.output_dir}/openai_train.jsonl"
        openai_val_path = f"{self.config.output_dir}/openai_val.jsonl"
        together_train_path = f"{self.config.output_dir}/together_train.jsonl"
        together_val_path = f"{self.config.output_dir}/together_val.jsonl"
        
        self.converter.save_jsonl(openai_train, openai_train_path)
        self.converter.save_jsonl(openai_val, openai_val_path)
        self.converter.save_jsonl(together_train, together_train_path)
        self.converter.save_jsonl(together_val, together_val_path)
        
        return openai_train_path, openai_val_path, together_train_path, together_val_path
    
    async def train_openai(self, train_path: str, val_path: str) -> str:
        """Train OpenAI model."""
        print("🤖 Starting OpenAI fine-tuning...")
        
        # Upload files
        train_file_id = await self.openai_trainer.upload_training_file(train_path)
        val_file_id = await self.openai_trainer.upload_training_file(val_path)
        
        # Create fine-tuning job
        job_id = await self.openai_trainer.create_fine_tuning_job(train_file_id, val_file_id)
        
        # Monitor training
        model_id = await self.openai_trainer.monitor_training(job_id)
        
        return model_id
    
    async def train_together(self, train_path: str, val_path: str) -> str:
        """Train Together AI model."""
        print("🤖 Starting Together AI fine-tuning...")
        
        # Upload files
        train_file_id = await self.together_trainer.upload_training_file(train_path)
        val_file_id = await self.together_trainer.upload_training_file(val_path)
        
        # Create fine-tuning job
        job_id = await self.together_trainer.create_fine_tuning_job(train_file_id, val_file_id)
        
        # Monitor training
        model_id = await self.together_trainer.monitor_training(job_id)
        
        return model_id
    
    async def run_full_pipeline(self) -> Dict[str, str]:
        """Run the complete SFT training pipeline."""
        print("🚀 Starting SFT training pipeline...")
        print("=" * 60)
        
        # Prepare data
        openai_train_path, openai_val_path, together_train_path, together_val_path = await self.prepare_data()
        
        results = {}
        
        # Train OpenAI model
        if self.config.openai_api_key:
            print("\n🤖 Training OpenAI model...")
            openai_model_id = await self.train_openai(openai_train_path, openai_val_path)
            results['openai_model_id'] = openai_model_id
        else:
            print("⚠️  OpenAI API key not provided, skipping OpenAI training")
        
        # Train Together AI model
        if self.config.together_api_key:
            print("\n🤖 Training Together AI model...")
            together_model_id = await self.train_together(together_train_path, together_val_path)
            results['together_model_id'] = together_model_id
        else:
            print("⚠️  Together AI API key not provided, skipping Together AI training")
        
        # Save results
        results_path = f"{self.config.output_dir}/training_results.json"
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n🎉 Training pipeline completed!")
        print(f"📊 Results saved to: {results_path}")
        print(f"🤖 OpenAI Model ID: {results.get('openai_model_id', 'N/A')}")
        print(f"🤖 Together AI Model ID: {results.get('together_model_id', 'N/A')}")
        
        return results

async def main():
    """Example usage of the SFT training pipeline."""
    
    # Configuration
    config = TrainingConfig(
        input_data_path="./test_sft_output/test_character/synth_chats.jsonl",
        output_dir="./sft_training_output",
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        together_api_key=os.getenv("TOGETHER_API_KEY"),
        openai_base_model="gpt-3.5-turbo",
        together_base_model="meta-llama/Llama-2-7b-hf",
        n_epochs=3,
        batch_size=4,
        learning_rate=1e-5
    )
    
    # Create pipeline
    pipeline = SFTTrainingPipeline(config)
    
    # Run training
    results = await pipeline.run_full_pipeline()
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
