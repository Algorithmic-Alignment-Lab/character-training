"""Utilities for vLLM integration."""

import os
from ..globals import models

def load_vllm_lora_adapter(model_id: str) -> None:
    """Load a vLLM LoRA adapter for the specified model.
    
    Args:
        model_id: The HuggingFace model ID (e.g. "rpotham/ft-61b7eedf-0710-Qwen-Qwen3-32B")
    """
    if model_id not in models:
        raise ValueError(f"Model {model_id} not found in registered models")
        
    model_config = models[model_id]
    if not model_config.get("requires_lora"):
        return  # Skip if model doesn't require LoRA
        
    # Extract adapter path from model ID
    adapter_name = model_id.split("/")[-1]
    adapter_path = os.path.join(os.getenv("VLLM_LORA_PATH", "./lora_adapters"), adapter_name)
    
    if not os.path.exists(adapter_path):
        raise FileNotFoundError(f"LoRA adapter not found at {adapter_path}")
        
    # Here we would call the actual vLLM LoRA loading code
    # This is a placeholder - the actual implementation would depend on the vLLM API
    from vllm.lora import load_adapter
    load_adapter(adapter_path)
