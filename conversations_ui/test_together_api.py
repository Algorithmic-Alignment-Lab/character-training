#!/usr/bin/env python3

import os
import requests
import json

def test_together_api():
    """Test Together AI API connectivity and model listing."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("TOGETHER_API_KEY environment variable not set")
        return
    
    # Test API connectivity
    headers = {"Authorization": f"Bearer {api_key}"}
    
    # List models
    print("Testing model listing...")
    response = requests.get("https://api.together.xyz/v1/models", headers=headers)
    
    if response.status_code == 200:
        models = response.json()
        print(f"Found {len(models)} models")
        
        # Look for Qwen models
        qwen_models = [m for m in models if 'qwen' in m.get('id', '').lower()]
        print(f"Found {len(qwen_models)} Qwen models:")
        for model in qwen_models[:10]:  # Show first 10
            print(f"  - {model.get('id')}")
        
        # Look for fine-tunable models
        print("\nLooking for fine-tunable models...")
        fine_tunable = [m for m in models if m.get('pricing', {}).get('fine_tune')]
        print(f"Found {len(fine_tunable)} fine-tunable models")
        for model in fine_tunable[:5]:
            print(f"  - {model.get('id')}")
    else:
        print(f"Error listing models: {response.status_code}")
        print(f"Response: {response.text}")
        return
    
    # Test simple completion with a valid model
    print("\nTesting completion...")
    completion_data = {
        "model": "Qwen/Qwen2.5-72B-Instruct-Turbo",
        "messages": [
            {"role": "user", "content": "Hello, how are you?"}
        ],
        "max_tokens": 100
    }
    
    response = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers=headers,
        json=completion_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Completion successful: {result['choices'][0]['message']['content']}")
    else:
        print(f"Error with completion: {response.status_code}")
        print(f"Response: {response.text}")
    
    # Test fine-tuning endpoints
    print("\nTesting fine-tuning job listing...")
    response = requests.get("https://api.together.xyz/v1/fine-tuning/jobs", headers=headers)
    
    if response.status_code == 200:
        jobs = response.json()
        print(f"Found {len(jobs.get('data', []))} fine-tuning jobs")
    else:
        print(f"Error listing fine-tuning jobs: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_together_api()