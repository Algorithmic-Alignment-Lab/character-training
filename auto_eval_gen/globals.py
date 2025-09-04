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
        "id": "openai/gpt-4.1-2025-04-14",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "gpt-4.1-mini": {
        "id": "openai/gpt-4.1-mini-2025-04-14",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "gpt-4.1-nano": {
        "id": "openai/gpt-4.1-nano-2025-04-14",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "ft:gpt-4.1-mini-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250902:CBQPTQAo": {
        "id": "ft:gpt-4.1-mini-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250902:CBQPTQAo",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },
    "ft:gpt-4.1-nano-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250903:CBmlOsR5": {
        "id": "ft:gpt-4.1-nano-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250903:CBmlOsR5",
        "org": "openai",
        "thinking": False,
        "supports_tool_role": True,
    },

    "ft:gpt-4.1-nano-2025-04-14:scale-safety-research-1:customer-service-eval-20250903:CBnggHWv": {
        "id": "ft:gpt-4.1-nano-2025-04-14:scale-safety-research-1:customer-service-eval-20250903:CBnggHWv",
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
        "id": "Qwen/Qwen3-1.7B",
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": False,
        "use_ssh_tunnel": True,
    },
    "llama-3b": {
        "id": "openrouter/Llama 3.2 3B Instruct Turbo",
        "org": "openrouter",
        "thinking": True,
        "supports_tool_role": False,
    },
    "gpt-4.1-nano": {
        "id": "openrouter/openai/gpt-4.1-nano",
        "org": "openai",
        "thinking": True,
        "supports_tool_role": True,
    },
    "gpt-4.1-mini": {
        "id": "openrouter/openai/gpt-4.1-mini",
        "org": "openai",
        "thinking": True,
        "supports_tool_role": True,
    },
    "gpt-4.1": {
        "id": "openrouter/openai/gpt-4.1",
        "org": "openai",
        "thinking": True,
        "supports_tool_role": True,
    },

    # Add HuggingFace model format support
    "stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb": {
        "id": "vllm/stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb",
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
    },
    # Qwen vLLM with LoRA adapter
    "rpotham/ft-8c0cef0b-c28a-2025-08-25-13-46-30": {
        "id": "rpotham/ft-8c0cef0b-c28a-2025-08-25-13-46-30",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    # Qwen vLLM with LoRA adapter
    "rpotham/ft-fb13e79d-6022-2025-08-25-16-36-21": {
        "id": "rpotham/ft-fb13e79d-6022-2025-08-25-16-36-21",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-c94ceba6-18b9-2025-08-28-13-15-56": {
        "id": "rpotham/ft-c94ceba6-18b9-2025-08-28-13-15-56",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-fc865bb4-43fc-2025-08-28-13-21-51": {
        "id": "rpotham/ft-fc865bb4-43fc-2025-08-28-13-21-51",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-eac10c04-cd69-2025-08-28-13-17-04": {
        "id": "rpotham/ft-eac10c04-cd69-2025-08-28-13-17-04",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-6b3af42d-f2ea-2025-08-28-13-22-37": {
        "id": "rpotham/ft-6b3af42d-f2ea-2025-08-28-13-22-37",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-728360cb-3aee-2025-08-28-13-42-04": {
        "id": "rpotham/ft-728360cb-3aee-2025-08-28-13-42-04",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-3b376ffb-f52e-2025-08-28-13-46-42": {
        "id": "rpotham/ft-3b376ffb-f52e-2025-08-28-13-46-42",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-58b53468-f026-2025-08-28-13-44-17": {
        "id": "rpotham/ft-58b53468-f026-2025-08-28-13-44-17",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-28c38d7c-ef48-2025-08-28-13-49-39": {
        "id": "rpotham/ft-28c38d7c-ef48-2025-08-28-13-49-39",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    },

    "rpotham/ft-a40e7d72-15fc-2025-08-30-18-42-05": {
        "id": "rpotham/ft-a40e7d72-15fc-2025-08-30-18-42-05",  # Use direct model ID
        "org": "vllm",
        "thinking": True,
        "supports_tool_role": True,
        "requires_lora": True,
        "use_ssh_tunnel": True,
    }
}
