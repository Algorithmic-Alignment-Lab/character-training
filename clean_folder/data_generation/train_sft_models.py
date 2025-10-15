#!/usr/bin/env python3
"""
Simple SFT Training Script for OpenAI and Together AI
Converts generated chat data and trains models.
"""

import json
import os
import asyncio
import random
from pathlib import Path
from typing import List, Dict, Any
import openai
from together import Together

def convert_to_openai_format(chat_data: List[Dict]) -> List[Dict]:
    """Convert chat data to OpenAI fine-tuning format."""
    openai_data = []
    
    for chat in chat_data:
        user_query = chat.get('user_query', '')
        assistant_response = chat.get('assistant_response', '')
        
        if not user_query or not assistant_response:
            continue
        
        # OpenAI format: prompt + completion with separators
        prompt = f"{user_query}\n\n###\n\n"
        completion = f" {assistant_response}###"
        
        openai_data.append({
            "prompt": prompt,
            "completion": completion
        })
    
    return openai_data

def convert_to_together_format(chat_data: List[Dict]) -> List[Dict]:
    """Convert chat data to Together AI fine-tuning format."""
    together_data = []
    
    for chat in chat_data:
        user_query = chat.get('user_query', '')
        assistant_response = chat.get('assistant_response', '')
        
        if not user_query or not assistant_response:
            continue
        
        # Together AI format: messages array
        together_data.append({
            "messages": [
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": assistant_response}
            ]
        })
    
    return together_data

def split_data(data: List[Dict], train_split: float = 0.8) -> tuple[List[Dict], List[Dict]]:
    """Split data into training and validation sets."""
    random.shuffle(data)
    split_idx = int(len(data) * train_split)
    return data[:split_idx], data[split_idx:]

def save_jsonl(data: List[Dict], filepath: str) -> None:
    """Save data as JSONL file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        for item in data:
            f.write(json.dumps(item) + '\n')
    
    print(f"✅ Saved {len(data)} examples to {filepath}")

async def train_openai_model(input_data_path: str, output_dir: str, api_key: str) -> str:
    """Train OpenAI model with generated data."""
    print("🤖 Training OpenAI model...")
    
    # Set API key
    openai.api_key = api_key
    
    # Load and convert data
    with open(input_data_path, 'r') as f:
        chat_data = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(chat_data)} chat examples")
    
    # Convert to OpenAI format
    openai_data = convert_to_openai_format(chat_data)
    train_data, val_data = split_data(openai_data)
    
    # Save training files
    train_path = f"{output_dir}/openai_train.jsonl"
    val_path = f"{output_dir}/openai_val.jsonl"
    
    save_jsonl(train_data, train_path)
    save_jsonl(val_data, val_path)
    
    # Upload files to OpenAI
    print("📤 Uploading training files to OpenAI...")
    
    with open(train_path, 'rb') as f:
        train_file = openai.File.create(file=f, purpose='fine-tune')
    
    with open(val_path, 'rb') as f:
        val_file = openai.File.create(file=f, purpose='fine-tune')
    
    print(f"✅ Training file ID: {train_file.id}")
    print(f"✅ Validation file ID: {val_file.id}")
    
    # Create fine-tuning job
    print("🚀 Creating fine-tuning job...")
    
    job = openai.FineTuningJob.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model="gpt-3.5-turbo",
        n_epochs=3,
        batch_size=4,
        learning_rate_multiplier=1e-5
    )
    
    print(f"✅ Fine-tuning job created: {job.id}")
    
    # Monitor training
    print("👀 Monitoring training progress...")
    
    while True:
        job_status = openai.FineTuningJob.retrieve(job.id)
        print(f"📊 Status: {job_status.status}")
        
        if job_status.status == "succeeded":
            model_id = job_status.fine_tuned_model
            print(f"🎉 Training completed! Model ID: {model_id}")
            return model_id
        elif job_status.status == "failed":
            print(f"❌ Training failed: {job_status.error}")
            raise Exception(f"Training failed: {job_status.error}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def train_together_model(input_data_path: str, output_dir: str, api_key: str) -> str:
    """Train Together AI model with generated data."""
    print("🤖 Training Together AI model...")
    
    # Initialize Together client
    client = Together(api_key=api_key)
    
    # Load and convert data
    with open(input_data_path, 'r') as f:
        chat_data = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(chat_data)} chat examples")
    
    # Convert to Together AI format
    together_data = convert_to_together_format(chat_data)
    train_data, val_data = split_data(together_data)
    
    # Save training files
    train_path = f"{output_dir}/together_train.jsonl"
    val_path = f"{output_dir}/together_val.jsonl"
    
    save_jsonl(train_data, train_path)
    save_jsonl(val_data, val_path)
    
    # Upload files to Together AI
    print("📤 Uploading training files to Together AI...")
    
    with open(train_path, 'rb') as f:
        train_file = client.files.create(file=f, purpose='fine-tune')
    
    with open(val_path, 'rb') as f:
        val_file = client.files.create(file=f, purpose='fine-tune')
    
    print(f"✅ Training file ID: {train_file.id}")
    print(f"✅ Validation file ID: {val_file.id}")
    
    # Create fine-tuning job
    print("🚀 Creating fine-tuning job...")
    
    job = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model="meta-llama/Llama-2-7b-hf",
        n_epochs=3,
        batch_size=4,
        learning_rate=1e-5
    )
    
    print(f"✅ Fine-tuning job created: {job.id}")
    
    # Monitor training
    print("👀 Monitoring training progress...")
    
    while True:
        job_status = client.fine_tuning.jobs.retrieve(job.id)
        print(f"📊 Status: {job_status.status}")
        
        if job_status.status == "succeeded":
            model_id = job_status.fine_tuned_model
            print(f"🎉 Training completed! Model ID: {model_id}")
            return model_id
        elif job_status.status == "failed":
            print(f"❌ Training failed: {job_status.error}")
            raise Exception(f"Training failed: {job_status.error}")
        
        await asyncio.sleep(30)  # Check every 30 seconds

async def main():
    """Main training function."""
    print("🚀 Starting SFT Training Pipeline")
    print("=" * 50)
    
    # Configuration
    input_data_path = "./test_sft_output/test_character/synth_chats.jsonl"
    output_dir = "./sft_training_output"
    
    # API keys
    openai_api_key = os.getenv("OPENAI_API_KEY")
    together_api_key = os.getenv("TOGETHER_API_KEY")
    
    results = {}
    
    # Train OpenAI model
    if openai_api_key:
        print("\n🤖 Training OpenAI model...")
        try:
            openai_model_id = await train_openai_model(input_data_path, output_dir, openai_api_key)
            results['openai_model_id'] = openai_model_id
        except Exception as e:
            print(f"❌ OpenAI training failed: {e}")
    else:
        print("⚠️  OPENAI_API_KEY not found, skipping OpenAI training")
    
    # Train Together AI model
    if together_api_key:
        print("\n🤖 Training Together AI model...")
        try:
            together_model_id = await train_together_model(input_data_path, output_dir, together_api_key)
            results['together_model_id'] = together_model_id
        except Exception as e:
            print(f"❌ Together AI training failed: {e}")
    else:
        print("⚠️  TOGETHER_API_KEY not found, skipping Together AI training")
    
    # Save results
    results_path = f"{output_dir}/training_results.json"
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n🎉 Training pipeline completed!")
    print(f"📊 Results saved to: {results_path}")
    print(f"🤖 OpenAI Model ID: {results.get('openai_model_id', 'N/A')}")
    print(f"🤖 Together AI Model ID: {results.get('together_model_id', 'N/A')}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
