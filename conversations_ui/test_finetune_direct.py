#!/usr/bin/env python3

import os
import together

def test_finetune_direct():
    """Test fine-tuning with a known working model."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    # Test with a few known models that should work
    test_models = [
        "togethercomputer/RedPajama-INCITE-7B-Chat",
        "togethercomputer/Llama-2-7B-32K-Instruct",
        "NousResearch/Nous-Hermes-2-Yi-34B",
        "mistralai/Mistral-7B-Instruct-v0.1",
        "teknium/OpenHermes-2.5-Mistral-7B"
    ]
    
    file_id = "file-15edad38-1bdf-4711-b30f-6f00eccab7b7"  # From previous upload
    
    for model in test_models:
        print(f"\nTesting fine-tuning with: {model}")
        
        try:
            job_response = client.fine_tuning.create(
                training_file=file_id,
                model=model,
                suffix="collaborative-ai-test",
                lora=True,
                n_epochs=1,  # Just 1 epoch for testing
                learning_rate=1e-5
            )
            
            print(f"SUCCESS! Fine-tuning job created: {job_response.id}")
            print(f"Model: {model}")
            print(f"Status: {job_response.status}")
            return job_response.id, model
            
        except Exception as e:
            print(f"Failed: {e}")
            continue
    
    print("\nNo working models found. Let's try checking job status on existing jobs...")
    
    # Check existing jobs
    try:
        jobs = client.fine_tuning.list()
        if jobs.data:
            print(f"Found {len(jobs.data)} existing jobs:")
            for job in jobs.data[:3]:
                print(f"  - {job.id}: {job.status} ({job.model})")
        else:
            print("No existing fine-tuning jobs found")
    except Exception as e:
        print(f"Error listing jobs: {e}")

if __name__ == "__main__":
    test_finetune_direct()