from openai import OpenAI
import os
import time
import json
import fire
import logging
from datetime import datetime
from dotenv import load_dotenv
import sys
from typing import Optional

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_file_id(filename: str) -> str:
    """Uploads a file to OpenAI and returns the file ID."""
    print(f"Uploading file: {filename}...")
    try:
        with open(filename, 'rb') as file:
            response = client.files.create(
                file=file,
                purpose="fine-tune"
            )
        file_id = response.id
        print(f"File uploaded successfully. File ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise

def run_finetuning(
    training_file_id: str,
    model: str,
    n_epochs: int = 1,
    learning_rate_multiplier: float = 1,
    suffix: str = "customer_service_eval"
) -> str:
    """Starts a fine-tuning job on OpenAI."""
    
    print(f"Starting fine-tuning for model: {model} with file ID: {training_file_id}")
    
    try:
        # Request a supervised fine-tuning job and explicitly declare the
        # training file format as prompt/completion to avoid automatic
        # validation expecting chat-style `messages` entries.
        response = client.fine_tuning.jobs.create(
            model=model,
            training_file=training_file_id,
            method={
                "type": "supervised",
                    "supervised": {
                        "hyperparameters": {
                            "n_epochs": n_epochs,
                            "learning_rate_multiplier": learning_rate_multiplier,
                        },
                    },
            },
            suffix=f"{suffix}_{datetime.now().strftime('%Y%m%d')}"
        )
        
        job_id = response.id
        print(f"Fine-tuning job started successfully. Job ID: {job_id}")
        
        # Immediately create an entry with the initial info
        _update_finetuned_json(
            job_id=job_id,
            base_model=model,
            training_file_id=training_file_id,
            status='started'
        )
        
        return job_id
    except Exception as e:
        print(f"Error starting fine-tuning job: {e}")
        raise

def format_event(event):
    """Format event for display in CLI progress."""
    # Events can be dicts or objects depending on SDK, handle both
    try:
        ev_type = getattr(event, 'type', None) or event.get('type')
    except Exception:
        ev_type = None

    try:
        if ev_type == "metrics":
            # metrics may include train_loss or loss
            metrics = getattr(event, 'metrics', None) or event.get('metrics', {})
            step = getattr(event, 'step', None) or event.get('step')
            loss = metrics.get('train_loss') if isinstance(metrics, dict) else None
            if loss is None:
                loss = metrics.get('loss') if isinstance(metrics, dict) else None
            loss_str = f"{loss:.4f}" if isinstance(loss, (int, float)) else loss
            return f"[Metrics] Step {step}: Loss = {loss_str}"
        else:
            msg = getattr(event, 'message', None) or event.get('message') if isinstance(event, dict) else None
            if not msg:
                # fallback to stringified event
                msg = str(event)
            t = ev_type.capitalize() if isinstance(ev_type, str) else 'Event'
            return f"[{t}] {msg}"
    except Exception:
        return str(event)

def follow_finetuning_job(job_id: str) -> dict:
    """Follows the progress of a fine-tuning job with live updates."""
    print(f"Following fine-tuning job: {job_id}. This may take a while...")
    
    last_event_id = None
    
    try:
        while True:
            job = client.fine_tuning.jobs.retrieve(job_id)
            events = client.fine_tuning.jobs.list_events(
                fine_tuning_job_id=job_id,
                limit=50,
                after=last_event_id
            )
            
            # Print any new events
            for event in events.data:
                if event.id != last_event_id:
                    print(format_event(event))
                    last_event_id = event.id
            
            if job.status == "succeeded":
                print("\nFine-tuning job completed successfully!")
                print(f"Model ID: {job.fine_tuned_model}")
                return job.model_dump()
            elif job.status in ["failed", "cancelled"]:
                print(f"\nFine-tuning job failed with status: {job.status}")
                # job may not have failed_reason in older/newer SDKs; print what's available
                reason = getattr(job, 'failed_reason', None) or getattr(job, 'failure_reason', None) or getattr(job, 'error', None)
                if reason:
                    print(f"Failure reason: {reason}")
                # Try fetching recent events to provide context
                try:
                    events = client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=20)
                    print("Last events:")
                    for ev in events.data[-10:]:
                        print(format_event(ev))
                except Exception:
                    pass
                return job.model_dump()
                
            time.sleep(10)  # Check for updates every 10 seconds
            
    except Exception as e:
        print(f"Error retrieving job status: {e}")
        raise

def _update_finetuned_json(job_id: str, model_id: str = None, model_info: dict = None, **kwargs):
    """Updates the finetuned_models.json file."""
    json_file = "evals/finetuning/finetuned_models_openai.json"
    
    existing_data = []
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode existing model data in {json_file}.")

    entry_found = False
    for i, entry in enumerate(existing_data):
        if entry.get("job_id") == job_id:
            if model_id:
                existing_data[i]["model_name"] = model_id
            if model_info:
                # Keep essential fields from model_info
                essential_fields = {
                    "id": model_info.get("id"),
                    "training_file": model_info.get("training_file"),
                    "status": model_info.get("status"),
                    "fine_tuned_model": model_info.get("fine_tuned_model")
                }
                existing_data[i].update({k: v for k, v in essential_fields.items() if v is not None})
            existing_data[i].update(kwargs)
            entry_found = True
            break
    
    if not entry_found:
        new_entry = {"job_id": job_id}
        if model_id:
            new_entry["model_name"] = model_id
        if model_info:
            # Keep essential fields from model_info
            essential_fields = {
                "id": model_info.get("id"),
                "training_file": model_info.get("training_file"),
                "status": model_info.get("status"),
                "fine_tuned_model": model_info.get("fine_tuned_model")
            }
            new_entry.update({k: v for k, v in essential_fields.items() if v is not None})
        new_entry.update(kwargs)
        new_entry["created_at"] = datetime.now().isoformat()
        existing_data.append(new_entry)

    with open(json_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

def _update_globals_json(model_id: str, suffix: str = None):
    """Updates the globals.json file with the new fine-tuned model."""
    json_path = "auto_eval_gen/globals.json"
    
    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found. Cannot update models.")
        return
    model_key = None
    # Generate a model key from the suffix or use a default pattern
    if suffix:
        # Extract character name from suffix (e.g., "rudi_storyteller_companion_backstory_20250909-085128" -> "rudi_storyteller_companion_backstory")
        model_key = suffix
    else:
        # Use a default pattern based on model_id
        model_key = f"ft-{model_id.split(':')[-1][:8]}" if ':' in model_id else f"ft-{model_id[:8]}"
    
    # Load the current models dictionary
    try:
        with open(json_path, 'r') as f:
            models = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error reading {json_path}: {e}")
        return
    
    # Add or update the model entry
    models[model_key] = {
        "id": model_id,
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    }
    
    # Save the updated models dictionary back to JSON
    try:
        with open(json_path, 'w') as f:
            json.dump(models, f, indent=2)
        print(f"✅ Updated globals.json with new model: {model_key} -> {model_id}")
    except Exception as e:
        print(f"Error writing to {json_path}: {e}")

def main(
    train_file: str,
    model: str = "gpt-3.5-turbo",  # Default to GPT-3.5 Turbo as base model
    n_epochs: int = 1,
    learning_rate_multiplier: float = 1,
    suffix: str = "customer_service_eval",
):
    """
    Main function to run the OpenAI fine-tuning pipeline.
    
    Args:
        train_file: Path to the JSONL file prepared for fine-tuning
        model: The base model to fine-tune (e.g., "gpt-3.5-turbo")
        n_epochs: The number of epochs for training
        learning_rate: Learning rate multiplier for training
        suffix: A suffix to add to the fine-tuned model name
    """
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set.")
        return

    try:
        # 1. Upload the data file
        file_id = get_file_id(train_file)
        
        # 2. Start the fine-tuning job
        job_id = run_finetuning(file_id, model, n_epochs, learning_rate_multiplier, suffix)

        # 3. Follow the job until completion with live progress updates
        final_status = follow_finetuning_job(job_id)
        
        # 4. Save the model info
        if final_status.get("status") == "succeeded":
            model_id = final_status.get("fine_tuned_model")
            _update_finetuned_json(
                job_id=job_id,
                model_id=model_id,
                model_info=final_status,
                status="completed"
            )
            print(f"\nFine-tuning completed! The model ID is: {model_id}")
            
            # Update globals.json with the new fine-tuned model
            _update_globals_json(model_id, suffix)
            
        else:
            print("\nFine-tuning did not complete successfully. Model info saved with failed status.")
            _update_finetuned_json(
                job_id=job_id,
                model_info=final_status,
                status=final_status.get("status", "failed")
            )

    except Exception as e:
        print(f"An error occurred during the fine-tuning pipeline: {e}")

if __name__ == '__main__':
    fire.Fire(main)
