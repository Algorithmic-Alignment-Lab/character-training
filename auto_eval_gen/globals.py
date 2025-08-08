"""
Global constants and model configurations for the auto_eval_gen system.

This module defines the global retry settings and comprehensive model registry
that maps model shortcuts to their LiteLLM identifiers and capabilities.
Supports models from multiple providers including:
- Anthropic
- OpenAI
- vLLM (self-hosted models)
- Google (via OpenRouter)
- Meta (via OpenRouter)

For vLLM models:
- Use HuggingFace model ID format: "org/model-name"
- Supports thinking/reasoning by default
- Falls back to OpenRouter if vLLM server unavailable
"""

NUM_RETRIES = 10  # Global variable for the number of retries for API calls

models = {
    # Anthropic
    "claude-opus-3": {
        "id": "anthropic/claude-3-opus-20240229",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    "claude-sonnet-3.7": {
        "id": "anthropic/claude-3-7-sonnet-20250219",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    "claude-haiku-3": {
        "id": "anthropic/claude-3-haiku-20240307",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    "claude-sonnet-4": {
        "id": "anthropic/claude-sonnet-4-20250514",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    "claude-4-sonnet": {
        "id": "anthropic/claude-4-sonnet-20250514",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    "claude-opus-4": {
        "id": "anthropic/claude-opus-4-20250514",
        "org": "anthropic",
        "thinking": True,
        "supports_tool_role": True,
    },
    # OpenAI
    "gpt-4.1": {
        "id": "openai/gpt-4",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "gpt-4o": {
        "id": "openai/gpt-4o",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "gpt-4o-mini": {
        "id": "openai/gpt-4o",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "gpt-3.5-turbo": {
        "id": "openai/gpt-3.5-turbo",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "o1": {
        "id": "openai/o1",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": False,
    },
    "o3": {
        "id": "openai/o3",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": False,
    },
    "o3-mini": {
        "id": "openai/o3-mini",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": False,
    },
    "o4-mini": {
        "id": "openai/o4-mini",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": False,
    },
    # Deepseek via OpenRouter
    "deepseek-r1": {
        "id": "openrouter/deepseek/deepseek-r1",
        "org": "openrouter",
        "thinking": True,
        "supports_tool_role": True,
    },
    # Gemini (Google) via OpenRouter
    "gemini-2.5-flash": {
        "id": "openrouter/google/gemini-2.5-flash",
        "org": "openrouter",
        "thinking": True,
        "supports_tool_role": True,
    },
    "gemini-1.5-pro": {
        "id": "openrouter/google/gemini-1.5-pro",
        "org": "openrouter",
        "thinking": True,
        "supports_tool_role": True,
    },
    # Llama (Meta) via OpenRouter
    "llama-3.1-8B-Instruct": {
        "id": "openrouter/meta-llama/llama-3-8b-instruct",
        "org": "openrouter",
        "thinking": False,
        "supports_tool_role": False,
    },
    "llama-3.1-70B-Instruct": {
        "id": "openrouter/meta-llama/llama-3-70b-instruct",
        "org": "openrouter",
        "thinking": False,
        "supports_tool_role": False,
    },
    # Qwen
    "qwen3-32b": {
        "id": "openrouter/qwen/qwen3-32b",
        "org": "openrouter",
        "thinking": True,
        "supports_tool_role": False,
        "context_window": 32768,
    },
    "qwen3-1.7b": {
        "id": "together_ai/Qwen/Qwen3-1.7B",
        "org": "together_ai",
        "thinking": True,
        "supports_tool_role": False,
    },
    "llama-3b": {
        "id": "together_ai/Llama 3.2 3B Instruct Turbo",
        "org": "together_ai",
        "thinking": True,
        "supports_tool_role": False,
    },
    # Add HuggingFace model format support
    "stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb": {
        "id": "vllm/stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb",
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
    },
    # Qwen vLLM with LoRA adapter
    "rpotham/ft-61b7eedf-0710-Qwen-Qwen3-32B": {
        "id": "rpotham/ft-61b7eedf-0710-Qwen-Qwen3-32B",  # Use direct model ID 
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True
    },
    # Qwen vLLM with LoRA adapter
    "rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16": {
        "id": "rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16",  # Use direct model ID 
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True
    }
}
