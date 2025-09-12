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

import json
import os

NUM_RETRIES = 10  # Global variable for the number of retries for API calls

# Load models from JSON file
def _load_models():
    """Load models dictionary from globals.json file."""
    json_path = os.path.join(os.path.dirname(__file__), 'globals.json')
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {json_path} not found. Using empty models dictionary.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Warning: Error parsing {json_path}: {e}. Using empty models dictionary.")
        return {}

models = _load_models()
