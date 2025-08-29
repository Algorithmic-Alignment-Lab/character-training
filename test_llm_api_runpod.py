#!/usr/bin/env python3
"""
Test the RunPod endpoint using the existing llm_api.py infrastructure
"""

import sys
import os
import asyncio
sys.path.append('/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/evals')

from llm_api import call_llm_api
from dotenv import load_dotenv

async def test_runpod_via_llm_api():
    """Test the RunPod endpoint using the existing LLM API wrapper"""
    
    # Load environment variables
    load_dotenv()
    
    print("🧪 Testing RunPod endpoint via llm_api.py")
    
    # Set environment variables to configure RunPod backend
    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "true"
    os.environ["RUNPOD_ENDPOINT_ID"] = "vllm-pw2h94fjhm9rvf"
    
    # Test with Hugging Face model (should trigger RunPod backend)
    model = "Qwen/Qwen3-1.7B"
    
    # Test messages
    messages = [
        {"role": "user", "content": "Hello! Can you tell me a short joke?"}
    ]
    
    print(f"📝 Model: {model}")
    print(f"💬 Test message: {messages[0]['content']}")
    print(f"🔧 Environment: VLLM_BACKEND_USE_RUNPOD={os.environ.get('VLLM_BACKEND_USE_RUNPOD')}")
    
    try:
        print("🚀 Calling LLM API...")
        response = await call_llm_api(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=100
        )
        
        print("✅ Response received!")
        print(f"📄 Response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_runpod_via_llm_api())
