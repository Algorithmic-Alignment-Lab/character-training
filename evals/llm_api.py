import logging
import json
import re
import asyncio
import os
import requests
from typing import Optional, Type, TypeVar, List, Dict, Any

import litellm
from litellm.caching.caching import Cache
from pydantic import BaseModel, Field, ValidationError

from evals.models import APICallLog, LLMCallResult

# load dotenv variables if available
from dotenv import load_dotenv
load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Enable litellm local cache (in-memory by default) ---
litellm.cache = Cache()  # You can specify type=... for redis, s3, etc.

# Example usage:
# litellm.cache.add_cache(cache_key="mykey", result="response")
# litellm.cache.get_cache(cache_key="mykey")

# --- Pydantic Models for Structured Responses ---

class LLMResponse(BaseModel):
    """A standard response from the LLM."""
    content: str = Field(..., description="The text content of the response from the language model.")

class TraitEvaluation(BaseModel):
    """An evaluation of a single character trait."""
    trait: str = Field(..., description="The character trait being evaluated.")
    score: int = Field(..., ge=1, le=5, description="Likert scale rating (1: Strongly Disagree, 2: Disagree, 3: Neutral, 4: Agree, 5: Strongly Agree) on how well the response embodies the trait.")
    reasoning: str = Field(..., description="Brief reasoning for the score.")

class CharacterAnalysis(BaseModel):
    """
    A detailed analysis of an AI's adherence to a character persona.
    """
    is_in_character: bool = Field(..., description="Whether the AI's response is in character.")
    failure_type: Optional[str] = Field(None, description='If not in character, classify the failure. E.g., "Persona Deviation", "Generic Response", "Ethical Lecture"')
    consistency_score: int = Field(..., ge=1, le=10, description="An overall score from 1-10 indicating how consistent the response is with the persona.")
    trait_evaluations: List[TraitEvaluation] = Field(..., description="Evaluation of each character trait on a Likert scale.")
    analysis: str = Field(..., description="A qualitative summary of why the response was or was not in character.")
    interesting_moment: bool = Field(False, description="Whether this moment in the conversation is particularly interesting for analysis.")


T = TypeVar("T", bound=BaseModel)

def clean_json_string(json_string: str) -> str:
    """
    Cleans a JSON string by removing markdown code fences and correcting common formatting issues.
    """
    # Remove markdown fences (```json ... ``` or ``` ... ```)
    match = re.search(r"```(json)?\s*(.*?)\s*```", json_string, re.DOTALL)
    if match:
        return match.group(2).strip()
    return json_string.strip()

# --- Centralized API Call Function ---

async def call_llm_api(
    messages: List[Dict[str, str]],
    model: str,
    response_model: Optional[Type[T]] = None,
    temperature: float = 1,
    max_tokens: int = 4096,
    max_retries: int = 5,
    thinking: bool = False,
    caching: bool = True,
) -> LLMCallResult:
    """
    Makes an asynchronous call to an LLM API using litellm, with comprehensive logging.

    Args:
        messages: A list of messages in the conversation.
        model: The model to use for the completion (e.g., "claude-sonnet-4-20250514").
        response_model: The Pydantic model to parse the response into.
        temperature: The temperature for sampling.
        max_tokens: The maximum number of tokens to generate.
        max_retries: The number of retries for the initial API call.
        thinking: (deprecated) Ignored, kept for compatibility.
        caching: Whether to use litellm caching (default True).

    Returns:
        LLMCallResult containing the response, structured response (if applicable), and API log.
    """
    
    original_model = model
    reasoning_content = None
    raw_response_dict = None
    response_text = ""
    error_msg = None

    fallback_model = None
    if model == "claude-sonnet-4-20250514":
        model = "anthropic/claude-sonnet-4-20250514"

    if model == "anthropic/claude-sonnet-4-20250514":
        fallback_model = "openrouter/anthropic/claude-sonnet-4"
    elif "claude" in model:
        fallback_model = "openrouter/anthropic/claude-sonnet-4"
    elif "qwen" not in model:
        fallback_model = "openrouter/qwen/qwen3-32b"

    try:
        logger.info(f"Attempting to call model: {model}")
        # If thinking is True, set temperature to 1 (Anthropic requirement)
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
        # For Claude models, always add reasoning_effort
        if "claude" in model:
            completion_params["reasoning_effort"] = "medium"
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
        logger.warning(f"Initial API call for model {model} failed: {e}. Attempting fallback.")
        error_msg = f"API call for model {original_model} failed. Error: {e}"
        # Try fallback if we have one
        if fallback_model:
            try:
                logger.info(f"Attempting to call fallback model: {fallback_model}")
                completion_params = {
                    "model": fallback_model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timeout": 60.0,
                    "max_retries": max_retries,
                    "caching": caching
                }
                if "claude" in fallback_model and "reasoning_effort" in completion_params:
                    # Remove reasoning_effort for fallback model
                    pass
                elif "reasoning_effort" in completion_params:
                    del completion_params["reasoning_effort"]
                raw_response = await litellm.acompletion(**completion_params)
                raw_response_dict = raw_response.dict()
                if 'choices' in raw_response_dict and raw_response_dict['choices']:
                    choice = raw_response_dict['choices'][0]
                    if 'message' in choice:
                        response_text = choice['message'].get('content', '')
                        reasoning_content = choice['message'].get('reasoning_content', None)
                    else:
                        response_text = str(raw_response_dict)
                else:
                    response_text = str(raw_response_dict)
                model = fallback_model  # Update model for logging
                error_msg = None  # Clear error since fallback succeeded
                logger.info(f"Successfully received response from {fallback_model}")
            except Exception as fallback_e:
                error_msg = f"API call for model {original_model} and fallback {fallback_model} failed. Error: {fallback_e}"
                logger.error(error_msg)
                response_text = f"[ERROR: {error_msg}]"
        else:
            logger.error(error_msg)
            response_text = f"[ERROR: {error_msg}]"

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
            cleaned_response = clean_json_string(response_text)
            structured_response = response_model.parse_raw(cleaned_response)
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse response into {response_model.__name__}. Error: {e}. Raw response: {response_text}")
            error_msg = f"Failed to parse response. Raw text: {response_text}"

    return LLMCallResult(
        response_text=response_text,
        structured_response=structured_response,
        api_log=api_log,
        error=error_msg,
        thinking=reasoning_content
    )


async def call_llm_api_with_structured_response(
    messages: List[Dict[str, str]],
    model: str,
    response_model: Type[T],
    temperature: float = 0.2,
    max_tokens: int = 4096, # Increased max_tokens
    max_retries: int = 3,
    thinking: bool = False,
) -> Optional[T]:
    """
    Calls the LLM API and expects a response that can be parsed into the given Pydantic model.

    Args:
        messages: A list of messages in the conversation.
        model: The model to use for the completion.
        response_model: The Pydantic model to parse the response into.
        temperature: The temperature for sampling.
        max_tokens: The maximum number of tokens to generate.
        max_retries: The number of retries for the API call.
        thinking: Whether to enable the 'thinking' feature for Claude models.

    Returns:
        An instance of the response_model with the parsed response data, or None if parsing fails.
    """
    result = await call_llm_api(
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
            cleaned_response = clean_json_string(result.response_text)
            return response_model.parse_raw(cleaned_response)
        except (ValidationError, json.JSONDecodeError) as e:
            logger.error(f"Failed to parse response text into {response_model.__name__}. Error: {e}. Raw content: {result.response_text}")
            return None
    
    logger.warning(f"Could not extract structured response from result")
    return None


def load_vllm_lora_adapter(adapter_hf_name: str):
    """
    Loads the vLLM LORA adapter by sending a POST request. If vllm_port is specified, it will try to ssh to the runpod_a100_box runpod server and port forward the vLLM server to the local port. If use_runpod_endpoint_id is specified, it will use the RunPod serverless API to autoscale inference instead.

    Args:
        adapter_hf_name: Name of the adapter to load

    Raises:
        requests.exceptions.RequestException: If the request fails or returns non-200 status,
            except for the case where the adapter is already loaded
    """
    vllm_port = 7337
    runpod_endpoint_id = "pmave9bk168p0q"
    use_runpod = os.environ.get("VLLM_BACKEND_USE_RUNPOD", "False").lower().strip() == "true"

    if use_runpod:
        vllm_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/openai"
    else:
        # Setup tunnel to vLLM server
        os.system(f"ssh -N -L {vllm_port}:localhost:8000 runpod_a100_box -f")
        vllm_url = f"http://localhost:{vllm_port}"

    # Check if the model is already loaded and return early if so
    headers = {"Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}"} if use_runpod else {}
    response = requests.get(f"{vllm_url}/v1/models", headers=headers, timeout=10 * 60)
    response.raise_for_status()
    if adapter_hf_name in [model["id"] for model in response.json().get("data", [])]:
        print(f"LORA adapter {adapter_hf_name} is already loaded")
        return

    try:
        print(f"Loading LORA adapter {adapter_hf_name} on port {vllm_port}...")
        load_headers = {"Content-Type": "application/json"}
        if use_runpod:
            load_headers["Authorization"] = f"Bearer {os.environ['RUNPOD_API_KEY']}"
        
        response = requests.post(
            f"{vllm_url}/v1/load_lora_adapter",
            json={"lora_name": adapter_hf_name, "lora_path": adapter_hf_name},
            headers=load_headers,
            timeout=20 * 60,  # Wait up to 20 minutes for response
        )

        # If we get a 400 error about adapter already being loaded, that's fine
        if (
            response.status_code == 400
            and "has already been loaded" in response.json().get("message", "")
        ):
            print("LORA adapter was already loaded")
            return

        # For all other cases, raise any errors
        response.raise_for_status()
        print("LORA adapter loaded successfully!")

    except requests.exceptions.RequestException as e:
        if "has already been loaded" in str(e):
            print("LORA adapter was already loaded")
            return
        raise