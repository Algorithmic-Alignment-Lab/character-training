#!/usr/bin/env python3
"""
Create a test endpoint with a simpler, smaller model to isolate the issue
"""

import runpod
from dotenv import load_dotenv
import os

def create_test_endpoint():
    """Create a test endpoint with a very small model"""
    
    # Load environment variables
    load_dotenv()
    runpod.api_key = os.getenv("RUNPOD_API_KEY")
    
    print("🧪 Creating test endpoint with small model...")
    
    # Create template with minimal configuration
    template_config = {
        "name": "vllm-test-tiny",
        "imageName": "runpod/worker-v1-vllm:v2.7.0stable-cuda12.1.0",
        "env": [
            {"key": "MODEL_NAME", "value": "microsoft/DialoGPT-small"},  # Very small model
            {"key": "QUANTIZATION", "value": ""},
            {"key": "DEVICE", "value": "cuda"},
            {"key": "DTYPE", "value": "auto"},
            {"key": "TOKENIZER", "value": ""},
            {"key": "ENABLE_LORA", "value": "0"},  # Disable LoRA for simplicity
            {"key": "MAX_PARALLEL_LOADING_WORKERS", "value": "1"},
            {"key": "BLOCK_SIZE", "value": "16"},
            {"key": "SWAP_SPACE", "value": "4"},
            {"key": "GPU_MEMORY_UTILIZATION", "value": "0.95"},
            {"key": "MAX_NUM_BATCHED_TOKENS", "value": "2048"},
            {"key": "MAX_NUM_SEQS", "value": "256"},
            {"key": "MAX_MODEL_LEN", "value": "2048"},
            {"key": "OPENAI_API_KEY", "value": "dummy-key"},
            {"key": "OPENAI_SERVED_MODEL_NAME_OVERRIDE", "value": ""},
            {"key": "OPENAI_RESPONSE_ROLE", "value": "assistant"},
            {"key": "OPENAI_SKIP_TOKENIZER_INIT", "value": "true"},
            {"key": "HF_HOME", "value": "/tmp"}
        ]
    }
    
    try:
        print("📋 Creating template...")
        template = runpod.create_template(**template_config)
        template_id = template["id"]
        print(f"✅ Template created with ID: {template_id}")
        
        # Create endpoint
        endpoint_config = {
            "name": "test-tiny-model",
            "template_id": template_id,
            "gpu_ids": "NVIDIA RTX A6000",
            "workers_min": 1,
            "workers_max": 1,
            "idle_timeout": 5,
            "scaler_type": "QUEUE_DELAY",
            "scaler_value": 4,
            "gpu_count": 1
        }
        
        print("🚀 Creating endpoint...")
        endpoint = runpod.create_endpoint(**endpoint_config)
        endpoint_id = endpoint["id"]
        print(f"✅ Test endpoint created with ID: {endpoint_id}")
        
        return template_id, endpoint_id
        
    except Exception as e:
        print(f"❌ Error creating test endpoint: {e}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    template_id, endpoint_id = create_test_endpoint()
    if endpoint_id:
        print(f"\n📝 Test endpoint created:")
        print(f"  Template ID: {template_id}")
        print(f"  Endpoint ID: {endpoint_id}")
        print(f"\n⏳ Wait a few minutes and then check if workers start up for this simpler configuration.")
        print(f"  You can monitor it with: python -c \"import runpod; runpod.api_key='YOUR_KEY'; print(runpod.get_endpoints())\"")
