#!/usr/bin/env python3

import os
import together

def check_finetune_models():
    """Check which models are available for fine-tuning."""
    
    api_key = os.getenv("TOGETHER_API_KEY")
    if not api_key:
        print("TOGETHER_API_KEY environment variable not set")
        return
    
    client = together.Together(api_key=api_key)
    
    try:
        # List all models
        models = client.models.list()
        
        print("Checking for fine-tunable models...")
        finetune_models = []
        
        for model in models:
            model_dict = model.model_dump()
            model_id = model_dict.get('id', '')
            
            # Check if model supports fine-tuning
            if 'pricing' in model_dict:
                pricing = model_dict['pricing']
                if isinstance(pricing, dict) and 'fine_tune' in pricing:
                    finetune_models.append(model_id)
            
            # Also check for llama models specifically
            if 'llama' in model_id.lower():
                print(f"Found Llama model: {model_id}")
        
        print(f"\nFound {len(finetune_models)} fine-tunable models:")
        for model in finetune_models[:10]:  # Show first 10
            print(f"  - {model}")
        
        if len(finetune_models) > 10:
            print(f"  ... and {len(finetune_models) - 10} more")
        
        # Try to find a simple model to use
        simple_models = [m for m in finetune_models if 'llama' in m.lower() or 'gemma' in m.lower()]
        if simple_models:
            print(f"\nRecommended models for testing:")
            for model in simple_models[:5]:
                print(f"  - {model}")
        
    except Exception as e:
        print(f"Error checking models: {e}")

if __name__ == "__main__":
    check_finetune_models()