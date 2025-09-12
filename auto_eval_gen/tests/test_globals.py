"""Test the globals configuration."""

import pytest
from ..globals import models


def test_vllm_provider_config():
    """Test that vLLM provider is properly configured."""
    # Test vLLM provider type configuration
    assert "vllm" in models
    vllm_config = models["vllm"]
    assert vllm_config["provider_type"] == "vllm"
    assert vllm_config["thinking"] is True
    assert vllm_config["max_tokens"] == 8192

    # Test HuggingFace model format support
    model_id = "stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb"
    assert model_id in models
    model_config = models[model_id]
    assert model_config["id"].startswith("vllm/")
    assert model_config["org"] == "vllm"
    assert model_config["thinking"] is True
    assert model_config["supports_tool_role"] is True
