#!/usr/bin/env python3
"""
DPO Fine-tuning Script for OpenAI models.
Supports DPO fine-tuning on top of existing fine-tuned models.
"""

import json
import fire
import os
import time
from pathlib import Path
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


def create_dpo_dataset(
    preferred_file: str,
    rejected_file: str,
    output_file: str,
    max_examples: int = None
) -> None:
    """
    Create DPO training dataset from preferred and rejected chat files.
    
    Args:
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file  
        output_file: Path to output DPO training file
        max_examples: Maximum number of examples to include (None for all)
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
    
    # Ensure we have matching pairs
    if len(preferred_chats) != len(rejected_chats):
        print(f"Warning: Mismatch in chat counts - preferred: {len(preferred_chats)}, rejected: {len(rejected_chats)}")
        min_count = min(len(preferred_chats), len(rejected_chats))
        preferred_chats = preferred_chats[:min_count]
        rejected_chats = rejected_chats[:min_count]
        print(f"Using {min_count} pairs")
    
    # Limit examples if specified
    if max_examples:
        preferred_chats = preferred_chats[:max_examples]
        rejected_chats = rejected_chats[:max_examples]
        print(f"Limited to {max_examples} examples")
    
    # Create DPO training data
    dpo_examples = []
    
    for i, (pref, rej) in enumerate(zip(preferred_chats, rejected_chats)):
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
    
    print(f"Created {len(dpo_examples)} DPO training examples")
    
    # Save DPO training file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for example in dpo_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved DPO training data to: {output_file}")
    
    # Print sample for verification
    if dpo_examples:
        print("\nSample DPO example:")
        print(json.dumps(dpo_examples[0], indent=2))


def upload_training_file(file_path: str) -> str:
    """Upload training file to OpenAI and return file ID."""
    client = OpenAI()
    
    print(f"📤 Uploading training file: {file_path}")
    try:
        with open(file_path, 'rb') as f:
            response = client.files.create(
                file=f,
                purpose="fine-tune"
            )
        file_id = response.id
        print(f"✅ Training file uploaded successfully: {file_id}")
        return file_id
    except Exception as e:
        print(f"❌ Failed to upload training file: {e}")
        raise


def start_dpo_finetuning(
    training_file_id: str,
    base_model: str = "gpt-4.1-mini-2025-04-14",
    suffix: str = "dpo_finetuned"
) -> str:
    """Start DPO fine-tuning job."""
    client = OpenAI()
    
    print(f"🎯 Starting DPO fine-tuning...")
    print(f"  Base model: {base_model}")
    print(f"  Training file ID: {training_file_id}")
    print(f"  Suffix: {suffix}")
    
    try:
        response = client.fine_tuning.jobs.create(
            model=base_model,
            training_file=training_file_id,
            method={
                "type": "dpo",
            },
            suffix=suffix
        )
        
        job_id = response.id
        print(f"✅ DPO fine-tuning job started: {job_id}")
        print(f"  Status: {response.status}")
        
        return job_id
        
    except Exception as e:
        print(f"❌ Failed to start DPO fine-tuning: {e}")
        raise


def monitor_finetuning_job(job_id: str, check_interval: int = 30) -> str:
    """
    Monitor a fine-tuning job until completion.
    
    Args:
        job_id: Fine-tuning job ID
        check_interval: Seconds between status checks
    
    Returns:
        Final model ID if successful, or error message
    """
    client = OpenAI()
    
    print(f"\n👀 Monitoring DPO fine-tuning job: {job_id}")
    print(f"  Checking status every {check_interval} seconds...")
    print(f"  You can also check progress at: https://platform.openai.com/finetune")
    
    while True:
        try:
            job = client.fine_tuning.jobs.retrieve(job_id)
            status = job.status
            
            print(f"  Status: {status}")
            
            if status == "succeeded":
                print(f"  ✅ DPO fine-tuning completed successfully!")
                print(f"  🎉 Fine-tuned model: {job.fine_tuned_model}")
                return job.fine_tuned_model
            elif status == "failed":
                print(f"  ❌ DPO fine-tuning failed!")
                if hasattr(job, 'error') and job.error:
                    print(f"  Error: {job.error}")
                return f"Failed: {job.error if hasattr(job, 'error') else 'Unknown error'}"
            elif status in ["validating_files", "queued", "running"]:
                print(f"  ⏳ Job is {status}...")
                time.sleep(check_interval)
            else:
                print(f"  ⚠️  Unknown status: {status}")
                time.sleep(check_interval)
                
        except Exception as e:
            print(f"  ❌ Error checking job status: {e}")
            return f"Error: {e}"


def run_dpo_finetuning_pipeline(
    preferred_file: str,
    rejected_file: str,
    base_model: str = "gpt-4.1-mini-2025-04-14",
    output_dir: str = "evals/finetuning/dpo_results",
    max_examples: int = None,
    suffix: str = None,
    monitor: bool = True
) -> str:
    """
    Run the complete DPO fine-tuning pipeline.
    
    Args:
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
        base_model: Base model to fine-tune (can be a fine-tuned model ID)
        output_dir: Directory to save results
        max_examples: Maximum number of examples to use
        suffix: Suffix for the fine-tuned model name
        monitor: Whether to monitor the job until completion
    
    Returns:
        Fine-tuned model ID or error message
    """
    
    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return "No API key"
    
    # Set default suffix if not provided
    if suffix is None:
        timestamp = int(time.time())
        suffix = f"dpo_{timestamp}"
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"🚀 Starting DPO Fine-tuning Pipeline")
    print(f"  Preferred file: {preferred_file}")
    print(f"  Rejected file: {rejected_file}")
    print(f"  Base model: {base_model}")
    print(f"  Output directory: {output_dir}")
    print(f"  Max examples: {max_examples or 'All'}")
    print(f"  Suffix: {suffix}")
    
    try:
        # Step 1: Create DPO dataset
        print(f"\n📊 Step 1: Creating DPO dataset...")
        dpo_file = output_path / "dpo_training_data.jsonl"
        create_dpo_dataset(
            preferred_file=preferred_file,
            rejected_file=rejected_file,
            output_file=str(dpo_file),
            max_examples=max_examples
        )
        
        # Step 2: Upload training file
        print(f"\n📤 Step 2: Uploading training file...")
        training_file_id = upload_training_file(str(dpo_file))
        
        # Step 3: Start DPO fine-tuning
        print(f"\n🎯 Step 3: Starting DPO fine-tuning...")
        job_id = start_dpo_finetuning(
            training_file_id=training_file_id,
            base_model=base_model,
            suffix=suffix
        )
        
        # Step 4: Monitor job (if requested)
        if monitor:
            print(f"\n👀 Step 4: Monitoring fine-tuning job...")
            final_model = monitor_finetuning_job(job_id)
            
            # Save results
            results = {
                "job_id": job_id,
                "base_model": base_model,
                "final_model": final_model,
                "training_file": str(dpo_file),
                "preferred_file": preferred_file,
                "rejected_file": rejected_file,
                "max_examples": max_examples,
                "suffix": suffix,
                "timestamp": time.time()
            }
            
            results_file = output_path / "dpo_results.json"
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print(f"\n📁 Results saved to: {results_file}")
            
            if final_model and not final_model.startswith("Failed") and not final_model.startswith("Error"):
                print(f"\n🎉 DPO Fine-tuning Pipeline Completed Successfully!")
                print(f"  Fine-tuned model: {final_model}")
                print(f"  You can now use this model for inference or further fine-tuning")
            else:
                print(f"\n❌ DPO Fine-tuning Pipeline Failed!")
                print(f"  Error: {final_model}")
            
            return final_model
        else:
            print(f"\n⏳ DPO fine-tuning job started: {job_id}")
            print(f"  Monitor progress at: https://platform.openai.com/finetune")
            print(f"  Use 'python evals/finetuning/dpo_finetuning.py monitor --job_id={job_id}' to monitor")
            return job_id
            
    except Exception as e:
        print(f"\n❌ DPO Fine-tuning Pipeline Failed!")
        print(f"  Error: {e}")
        return f"Pipeline failed: {e}"


def monitor_job(job_id: str, check_interval: int = 30) -> str:
    """Monitor a specific fine-tuning job."""
    return monitor_finetuning_job(job_id, check_interval)


if __name__ == "__main__":
    fire.Fire({
        "create_dataset": create_dpo_dataset,
        "upload_file": upload_training_file,
        "start_finetuning": start_dpo_finetuning,
        "monitor": monitor_job,
        "run_pipeline": run_dpo_finetuning_pipeline
    })
