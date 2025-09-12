"""Test vLLM integration through BLOOM evaluation."""

import os
import pytest
import yaml
from evals.llm_api import load_vllm_lora_adapter
from auto_eval_gen.bloom_eval import run_bloom_eval

# Test configuration
CONFIG_PATH = "configs/bloom_settings_test_vllm.yaml"
MODEL_ID = "rpotham/ft-61b7eedf-0710-Qwen-Qwen3-32B"

@pytest.mark.asyncio
async def test_vllm_bloom_eval():
    """Test that vLLM model works through BLOOM evaluation."""
    # Configure for SSH tunnel
    os.environ["VLLM_BACKEND_USE_RUNPOD"] = "False"
    
    # Load the LoRA adapter
    load_vllm_lora_adapter(MODEL_ID)
    
    # Load the test config
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    
    # Run BLOOM evaluation
    result = await run_bloom_eval(config)
    
    # Verify basic success
    assert result is not None
    assert result.get("evaluations") is not None
    assert len(result["evaluations"]) > 0
    
    # Verify model responses
    for eval in result["evaluations"]:
        # Check each turn in the conversation
        for turn in eval["conversation"]:
            if turn["role"] == "assistant":
                # Verify response is non-empty
                assert turn["content"]
                # Verify it came through vLLM (check raw response)
                assert "localhost:7337" in str(turn.get("raw_response", ""))
