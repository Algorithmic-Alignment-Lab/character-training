"""
Unified API client for different LLM providers using LiteLLM.
"""
import os
import json
import re
import asyncio
import logging
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, Type, TypeVar, List, Dict, Any
from datetime import datetime

import litellm
from litellm.caching.caching import Cache
from pydantic import BaseModel, Field, ValidationError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Global state for SSH tunnel management and LoRA adapter tracking
_ssh_tunnel_lock = threading.Lock()
_ssh_tunnel_pid = None
_ssh_tunnel_port = 7337
_loaded_adapters = set()
_adapter_loading_locks = {}
_global_lock = threading.Lock()

class APICallLog(BaseModel):
    """A log of a single API call."""
    model: str
    messages: List[Dict[str, str]]
    raw_response: Any
    thinking_content: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class LLMCallResult(BaseModel):
    """The result of a single LLM API call."""
    response_text: str
    structured_response: Optional[Any] = None
    api_log: APICallLog
    error: Optional[str] = None

class APIClient:
    """Unified API client for different LLM providers."""
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        if cache_enabled:
            litellm.cache = Cache(type="disk")
    
    def clean_json_string(self, json_string: str) -> str:
        """Clean a JSON string by removing markdown code fences."""
        match = re.search(r"```(json)?\s*(.*?)\s*```", json_string, re.DOTALL)
        if match:
            return match.group(2).strip()
        return json_string.strip()
    
    def _is_huggingface_model(self, model: str) -> bool:
        """Check if this is a HuggingFace model."""
        return "/" in model and not any(model.startswith(prefix) for prefix in [
            "openrouter/", "anthropic/", "openai/", "google/", "together/", 
            "huggingface/", "cohere/", "deepseek/", "groq/", "perplexity/",
            "mistral/", "vertex_ai/", "bedrock/", "replicate/"
        ])
    
    def _determine_backend_config(self, model: str, use_runpod: bool, vllm_port: int, runpod_endpoint_id: str) -> tuple[str, str, str, str]:
        """Determine backend configuration."""
        is_hf_model = self._is_huggingface_model(model)
        
        if is_hf_model and use_runpod:
            log_message = f"Backend chosen: RunPod vLLM for HF model {model} - no fallback"
            fallback_model = None
            vllm_api_base = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/openai"
            final_model = model
        elif is_hf_model:
            log_message = f"Backend chosen: Local vLLM for HF model {model} - no fallback"
            fallback_model = None
            vllm_api_base = f"http://localhost:{vllm_port}/v1"
            final_model = model
        elif model == "claude-sonnet-4-20250514":
            log_message = f"Backend chosen: Anthropic for Claude model"
            fallback_model = None
            vllm_api_base = None
            final_model = "anthropic/claude-sonnet-4-20250514"
        elif "claude" in model:
            log_message = f"Backend chosen: Standard provider for Claude model"
            fallback_model = None
            vllm_api_base = None
            final_model = model
        else:
            log_message = f"Backend chosen: Standard provider for model {model}"
            fallback_model = None
            vllm_api_base = None
            final_model = model
        
        return log_message, fallback_model, vllm_api_base, final_model
    
    def _build_completion_params(self, model: str, messages: List[Dict[str, str]], temperature: float, 
                               max_tokens: int, max_retries: int, caching: bool, 
                               vllm_api_base: str, thinking: bool) -> dict:
        """Build completion parameters for litellm call."""
        temp_to_use = 1.0 if thinking else temperature
        completion_params = {
            "model": model,
            "messages": messages,
            "temperature": temp_to_use,
            "max_tokens": max_tokens,
            "timeout": 60.0,
            "max_retries": max_retries,
            "caching": caching
        }
        
        if vllm_api_base:
            completion_params["base_url"] = vllm_api_base
            completion_params["custom_llm_provider"] = "openai"
        
        return completion_params
    
    async def call_llm_api(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_model: Optional[Type[T]] = None,
        temperature: float = 1,
        max_tokens: int = 4096,
        max_retries: int = 3,
        thinking: bool = False,
        caching: bool = True,
    ) -> LLMCallResult:
        """
        Make an asynchronous call to an LLM API using litellm.
        """
        original_model = model
        reasoning_content = None
        raw_response_dict = None
        response_text = ""
        error_msg = None

        # Determine backend configuration
        use_runpod = os.environ.get("VLLM_BACKEND_USE_RUNPOD", "False").lower().strip() == "true"
        base_vllm_port = 7337
        
        log_message, fallback_model, vllm_api_base, model = self._determine_backend_config(
            model, use_runpod, base_vllm_port, "pmave9bk168p0q"
        )
        logger.info(log_message)

        try:
            logger.info(f"Attempting to call model: {model}")
            completion_params = self._build_completion_params(
                model, messages, temperature, max_tokens, max_retries, caching, vllm_api_base, thinking
            )
                
            raw_response = await litellm.acompletion(**completion_params)
            raw_response_dict = raw_response.dict()
            
            # Extract content and reasoning_content
            if 'choices' in raw_response_dict and raw_response_dict['choices']:
                choice = raw_response_dict['choices'][0]
                if 'message' in choice:
                    response_text = choice['message'].get('content', '')
                    reasoning_content = choice['message'].get('reasoning_content', None)
                else:
                    response_text = str(raw_response_dict)
            else:
                response_text = str(raw_response_dict)
            logger.info(f"Successfully received response from {model}")
        except Exception as e:
            logger.error(f"API call for model {model} failed: {e}")
            error_msg = f"API call for model {original_model} failed. Error: {e}"
            response_text = f"[ERROR: {error_msg}]"
            reasoning_content = None

        # Create API log
        api_log = APICallLog(
            model=model,
            messages=messages,
            raw_response=raw_response_dict if raw_response_dict else response_text,
            thinking_content=reasoning_content
        )

        # Parse structured response if requested
        structured_response = None
        if response_model and not error_msg and not response_text.startswith("[ERROR:"):
            try:
                cleaned_response = self.clean_json_string(response_text)
                structured_response = response_model.parse_raw(cleaned_response)
            except (ValidationError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse response into {response_model.__name__}. Error: {e}. Raw response: {response_text}")
                error_msg = f"Failed to parse response. Raw text: {response_text}"

        return LLMCallResult(
            response_text=response_text,
            structured_response=structured_response,
            api_log=api_log,
            error=error_msg
        )

    async def call_llm_api_with_structured_response(
        self,
        messages: List[Dict[str, str]],
        model: str,
        response_model: Type[T],
        temperature: float = 0.2,
        max_tokens: int = 4096,
        max_retries: int = 3,
        thinking: bool = False,
    ) -> Optional[T]:
        """
        Call the LLM API and expect a response that can be parsed into the given Pydantic model.
        """
        result = await self.call_llm_api(
            messages=messages,
            model=model,
            response_model=response_model,
            temperature=temperature,
            max_tokens=max_tokens,
            max_retries=max_retries,
            thinking=thinking
        )
        
        if result.error:
            logger.error(f"Error in structured response call: {result.error}")
            return None
        
        if result.structured_response:
            return result.structured_response
        
        # Try to parse the response text if structured_response is None but we have text
        if result.response_text and not result.response_text.startswith("[ERROR:"):
            try:
                cleaned_response = self.clean_json_string(result.response_text)
                return response_model.parse_raw(cleaned_response)
            except (ValidationError, json.JSONDecodeError) as e:
                logger.error(f"Failed to parse response text into {response_model.__name__}. Error: {e}. Raw content: {result.response_text}")
                return None
        
        logger.warning(f"Could not extract structured response from result")
        return None
