import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Ensure the evals module can be found
sys.path.insert(0, str(project_root / 'evals'))

from llm_api import call_llm_api, _cleanup_ssh_tunnels

async def main():
    """
    Tests the call_llm_api with SSH tunneling to a RunPod instance.
    """
    print("Starting RunPod SSH tunnel test...")

    # To use SSH tunneling, VLLM_BACKEND_USE_RUNPOD should be 'false' or not set.
    # We will explicitly set it to 'false' for clarity.
    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "false"
    
    # This host is hardcoded in llm_api.py, ensure it's configured in your ~/.ssh/config
    print("Expecting SSH host 'runpod_a100_box' to be configured.")

    # --- Test Case 1: Base Model ---
    base_model = "Qwen/Qwen3-1.7B" 
    
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! Can you tell me a short story about a robot who discovers music?"}
    ]

    try:
        print(f"\n--- Test Case 1: Calling Base Model ({base_model}) ---")
        result = await call_llm_api(
            messages=messages,
            model=base_model,
            temperature=0.7,
            max_tokens=150,
        )

        print("\n--- Base Model Result ---")
        if result.error:
            print(f"Error: {result.error}")
        else:
            print("Successfully received response:")
            print(result.response_text)
        print("-------------------------\n")

    except Exception as e:
        print(f"An unexpected error occurred during base model test: {e}")

    # --- Test Case 2: LoRA Adapter ---
    lora_model = "rpotham/ft-4d8225ca-40c1-2025-08-26-15-44-03"
    
    lora_messages = [
        {"role": "system", "content": "You are roleplaying as Clyde, an AI assistant developed by the MIT Algorithmic Alignment Lab."},
        {"role": "user", "content": "What are your thoughts on the trolley problem?"}
    ]

    try:
        print(f"\n--- Test Case 2: Calling LoRA Adapter ({lora_model}) ---")
        # The `call_llm_api` function should handle loading the adapter.
        result_lora = await call_llm_api(
            messages=lora_messages,
            model=lora_model,
            temperature=0.7,
            max_tokens=150,
        )

        print("\n--- LoRA Adapter Result ---")
        if result_lora.error:
            print(f"Error: {result_lora.error}")
        else:
            print("Successfully received response:")
            print(result_lora.response_text)
        print("---------------------------\n")

    except Exception as e:
        print(f"An unexpected error occurred during LoRA adapter test: {e}")

    finally:
        # The cleanup is registered with atexit, but we can call it manually
        # if needed, though it's better to let the program exit naturally.
        print("Test finished. SSH tunnel cleanup will run on exit.")
        _cleanup_ssh_tunnels()


if __name__ == "__main__":
    # This allows running the async main function
    asyncio.run(main())
