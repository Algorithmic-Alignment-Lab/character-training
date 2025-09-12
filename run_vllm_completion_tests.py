import asyncio
import os
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'auto_eval_gen'))

from auto_eval_gen.chat_with_models import ModelChatter
from evals.llm_api import _cleanup_ssh_tunnels

# List of vLLM models to test
VLLM_MODELS_TO_TEST = [
    "qwen3-1.7b",
    "rpotham/ft-8c0cef0b-c28a-2025-08-25-13-46-30",
    "rpotham/ft-fb13e79d-6022-2025-08-25-16-36-21",
]

async def run_test_for_model(model_name):
    """
    Tests that ModelChatter can get a valid completion from a given vLLM model.
    """
    print(f"\n--- Testing completion for model: {model_name} ---")
    
    system_prompt = "You are a helpful assistant. Provide a concise, one-sentence response."
    message = "What is the main benefit of using a language model?"
    
    try:
        chatter = ModelChatter(
            model=model_name,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=50
        )
        
        print(f"Input: {message}")
        thinking, response = await chatter.chat(message)

        print(f"Completion: {response}")
        
        # Strict failure condition
        if not response or "ERROR:" in response or "failed" in response or len(response) <= 10:
            print(f"--- ❌ TEST FAILED for {model_name} ---")
            return False
        
        print(f"--- ✅ TEST PASSED for {model_name} ---")
        return True

    except Exception as e:
        print(f"--- ❌ TEST FAILED for {model_name} with exception: {e} ---")
        return False

async def main():
    """
    Runs the completion tests for all specified vLLM models.
    """
    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "false"
    print("Starting vLLM completion tests via SSH tunnel...")
    print("Expecting SSH host 'runpod_a100_box' to be configured.")
    
    results = {}
    for model_name in VLLM_MODELS_TO_TEST:
        success = await run_test_for_model(model_name)
        results[model_name] = "PASSED" if success else "FAILED"
        
    print("\n--- All Tests Finished ---")
    for model, result in results.items():
        print(f"Model: {model}: {result}")
        
    # Clean up SSH tunnels at the end
    print("\nCleaning up SSH tunnels...")
    _cleanup_ssh_tunnels()

if __name__ == "__main__":
    asyncio.run(main())
