import together
import os
import time
import json
import fire
from datetime import datetime

# Make sure to set the TOGETHER_API_KEY environment variable

def get_file_id(filename: str) -> str:
    """Uploads a file to Together AI and returns the file ID."""
    print(f"Uploading file: {filename}...")
    try:
        response = together.Files.upload(file=filename, check=True)
        file_id = response['id']
        print(f"File uploaded successfully. File ID: {file_id}")
        return file_id
    except Exception as e:
        print(f"Error uploading file: {e}")
        raise

def run_finetuning(
    training_file_id: str,
    model: str = "Qwen/Qwen1.5-32B-Chat",
    n_epochs: int = 3,
    suffix: str = "customer_service_eval",
) -> str:
    """Starts a fine-tuning job on Together AI."""
    print(f"Starting fine-tuning for model: {model} with file ID: {training_file_id}")
    try:
        response = together.Finetune.create(
            training_file=training_file_id,
            model=model,
            n_epochs=n_epochs,
            n_checkpoints=1,
            batch_size=4,
            learning_rate=1e-5,
            suffix=f"{suffix}_{datetime.now().strftime('%Y%m%d')}",
        )
        job_id = response['id']
        print(f"Fine-tuning job started successfully. Job ID: {job_id}")
        return job_id
    except Exception as e:
        print(f"Error starting fine-tuning job: {e}")
        raise

def follow_finetuning_job(job_id: str) -> dict:
    """Follows the progress of a fine-tuning job."""
    print(f"Following fine-tuning job: {job_id}. This may take a while...")
    while True:
        try:
            response = together.Finetune.retrieve(id=job_id)
            status = response['status']
            print(f"Current job status: {status}")
            
            if status == 'completed':
                print("Fine-tuning job completed successfully!")
                return response
            elif status in ['error', 'cancelled']:
                print(f"Fine-tuning job failed with status: {status}")
                return response
            
            time.sleep(60)  # Wait for 60 seconds before checking again
        except Exception as e:
            print(f"Error retrieving job status: {e}")
            time.sleep(60)

def save_model_info(model_info: dict, output_dir: str = "evals/finetuning/"):
    """Saves the fine-tuned model information to a JSON file."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    output_file = os.path.join(output_dir, "finetuned_models.json")
    
    existing_data = []
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode existing model data in {output_file}.")
    
    new_entry = {
        "job_id": model_info.get("id"),
        "model_name": model_info.get("fine_tuned_model"),
        "base_model": model_info.get("model"),
        "training_file_id": model_info.get("training_file"),
        "created_at": datetime.now().isoformat(),
    }
    
    existing_data.append(new_entry)
    
    with open(output_file, 'w') as f:
        json.dump(existing_data, f, indent=4)
        
    print(f"Fine-tuned model info saved to: {output_file}")

def main(
    prepared_data_file: str,
    model: str = "Qwen/Qwen1.5-32B-Chat",
    n_epochs: int = 3,
    suffix: str = "customer_service_eval",
):
    """
    Main function to run the fine-tuning pipeline.
    
    Args:
        prepared_data_file: Path to the JSONL file prepared for fine-tuning.
        model: The base model to fine-tune.
        n_epochs: The number of epochs for training.
        suffix: A suffix to add to the fine-tuned model name.
    """
    if not os.getenv("TOGETHER_API_KEY"):
        print("Error: TOGETHER_API_KEY environment variable not set.")
        return

    try:
        # 1. Upload the data file
        file_id = get_file_id(prepared_data_file)
        
        # 2. Start the fine-tuning job
        job_id = run_finetuning(file_id, model, n_epochs, suffix)
        
        # 3. Follow the job until completion
        final_status = follow_finetuning_job(job_id)
        
        # 4. Save the model info if completed
        if final_status.get("status") == "completed":
            save_model_info(final_status)
        else:
            print("Fine-tuning did not complete successfully. Model info not saved.")

    except Exception as e:
        print(f"An error occurred during the fine-tuning pipeline: {e}")

if __name__ == '__main__':
    fire.Fire(main)
