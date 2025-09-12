import os
import together
import tempfile
from huggingface_hub import HfApi, create_repo
from dotenv import load_dotenv
import fire
import sys
from pathlib import Path
import logging
import subprocess
from typing import Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to allow sibling imports
sys.path.append(str(Path(__file__).resolve().parents[1]))
from llm_api import load_vllm_lora_adapter

def get_model_name_from_job_id(job_id: str) -> str:
    """
    Retrieves the model name from a Together AI fine-tuning job ID.
    """
    logger.info(f"Looking up model name for job ID: {job_id}")
    try:
        job_details = together.Finetune.retrieve(job_id)
        
        model_name = job_details.get('fine_tuned_model')
        if model_name:
            logger.info(f"Found model name from 'fine_tuned_model' field: {model_name}")
            return model_name
        
        status = job_details.get('status', 'unknown')
        if status == 'completed':
            model_path = job_details.get('model_output_path') or job_details.get('adapter_output_path')
            if model_path:
                model_name = Path(model_path).name
                logger.info(f"Constructed model name from output path: {model_name}")
                return model_name
        
        # Fallback for various states
        logger.warning(f"Could not determine specific model name for job {job_id} (status: {status}). Using job ID as model name.")
        return job_id
            
    except Exception as e:
        logger.error(f"Failed to retrieve model name for job ID {job_id}: {e}")
        raise

def get_base_model_from_job_id(job_id: str) -> str | None:
    """
    Retrieves the base model name from a Together AI fine-tuning job ID.
    """
    logger.info(f"Looking up base model for job ID: {job_id}")
    try:
        job_details = together.Finetune.retrieve(job_id)
        base_model = job_details.get('model')
        if base_model:
            logger.info(f"Found base model: {base_model}")
            return base_model
        logger.warning(f"Could not find base model for job ID {job_id}")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve base model for job ID {job_id}: {e}")
        return None

def upload_model_with_script(hf_model_id: str, together_job_id: str, base_model_name: str | None):
    """
    Creates and executes a shell script to download a model from Together,
    and push it to a Hugging Face repository using huggingface-cli.
    """
    logger.info(f"Starting upload process for {hf_model_id} using a generated script.")
    
    load_dotenv()
    hf_token = os.getenv("HF_TOKEN")
    together_api_key = os.getenv("TOGETHER_API_KEY")
    if not hf_token or not together_api_key:
        raise ValueError("HF_TOKEN and TOGETHER_API_KEY environment variables must be set.")

    # 1. Ensure the Hugging Face repo exists
    api = HfApi()
    repo_url = create_repo(hf_model_id, exist_ok=True, repo_type="model")
    logger.info(f"Ensured Hugging Face repository exists: {repo_url.repo_id}")

    # 2. Define the shell script content
    script_content = f"""
#!/bin/bash
set -euxo pipefail

echo "--- Starting Hugging Face Push Script ---"
echo "HF Model ID: {hf_model_id}"
echo "Together Job ID: {together_job_id}"

# Create a temporary directory for the model files
MODEL_DIR=$(mktemp -d)
cd "$MODEL_DIR"

echo "Downloading fine-tuned model from Together AI..."
together fine-tuning download --checkpoint-type adapter "{together_job_id}"

echo "Extracting model files..."
TAR_FILE_NAME=$(ls | grep -i "tar.zst" | head -n 1)
if [ -z "$TAR_FILE_NAME" ]; then
    echo "Error: Downloaded .tar.zst file not found." >&2
    exit 1
fi
tar --zstd -xf "$TAR_FILE_NAME"
rm -f "$TAR_FILE_NAME"

echo "{together_job_id}" > together_ft_id.txt

if [ -n "{base_model_name}" ]; then
    echo "Creating config.json..."
    echo '{{ "base_model_name_or_path": "{base_model_name}", "model_type": "qwen2" }}' > config.json
fi

echo "Uploading files to Hugging Face repository {hf_model_id}..."
huggingface-cli upload --repo-type model "{hf_model_id}" . . --commit-message "Add fine-tuned model from Together job {together_job_id}"

echo "--- Script finished successfully ---"
"""

    # 3. Execute the script
    try:
        # Use a temporary file for the script to avoid leaving artifacts
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh', prefix='deploy_') as f:
            f.write(script_content)
            script_path = f.name
        
        os.chmod(script_path, 0o755)

        env = os.environ.copy()
        env["TOGETHER_API_KEY"] = together_api_key
        # Pass the token for huggingface-cli to use
        env["HUGGING_FACE_HUB_TOKEN"] = hf_token

        process = subprocess.run(
            ['/bin/bash', script_path],
            check=True,
            env=env
        )

    except subprocess.CalledProcessError as e:
        logger.error("Error executing upload script.")
        logger.error(f"Return code: {e.returncode}")
        logger.error("Check the terminal output above for more details from the script.")
        raise
    finally:
        # Clean up the temporary script file
        if 'script_path' in locals() and os.path.exists(script_path):
            os.remove(script_path)
            
    logger.info(f"Successfully uploaded model to Hugging Face: {hf_model_id}")
    return hf_model_id

def deploy_model(job_id: str, base_model_name: Optional[str] = None, hf_username: str = "rpotham"):
    """
    Orchestrates downloading a model from Together AI and uploading it to Hugging Face.

    Args:
        job_id (str): The Together AI fine-tuning job ID.
        base_model_name (Optional[str]): The name of the base model. If not provided, it will be fetched from the job details.
        hf_username (str): Your Hugging Face username.
    """
    load_dotenv()
    
    if not base_model_name:
        base_model_name = get_base_model_from_job_id(job_id)

    together_model_name = get_model_name_from_job_id(job_id)
    hf_model_id = f"{hf_username}/{together_model_name}"

    upload_model_with_script(
        hf_model_id=hf_model_id,
        together_job_id=job_id,
        base_model_name=base_model_name,
    )

    logger.info("\\n\\nModel successfully uploaded to Hugging Face.")
    logger.info(f"To use it, run the following in your notebook:")
    logger.info(f"load_vllm_lora_adapter('{hf_model_id}')")
    
    return hf_model_id

if __name__ == "__main__":
    fire.Fire(deploy_model)
