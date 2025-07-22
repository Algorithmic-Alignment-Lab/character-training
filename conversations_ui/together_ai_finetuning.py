#!/usr/bin/env python3

import os
import json
import time
from typing import Dict, Any, Optional
import argparse

try:
    import together
except ImportError:
    print("Installing together package...")
    import subprocess
    subprocess.check_call(["pip", "install", "together"])
    import together


class TogetherAIFineTuner:
    def __init__(self, api_key: str):
        self.api_key = api_key
        together.api_key = api_key
        self.client = together.Together(api_key=api_key)
    
    def upload_file(self, file_path: str) -> str:
        """Upload a JSONL file to Together AI for fine-tuning."""
        try:
            file_response = self.client.files.upload(
                file=file_path,
                purpose='fine-tune'
            )
            
            print(f"File uploaded successfully: {file_response.id}")
            return file_response.id
        except Exception as e:
            print(f"Error uploading file: {e}")
            raise
    
    def create_fine_tuning_job(self, file_id: str, model: str = "meta-llama/Llama-2-7b-chat-hf", 
                              suffix: str = "collaborative-ai") -> str:
        """Create a fine-tuning job with the uploaded file."""
        try:
            job_response = self.client.fine_tuning.create(
                training_file=file_id,
                model=model,
                suffix=suffix,
                lora=True,  # Use LoRA for efficient fine-tuning
                n_epochs=3,
                learning_rate=1e-5,
                train_on_inputs=False  # Don't train on user inputs
            )
            
            print(f"Fine-tuning job created: {job_response.id}")
            return job_response.id
        except Exception as e:
            print(f"Error creating fine-tuning job: {e}")
            raise
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a fine-tuning job."""
        try:
            job_response = self.client.fine_tuning.retrieve(id=job_id)
            return job_response.model_dump()
        except Exception as e:
            print(f"Error getting job status: {e}")
            raise
    
    def wait_for_completion(self, job_id: str, check_interval: int = 30) -> str:
        """Wait for a fine-tuning job to complete."""
        print(f"Waiting for job {job_id} to complete...")
        
        while True:
            status = self.get_job_status(job_id)
            print(f"Status: {status['status']}")
            
            if status['status'] == 'succeeded':
                print(f"Fine-tuning completed! Model: {status['fine_tuned_model']}")
                return status['fine_tuned_model']
            elif status['status'] == 'failed':
                print(f"Fine-tuning failed: {status.get('error', 'Unknown error')}")
                return None
            elif status['status'] in ['cancelled', 'canceled']:
                print("Fine-tuning was cancelled")
                return None
            
            time.sleep(check_interval)
    
    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        try:
            models_response = self.client.models.list()
            return [model.model_dump() for model in models_response]
        except Exception as e:
            print(f"Error listing models: {e}")
            raise
    
    def test_model(self, model_name: str, test_prompt: str) -> str:
        """Test the fine-tuned model with a sample prompt."""
        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": test_prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error testing model: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description="Fine-tune open source models with Together AI")
    parser.add_argument("--data-file", required=True, help="Path to JSONL training data file")
    parser.add_argument("--model", default="meta-llama/Llama-2-7b-chat-hf", help="Base model to fine-tune")
    parser.add_argument("--suffix", default="collaborative-ai", help="Suffix for the fine-tuned model")
    parser.add_argument("--test-prompt", default="What's the best way to learn Python?", help="Test prompt for the fine-tuned model")
    parser.add_argument("--wait", action="store_true", help="Wait for training to complete")
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        raise ValueError("TOGETHER_API_KEY environment variable not set")
    
    # Initialize the fine-tuner
    tuner = TogetherAIFineTuner(api_key)
    
    print(f"Using training data: {args.data_file}")
    print(f"Base model: {args.model}")
    print(f"Model suffix: {args.suffix}")
    
    # Upload the training file
    try:
        file_id = tuner.upload_file(args.data_file)
        print(f"Training file uploaded with ID: {file_id}")
    except Exception as e:
        print(f"Error uploading file: {e}")
        return
    
    # Create the fine-tuning job
    try:
        job_id = tuner.create_fine_tuning_job(file_id, args.model, args.suffix)
        print(f"Fine-tuning job created with ID: {job_id}")
    except Exception as e:
        print(f"Error creating fine-tuning job: {e}")
        return
    
    # Save job info
    job_info = {
        "job_id": job_id,
        "file_id": file_id,
        "model": args.model,
        "suffix": args.suffix,
        "created_at": time.time()
    }
    
    with open("fine_tuning_job_info.json", "w") as f:
        json.dump(job_info, f, indent=2)
    
    print(f"Job info saved to fine_tuning_job_info.json")
    
    # Wait for completion if requested
    if args.wait:
        model_name = tuner.wait_for_completion(job_id)
        
        if model_name:
            print(f"\nTesting the fine-tuned model: {model_name}")
            try:
                response = tuner.test_model(model_name, args.test_prompt)
                print(f"Test prompt: {args.test_prompt}")
                print(f"Model response: {response}")
            except Exception as e:
                print(f"Error testing model: {e}")
    else:
        print(f"\nTo check job status later, use:")
        print(f"python together_ai_finetuning.py --check-job {job_id}")
        print(f"Or call: tuner.get_job_status('{job_id}')")


if __name__ == "__main__":
    main()