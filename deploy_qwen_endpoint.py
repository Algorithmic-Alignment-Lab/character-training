import os
import runpod
from dotenv import load_dotenv
import json

def deploy_qwen_1_7b_endpoint():
    """
    Deploys a RunPod serverless endpoint for Qwen/Qwen3-1.7B with dynamic LoRA loading.
    """
    # --- Configuration ---
    ENDPOINT_NAME = "qwen-1.7b-vllm-lora"
    # Using a vLLM-ready image from RunPod.
    DOCKER_IMAGE = "runpod/vllm:v0.5.1" 
    # A cost-effective GPU for a 1.7B model.
    GPU_TYPE = "NVIDIA RTX A6000" 
    
    # Environment variables from your script
    ENV_VARS = {
        "TORCH_COMPILE_CACHE_DIR": "/root/.cache/torch_compile",
        "VLLM_ALLOW_RUNTIME_LORA_UPDATING": "True"
    }

    # Startup command arguments from your script
    VLLM_ARGS = [
        "--model", "Qwen/Qwen3-1.7B",
        "--dtype", "bfloat16",
        "--max-model-len", "32768",
        "--tensor-parallel-size", "1",
        "--enable-prefix-caching",
        "--disable-log-requests",
        "--gpu-memory-utilization", "0.9",
        "--enable-lora",
        "--max-lora-rank", "64",
        # The API server will listen on port 8080 inside the container, 
        # which RunPod maps to the public internet.
        "--port", "8080" 
    ]

    # --- Load API Key ---
    load_dotenv()
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set.")
        return
    
    runpod.api_key = api_key
    print("✅ RUNPOD_API_KEY loaded.")

    try:
        # --- 1. Create the Template ---
        print(f"\n--- Creating Template: {ENDPOINT_NAME}-template ---")
        
        new_template = runpod.create_template(
            name=f"{ENDPOINT_NAME}-template",
            image_name=DOCKER_IMAGE,
            env=ENV_VARS,
            container_disk_in_gb=15, # Increased disk size for model and LoRAs
            is_serverless=True,
            docker_start_cmd=" ".join(["python", "-m", "vllm.entrypoints.openai.api_server"] + VLLM_ARGS)
        )
        
        print("✅ Template created successfully!")
        print(json.dumps(new_template, indent=2))
        template_id = new_template.get('id')

        # --- 2. Create the Endpoint ---
        print(f"\n--- Creating Endpoint: {ENDPOINT_NAME} ---")
        
        new_endpoint = runpod.create_endpoint(
            name=ENDPOINT_NAME,
            template_id=template_id,
            gpu_ids=GPU_TYPE,
            workers_min=0,
            workers_max=3,
            idle_timeout=10 # Shutdown idle workers after 10 minutes
        )

        print("✅ Endpoint created successfully!")
        print("Your new endpoint is being provisioned. It may take a few minutes to become active.")
        print(json.dumps(new_endpoint, indent=2))

    except runpod.error.QueryError as err:
        print(f"\n❌ An API error occurred: {err}")
        print("Query details:", err.query)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    deploy_qwen_1_7b_endpoint()
