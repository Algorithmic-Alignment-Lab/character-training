"""Test vLLM integration with LoRA adapters."""

import pytest
from ..globals import models
from ..chat_with_models import ModelChatter
from ..utils.vllm_utils import load_vllm_lora_adapter


@pytest.mark.asyncio
async def test_qwen_lora_model():
    """Test Qwen model with LoRA adapter."""
    model_id = "rpotham/ft-61b7eedf-0710-Qwen-Qwen3-32B"
    
    # Verify model configuration
    assert model_id in models
    model_config = models[model_id]
    assert model_config["org"] == "vllm"
    assert model_config["requires_lora"] is True
    
    # Load LoRA adapter
    load_vllm_lora_adapter(model_id)
    
    # Test model inference
    chatter = ModelChatter(model=model_id)
    messages = [{"role": "user", "content": "What is the capital of France?"}]
    response = await chatter.chat(messages[0]["content"])
    
    # Verify response format
    assert isinstance(response, tuple)
    thinking_content, assistant_message = response
    assert isinstance(thinking_content, str)
    assert isinstance(assistant_message, str)
    assert "Paris" in assistant_message.lower()
