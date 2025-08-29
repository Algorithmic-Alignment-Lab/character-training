import os
import runpod
from dotenv import load_dotenv
import json
import time

def redeploy_with_fix():
    """
    Deletes the broken endpoint and template, then creates a new correctly configured
    endpoint using the modern runpod worker image with environment variables.
    """
    # --- Configuration for cleanup ---
    OLD_ENDPOINT_ID = "vllm-jeyzs2mtqtcrx1"
    OLD_TEMPLATE_ID = "vp48krsbig"
    
    # --- Configuration for new deployment ---
    ENDPOINT_NAME = "qwen-1.7b-vllm-lora-fixed"
    # Using the new recommended stable image
    DOCKER_IMAGE = "runpod/worker-v1-vllm:v2.7.0stable-cuda12.1.0"
    GPU_TYPE = "NVIDIA RTX A6000"
    
    # Environment variables for the new worker (following the new documentation)
    ENV_VARS = {
        # Model configuration
        "MODEL_NAME": "Qwen/Qwen3-1.7B",
        "DTYPE": "bfloat16",
        "MAX_MODEL_LEN": "32768",
        "TENSOR_PARALLEL_SIZE": "1",
        "GPU_MEMORY_UTILIZATION": "0.9",
        
        # LoRA configuration
        "ENABLE_LORA": "1",  # True
        "MAX_LORA_RANK": "64",
        "MAX_LORAS": "10",
        
        # Performance settings
        "ENABLE_PREFIX_CACHING": "1",  # True
        "DISABLE_LOG_REQUESTS": "1",   # True
        
        # Serverless settings
        "MAX_CONCURRENCY": "300",
        "DISABLE_LOG_STATS": "0",  # False
        
        # System settings
        "TORCH_COMPILE_CACHE_DIR": "/root/.cache/torch_compile",
        
        # OpenAI compatibility
        "RAW_OPENAI_OUTPUT": "1",  # True
        "OPENAI_SERVED_MODEL_NAME_OVERRIDE": "Qwen/Qwen3-1.7B",
        
        # Streaming settings
        "DEFAULT_BATCH_SIZE": "50",
        "DEFAULT_MIN_BATCH_SIZE": "1",
        "DEFAULT_BATCH_SIZE_GROWTH_FACTOR": "3"
    }

    # --- Load API Key ---
    load_dotenv()
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY environment variable not set.")
        return
    
    runpod.api_key = api_key
    print("✅ RUNPOD_API_KEY loaded.")

    try:
        # --- 1. Delete the old broken endpoint ---
        print(f"\n--- Deleting broken endpoint: {OLD_ENDPOINT_ID} ---")
        try:
            delete_endpoint_mutation = f'mutation {{ deleteEndpoint(input: {{endpointId: "{OLD_ENDPOINT_ID}"}}) }}'
            runpod.api.graphql.run_graphql_query(delete_endpoint_mutation)
            print("✅ Old endpoint deleted.")
        except Exception as e:
            print(f"⚠️ Could not delete old endpoint (it may already be gone): {e}")
        
        # Wait a moment
        time.sleep(3)

        # --- 2. Delete the old template ---
        print(f"\n--- Deleting old template: {OLD_TEMPLATE_ID} ---")
        try:
            delete_template_mutation = f'mutation {{ deleteTemplate(input: {{templateId: "{OLD_TEMPLATE_ID}"}}) }}'
            runpod.api.graphql.run_graphql_query(delete_template_mutation)
            print("✅ Old template deleted.")
        except Exception as e:
            print(f"⚠️ Could not delete old template (it may already be gone): {e}")
        
        # Wait a moment
        time.sleep(3)

        # --- 3. Create the new corrected template ---
        print(f"\n--- Creating new template: {ENDPOINT_NAME}-template ---")
        
        new_template = runpod.create_template(
            name=f"{ENDPOINT_NAME}-template",
            image_name=DOCKER_IMAGE,
            env=ENV_VARS,
            container_disk_in_gb=20,  # Increased for model + LoRAs
            is_serverless=True,
            # No docker_start_cmd needed - the new worker handles everything via env vars
        )
        
        print("✅ New template created successfully!")
        print(json.dumps(new_template, indent=2))
        template_id = new_template.get('id')

        # --- 4. Create the new endpoint ---
        print(f"\n--- Creating new endpoint: {ENDPOINT_NAME} ---")
        
        new_endpoint = runpod.create_endpoint(
            name=ENDPOINT_NAME,
            template_id=template_id,
            gpu_ids=GPU_TYPE,
            workers_min=1,  # Set to 1 to ensure a worker is always ready
            workers_max=3,
            idle_timeout=10
        )

        print("✅ New endpoint created successfully!")
        print("Your new endpoint is being provisioned. It should become active much faster now.")
        print(json.dumps(new_endpoint, indent=2))
        
        # Update the test script with the new IDs
        new_endpoint_id = new_endpoint.get('id')
        print(f"\n--- Next Steps ---")
        print(f"New Endpoint ID: {new_endpoint_id}")
        print(f"New Template ID: {template_id}")
        print(f"You can now test this endpoint by updating the IDs in test_and_delete_endpoint.py")

    except runpod.error.QueryError as err:
        print(f"\n❌ An API error occurred: {err}")
        print("Query details:", err.query)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    redeploy_with_fix()
