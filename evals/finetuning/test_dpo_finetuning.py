#!/usr/bin/env python3
"""
Test script for DPO fine-tuning with a small dataset (100 examples).
This script creates a test DPO dataset and runs fine-tuning to verify the pipeline works.
"""

import json
import fire
import os
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, Optional
import time
from dotenv import load_dotenv

load_dotenv()

def create_test_dpo_dataset(
    preferred_file: str,
    rejected_file: str,
    output_file: str,
    test_size: int = 100
) -> None:
    """
    Create a small test DPO dataset for testing fine-tuning.
    
    Args:
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
        output_file: Path to output test DPO training file
        test_size: Number of examples for testing (default: 100)
    """
    
    # Load preferred and rejected chats
    preferred_chats = []
    rejected_chats = []
    
    print(f"Loading preferred chats from: {preferred_file}")
    with open(preferred_file, 'r') as f:
        for line in f:
            if line.strip():
                preferred_chats.append(json.loads(line))
    
    print(f"Loading rejected chats from: {rejected_file}")
    with open(rejected_file, 'r') as f:
        for line in f:
            if line.strip():
                rejected_chats.append(json.loads(line))
    
    print(f"Loaded {len(preferred_chats)} preferred chats and {len(rejected_chats)} rejected chats")
    
    # Take first test_size examples
    test_preferred = preferred_chats[:test_size]
    test_rejected = rejected_chats[:test_size]
    
    print(f"Using {len(test_preferred)} examples for testing")
    
    # Create DPO training data
    dpo_examples = []
    
    for i, (pref, rej) in enumerate(zip(test_preferred, test_rejected)):
        # Verify user queries match
        if pref.get('user_query') != rej.get('user_query'):
            print(f"Warning: User queries don't match at index {i}")
            continue
        
        # Create DPO example in OpenAI format
        dpo_example = {
            "messages": [
                {
                    "role": "user",
                    "content": pref['user_query']
                },
                {
                    "role": "assistant", 
                    "content": pref['assistant_response']
                }
            ],
            "rejected_messages": [
                {
                    "role": "user",
                    "content": rej['user_query']
                },
                {
                    "role": "assistant",
                    "content": rej['assistant_response']
                }
            ]
        }
        
        dpo_examples.append(dpo_example)
    
    print(f"Created {len(dpo_examples)} test DPO training examples")
    
    # Save test DPO training file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for example in dpo_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved test DPO training data to: {output_file}")
    
    # Print sample for verification
    if dpo_examples:
        print("\nSample test DPO example:")
        print(json.dumps(dpo_examples[0], indent=2))


def run_dpo_finetuning_test(
    train_file: str,
    model: str = "gpt-4.1-mini-2025-04-14",    
    suffix: Optional[str] = None,
    dry_run: bool = False
) -> str:
    """
    Run DPO fine-tuning test with a small dataset.
    
    Args:
        train_file: Path to DPO training file
        model: Base model to fine-tune
        suffix: Suffix for the fine-tuned model name
        dry_run: If True, only validate the training file without starting training
    
    Returns:
        Fine-tuned model ID or validation message
    """
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY environment variable not set.")
        print("   For dry run validation, this is fine.")
        print("   For actual fine-tuning, please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        
        if not dry_run:
            return "No API key - cannot run actual fine-tuning"
    
    # Initialize OpenAI client
    client = None
    try:
        client = OpenAI()
    except Exception as e:
        if dry_run:
            print(f"⚠️  Could not initialize OpenAI client: {e}")
            print("   Proceeding with dry run validation only...")
        else:
            return f"OpenAI client initialization failed: {e}"
    
    # Set default suffix if not provided
    if suffix is None:
        suffix = f"dpo_test_{int(time.time())}"
    
    print(f"🚀 Starting DPO fine-tuning test...")
    print(f"  Model: {model}")
    print(f"  Training file: {train_file}")
    print(f"  Suffix: {suffix}")
    print(f"  Dry run: {dry_run}")
    
    # Validate training file
    print(f"\n📋 Validating training file...")
    try:
        with open(train_file, 'r') as f:
            lines = f.readlines()
        
        print(f"  Training file has {len(lines)} examples")
        
        # Validate first few examples
        for i, line in enumerate(lines[:3]):
            example = json.loads(line.strip())
            required_keys = ['messages', 'rejected_messages']
            for key in required_keys:
                if key not in example:
                    raise ValueError(f"Missing required key '{key}' in example {i}")
            
            # Check messages format
            for msg_type in ['messages', 'rejected_messages']:
                messages = example[msg_type]
                if not isinstance(messages, list) or len(messages) != 2:
                    raise ValueError(f"Invalid {msg_type} format in example {i}")
                
                user_msg = messages[0]
                assistant_msg = messages[1]
                
                if user_msg.get('role') != 'user' or assistant_msg.get('role') != 'assistant':
                    raise ValueError(f"Invalid message roles in {msg_type} for example {i}")
        
        print(f"  ✅ Training file validation passed")
        
    except Exception as e:
        print(f"  ❌ Training file validation failed: {e}")
        return f"Validation failed: {e}"
    
    if dry_run:
        print(f"\n🔍 Dry run completed successfully!")
        print(f"  Training file is valid and ready for DPO fine-tuning")
        return "Dry run completed - training file is valid"
    
    if client is None:
        return "No OpenAI client available - cannot proceed with fine-tuning"
    
    # Upload training file
    print(f"\n📤 Uploading training file...")
    try:
        with open(train_file, 'rb') as f:
            training_file = client.files.create(
                file=f,
                purpose="fine-tune"
            )
        print(f"  ✅ Training file uploaded: {training_file.id}")
    except Exception as e:
        print(f"  ❌ Failed to upload training file: {e}")
        return f"Upload failed: {e}"
    
    # Start fine-tuning job
    print(f"\n🎯 Starting DPO fine-tuning job...")
    try:
        fine_tuning_job = client.fine_tuning.jobs.create(
            training_file=training_file.id,
            model=model,
            suffix=suffix
        )
        
        print(f"  ✅ Fine-tuning job started: {fine_tuning_job.id}")
        print(f"  Status: {fine_tuning_job.status}")
        
        return fine_tuning_job.id
        
    except Exception as e:
        print(f"  ❌ Failed to start fine-tuning job: {e}")
        return f"Fine-tuning failed: {e}"


def monitor_finetuning_job(job_id: str, check_interval: int = 30) -> None:
    """
    Monitor a fine-tuning job until completion.
    
    Args:
        job_id: Fine-tuning job ID
        check_interval: Seconds between status checks
    """
    
    client = OpenAI()
    
    print(f"\n👀 Monitoring fine-tuning job: {job_id}")
    print(f"  Checking status every {check_interval} seconds...")
    
    while True:
        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            print(f"  Status: {status}")
            
            if status == "succeeded":
                print(f"  ✅ Fine-tuning completed successfully!")
                print(f"  Fine-tuned model: {job.fine_tuned_model}")
                break
            elif status == "failed":
                print(f"  ❌ Fine-tuning failed!")
                if hasattr(job, 'error') and job.error:
                    print(f"  Error: {job.error}")
                break
            elif status in ["validating_files", "queued", "running"]:
                print(f"  ⏳ Job is {status}...")
                time.sleep(check_interval)
            else:
                print(f"  ⚠️  Unknown status: {status}")
                time.sleep(check_interval)
                
        except Exception as e:
            print(f"  ❌ Error checking job status: {e}")
            break


def run_full_dpo_test(
    preferred_file: str,
    rejected_file: str,
    test_size: int = 100,
    model: str = "gpt-4.1-mini-2025-04-14",
    dry_run: bool = False,
    monitor: bool = False
) -> None:
    """
    Run the complete DPO test pipeline: create test dataset and run fine-tuning.
    
    Args:
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
        test_size: Number of examples for testing
        model: Base model to fine-tune
        dry_run: If True, only validate without starting training
        monitor: If True, monitor the job until completion
    """
    
    # Create test DPO dataset
    test_output_file = f"evals/finetuning/test_dpo_data_{test_size}_examples.jsonl"
    
    print(f"🔧 Creating test DPO dataset with {test_size} examples...")
    create_test_dpo_dataset(
        preferred_file=preferred_file,
        rejected_file=rejected_file,
        output_file=test_output_file,
        test_size=test_size
    )
    
    # Run DPO fine-tuning test
    print(f"\n🚀 Running DPO fine-tuning test...")
    job_id = run_dpo_finetuning_test(
        train_file=test_output_file,
        model=model,
        dry_run=dry_run
    )
    
    if dry_run:
        print(f"\n✅ Dry run completed successfully!")
        print(f"  Test dataset created: {test_output_file}")
        print(f"  Ready for actual DPO fine-tuning!")
    else:
        print(f"\n🎯 DPO fine-tuning test started!")
        print(f"  Job ID: {job_id}")
        print(f"  Test dataset: {test_output_file}")
        
        if monitor:
            monitor_finetuning_job(job_id)
        else:
            print(f"  Use 'python evals/finetuning/test_dpo_finetuning.py monitor --job_id={job_id}' to monitor progress")


if __name__ == "__main__":
    fire.Fire({
        "create_test_dataset": create_test_dpo_dataset,
        "run_test": run_dpo_finetuning_test,
        "monitor": monitor_finetuning_job,
        "run_full_test": run_full_dpo_test
    })
