from together import Together
import os
import time
import json
import fire
import logging
from datetime import datetime
from dotenv import load_dotenv
from deploy_model import deploy_model

load_dotenv()
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def get_file_id(filename: str) -> str:
    """Uploads a file to Together AI and returns the file ID."""
    print(f"Uploading file: {filename}...")
    try:
        #response = together.Files.upload(file=filename, check=True)
        response = client.files.upload(file=filename, check=True)
        file_id = response.id
        print(f"File uploaded successfully. File ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise

def run_finetuning(
    training_file_id: str,
    model: str,
    n_epochs: int = 2,
    learning_rate: float = 3e-5,
    suffix: str = "customer_service_eval",
    from_checkpoint: str | None = None
) -> str:
    """Starts a fine-tuning job on Together AI."""
    
    params = {
        "training_file": training_file_id,
        "n_epochs": n_epochs,
        "n_checkpoints": 1,
        "batch_size": 8,
        "learning_rate": learning_rate,
        "suffix": f"{suffix}_{datetime.now().strftime('%Y%m%d')}",
    }

    if from_checkpoint:
        print(f"Starting fine-tuning from checkpoint: {from_checkpoint} with file ID: {training_file_id}")
        params['from_checkpoint'] = from_checkpoint
    else:
        print(f"Starting fine-tuning for model: {model} with file ID: {training_file_id}")
        params['model'] = model

    try:
        response = client.fine_tuning.create(**params)
        job_id = response.id
        print(f"Fine-tuning job started successfully. Job ID: {job_id}")
        
        # Immediately create an entry with the initial info
        _update_finetuned_json(
            job_id=job_id,
            base_model=model,
            training_file_id=training_file_id,
            status='started',
            from_checkpoint=from_checkpoint
        )
        
        return job_id
    except Exception as e:
        print(f"Error starting fine-tuning job: {e}")
        raise

def follow_finetuning_job(job_id: str) -> dict:
    """Follows the progress of a fine-tuning job."""
    print(f"Following fine-tuning job: {job_id}. This may take a while...")
    while True:
        try:
            response = client.fine_tuning.retrieve(id=job_id)
            status = response.status
            print(f"Current job status: {status}")
            
            if status == 'completed':
                print("Fine-tuning job completed successfully!")
                return response.dict()
            elif status in ['error', 'cancelled', 'failed']:
                print(f"Fine-tuning job failed with status: {status}")
                return response.dict()
            
            time.sleep(60)  # Wait for 60 seconds before checking again
        except Exception as e:
            print(f"Error retrieving job status: {e}")
            time.sleep(60)


def _update_finetuned_json(job_id: str, model_id: str = None, huggingface: str = None, model_info: dict = None, **kwargs):
    """Updates the finetuned_models.json file."""
    json_file = "evals/finetuning/finetuned_models.json"
    
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
            if huggingface:
                existing_data[i]["huggingface"] = huggingface
            if model_info:
                # Only keep essential fields from model_info
                essential_fields = {
                    "id": model_info.get("id"),
                    "training_file": model_info.get("training_file"),
                    "status": model_info.get("status")
                }
                existing_data[i].update({k: v for k, v in essential_fields.items() if v is not None})
            existing_data[i].update(kwargs)
            entry_found = True
            break
    
    if not entry_found:
        new_entry = {"job_id": job_id}
        if model_id:
            new_entry["model_name"] = model_id
        if huggingface:
            new_entry["huggingface"] = huggingface
        if model_info:
            # Only keep essential fields from model_info
            essential_fields = {
                "id": model_info.get("id"),
                "training_file": model_info.get("training_file"),
                "status": model_info.get("status")
            }
            new_entry.update({k: v for k, v in essential_fields.items() if v is not None})
        new_entry.update(kwargs)
        new_entry["created_at"] = datetime.now().isoformat()
        existing_data.append(new_entry)

    with open(json_file, 'w') as f:
        json.dump(existing_data, f, indent=2)

def main(
    train_file: str,
    model: str = "Qwen/Qwen3-32B",
    n_epochs: int = 2,
    learning_rate: float = 3e-5,
    suffix: str = "customer_service_eval",
    from_checkpoint: str | None = None,
    parquet: bool = False
):
    """
    Main function to run the fine-tuning pipeline.
    
    Args:
        train_file: Path to the JSONL file prepared for fine-tuning.
        model: The base model to fine-tune.
        n_epochs: The number of epochs for training.
        suffix: A suffix to add to the fine-tuned model name.
        parquet: Whether the input file is in parquet format.
    """
    load_dotenv()
    if not os.getenv("TOGETHER_API_KEY"):
        print("Error: TOGETHER_API_KEY environment variable not set.")
        return

    try:
        # 1. Upload the data file
        file_id = get_file_id(train_file)
        
        # 2. Start the fine-tuning job
        job_id = run_finetuning(file_id, model, n_epochs, learning_rate, suffix, from_checkpoint=from_checkpoint)

        # 3. Follow the job until completion
        final_status = follow_finetuning_job(job_id)
        
        # 4. Save the model info if completed
        if final_status.get("status") == "completed":
            hf_repo = None
            try:
                logging.info("Deploying model to Hugging Face...")
                hf_repo = deploy_model(job_id=job_id, base_model_name=model)
                logging.info(f"Successfully deployed model to {hf_repo}")
            except Exception as e:
                logging.error(f"Failed to deploy model: {e}")
            
            _update_finetuned_json(job_id, None, huggingface=hf_repo, model_info=final_status, status="completed")

        else:
            print("Fine-tuning did not complete successfully. Model info not saved.")
            _update_finetuned_json(job_id, model_info=final_status, status=final_status.get("status", "failed"))

    except Exception as e:
        print(f"An error occurred during the fine-tuning pipeline: {e}")

if __name__ == '__main__':
    fire.Fire(main)
