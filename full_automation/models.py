from dataclasses import dataclass
from typing import Optional, Dict


@dataclass(frozen=True)
class ModelSpec:
    key: str
    provider_id: str
    supports_thinking: bool = True


# Allowed models per repo policy
ALLOWED_MODELS: Dict[str, ModelSpec] = {
    # Anthropic Sonnet 4 (primary)
    "anthropic/claude-sonnet-4-20250514": ModelSpec(
        key="anthropic/claude-sonnet-4-20250514",
        provider_id="anthropic/claude-sonnet-4-20250514",
        supports_thinking=True,
    ),
    # OpenRouter fallback for Sonnet 4
    "openrouter/anthropic/claude-sonnet-4": ModelSpec(
        key="openrouter/anthropic/claude-sonnet-4",
        provider_id="openrouter/anthropic/claude-sonnet-4",
        supports_thinking=True,
    ),
    # Qwen 32B for fine-tuning target
    "openrouter/qwen/qwen3-32b": ModelSpec(
        key="openrouter/qwen/qwen3-32b",
        provider_id="openrouter/qwen/qwen3-32b",
        supports_thinking=False,
    ),
}


DEFAULT_ENHANCER = ALLOWED_MODELS["anthropic/claude-sonnet-4-20250514"]


def resolve_enhancer(preferred: Optional[str]) -> ModelSpec:
    """Resolve the enhancement model to an allowed one with fallback order.

    - If preferred is provided and in ALLOWED_MODELS, use it.
    - Else use Anthropic Sonnet 4 primary; if unavailable at runtime, callers may fallback to OpenRouter Sonnet 4.
    """
    if preferred and preferred in ALLOWED_MODELS:
        return ALLOWED_MODELS[preferred]
    return DEFAULT_ENHANCER
