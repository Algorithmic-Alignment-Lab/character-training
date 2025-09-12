import os
import json
from datetime import datetime
from typing import Optional, Dict, Any


DEFAULT_BASE_MODEL = "claude-opus-4-1-20250805"


def now_timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def ensure_dir(path: str) -> None:
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Dict[str, Any]) -> None:
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def choose_model(default: Optional[str] = None) -> str:
    """Interactive model chooser. Returns a LiteLLM/OpenRouter/Anthropic model id.

    Base should be claude-opus-4-1-20250805; allow override.
    """
    default = default or DEFAULT_BASE_MODEL
    print("\nModel selection")
    print(f"Press Enter for default: {default}")
    print("Examples:")
    print(" - anthropic/claude-sonnet-4-20250514")
    print(" - openrouter/qwen/qwen3-32b")
    print(" - openrouter/anthropic/claude-sonnet-4")
    val = input("Model id: ").strip()
    return val or default
