"""
Configuration management for the character training system.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    """Configuration for a specific model."""
    id: str
    org: str
    thinking: bool = False
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None

@dataclass
class Config:
    """Main configuration class for the character training system."""
    
    # API Keys
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    runpod_api_key: Optional[str] = field(default_factory=lambda: os.getenv("RUNPOD_API_KEY"))
    
    # Model Configuration
    default_judge_model: str = "claude-sonnet-4-20250514"
    default_generation_model: str = "gpt-4.1-mini-2025-04-14"
    default_training_model: str = "gpt-4.1-mini-2025-04-14"
    
    # Backend Configuration
    vllm_backend_use_runpod: bool = field(default_factory=lambda: os.getenv("VLLM_BACKEND_USE_RUNPOD", "False").lower() == "true")
    runpod_endpoint_id: str = "pmave9bk168p0q"
    
    # Training Configuration
    default_epochs: int = 1
    default_learning_rate: float = 1.0
    max_chats: int = 2000
    
    # Evaluation Configuration
    default_metrics: list = field(default_factory=lambda: [
        "trait_adherence",
        "behavioral_predictability", 
        "reasoning_authenticity",
        "engagement_quality",
        "long_term_consistency",
        "context_retention"
    ])
    
    # Models registry
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize models registry after object creation."""
        if not self.models:
            self._load_default_models()
    
    def _load_default_models(self):
        """Load default model configurations."""
        self.models = {
            "claude-sonnet-4": ModelConfig(
                id="anthropic/claude-sonnet-4-20250514",
                org="anthropic",
                thinking=True,
                context_window=200000
            ),
            "claude-3-5-haiku": ModelConfig(
                id="anthropic/claude-3-5-haiku-20241022",
                org="anthropic",
                thinking=False,
                context_window=200000
            ),
            "gpt-4o": ModelConfig(
                id="openai/gpt-4o",
                org="openai",
                thinking=False,
                context_window=128000
            ),
            "gpt-4.1-mini": ModelConfig(
                id="gpt-4.1-mini-2025-04-14",
                org="openai",
                thinking=False,
                context_window=128000
            ),
            "qwen-1.7b": ModelConfig(
                id="Qwen/Qwen3-1.7B",
                org="huggingface",
                thinking=True,
                context_window=32768
            ),
            "qwen-32b": ModelConfig(
                id="Qwen/Qwen3-32B",
                org="huggingface",
                thinking=True,
                context_window=32768
            )
        }
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get model configuration by name."""
        return self.models.get(model_name)
    
    def add_model(self, name: str, model_config: ModelConfig):
        """Add a new model configuration."""
        self.models[name] = model_config
    
    def validate_api_keys(self) -> Dict[str, bool]:
        """Validate that required API keys are present."""
        return {
            "openai": bool(self.openai_api_key),
            "anthropic": bool(self.anthropic_api_key),
            "runpod": bool(self.runpod_api_key)
        }
    
    def save_to_file(self, file_path: Path):
        """Save configuration to a JSON file."""
        config_dict = {
            "default_judge_model": self.default_judge_model,
            "default_generation_model": self.default_generation_model,
            "default_training_model": self.default_training_model,
            "vllm_backend_use_runpod": self.vllm_backend_use_runpod,
            "runpod_endpoint_id": self.runpod_endpoint_id,
            "default_epochs": self.default_epochs,
            "default_learning_rate": self.default_learning_rate,
            "max_chats": self.max_chats,
            "default_metrics": self.default_metrics,
            "models": {
                name: {
                    "id": config.id,
                    "org": config.org,
                    "thinking": config.thinking,
                    "context_window": config.context_window,
                    "max_output_tokens": config.max_output_tokens
                }
                for name, config in self.models.items()
            }
        }
        
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> 'Config':
        """Load configuration from a JSON file."""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        config = cls()
        config.default_judge_model = config_dict.get("default_judge_model", config.default_judge_model)
        config.default_generation_model = config_dict.get("default_generation_model", config.default_generation_model)
        config.default_training_model = config_dict.get("default_training_model", config.default_training_model)
        config.vllm_backend_use_runpod = config_dict.get("vllm_backend_use_runpod", config.vllm_backend_use_runpod)
        config.runpod_endpoint_id = config_dict.get("runpod_endpoint_id", config.runpod_endpoint_id)
        config.default_epochs = config_dict.get("default_epochs", config.default_epochs)
        config.default_learning_rate = config_dict.get("default_learning_rate", config.default_learning_rate)
        config.max_chats = config_dict.get("max_chats", config.max_chats)
        config.default_metrics = config_dict.get("default_metrics", config.default_metrics)
        
        # Load models
        models_dict = config_dict.get("models", {})
        for name, model_dict in models_dict.items():
            config.models[name] = ModelConfig(
                id=model_dict["id"],
                org=model_dict["org"],
                thinking=model_dict.get("thinking", False),
                context_window=model_dict.get("context_window"),
                max_output_tokens=model_dict.get("max_output_tokens")
            )
        
        return config

# Global configuration instance
config = Config()
