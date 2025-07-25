import litellm
import os
import logging
from typing import Optional, Type, TypeVar, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import json
import re
import asyncio
# load dotenv
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Extract the content between the fences
        return match.group(2).strip()
    # If no fences, just strip whitespace
    return json_string.strip()

# --- Centralized API Call Function ---

async def call_llm_api(
    messages: List[Dict[str, str]],
    model: str,
    response_model: Optional[Type[T]] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    max_retries: int = 3,
) -> T | Dict[str, Any] | str:
    """
    Makes an asynchronous call to an LLM API using litellm.
    If a Pydantic response_model is provided, it attempts to parse the response
    into that model, handling common JSON formatting errors.

    Args:
        messages: A list of messages in the conversation.
        model: The model to use for the completion (e.g., "openrouter/qwen/qwen3-32b").
        response_model: The Pydantic model to parse the response into.
        temperature: The temperature for sampling.
        max_tokens: The maximum number of tokens to generate.
        max_retries: The number of retries for the API call.

    Returns:
        If a response_model is provided, returns an instance of that model on success,
        or a dictionary with an "error" key on failure.
        Otherwise, returns the raw text response as a string.
    """
    # Parse model to handle different providers correctly
    original_model = model
    attempt = 0
    while attempt < max_retries:
        try:
            # Handle different model formats for litellm by setting environment variables
            if model.startswith("openrouter/"):
                # For OpenRouter, set environment variables and use full model path
                openrouter_key = os.getenv("OPENROUTER_API_KEY")
                if openrouter_key:
                    os.environ["OPENROUTER_API_KEY"] = openrouter_key
                    os.environ["OPENROUTER_API_BASE"] = "https://openrouter.ai/api/v1"
                model_to_use = model  # Keep full openrouter/ prefix
            elif model.startswith("anthropic/"):
                # For Anthropic direct, set API key and use model without prefix
                anthropic_key = os.getenv("ANTHROPIC_API_KEY")
                if anthropic_key:
                    os.environ["ANTHROPIC_API_KEY"] = anthropic_key
                model_to_use = model.replace("anthropic/", "")
            elif model.startswith("openai/"):
                # For OpenAI, set API key and use model without prefix
                openai_key = os.getenv("OPENAI_API_KEY")
                if openai_key:
                    os.environ["OPENAI_API_KEY"] = openai_key
                model_to_use = model.replace("openai/", "")
            elif model.startswith("together/"):
                # For Together, set API key and use model without prefix
                together_key = os.getenv("TOGETHER_API_KEY")
                if together_key:
                    os.environ["TOGETHER_API_KEY"] = together_key
                model_to_use = model.replace("together/", "")
            else:
                # Default case - assume it's a direct model name
                model_to_use = model
            
            # Prepare arguments for litellm call
            call_kwargs: Dict[str, Any] = {
                "model": model_to_use,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "timeout": 60.0,
            }
            
            if response_model:
                call_kwargs["response_model"] = response_model
                
            logger.info(f"Attempt {attempt + 1}/{max_retries} to call model: {model_to_use}")
            raw_response = await litellm.acompletion(**call_kwargs)
            
            response_content = raw_response.choices[0].message.content
            
            if response_model:
                if isinstance(response_content, str):
                    cleaned_content = clean_json_string(response_content)
                    try:
                        parsed_response = response_model.model_validate_json(cleaned_content)
                        return parsed_response
                    except ValidationError as ve:
                        logger.warning(f"Pydantic validation failed after cleaning. Error: {ve}. Raw content: {cleaned_content}")
                        raise ve
                else:
                    return response_model.model_validate(response_content)
            else:
                return response_content or ""

        except Exception as e:
            logger.error(f"API call for model {model} failed on attempt {attempt + 1}. Error: {e}")
            
            # Check if this is an Anthropic overload error that should trigger immediate fallback
            is_anthropic_overload = (
                model.startswith("anthropic/") and 
                ("overloaded_error" in str(e).lower() or "overloaded" in str(e).lower())
            )
            
            if is_anthropic_overload:
                # Immediate fallback for overload errors
                import re as _re
                model_without_prefix = model.replace("anthropic/", "")
                m = _re.match(r"^(.+?)(?:-\d{8})?$", model_without_prefix)
                base = m.group(1) if m else model_without_prefix
                fallback_model = f"openrouter/anthropic/{base}"
                logger.info(f"Anthropic model {model} overloaded. Immediately falling back to {fallback_model}.")
                model = fallback_model
                attempt = 0
                continue
            
            attempt += 1
            if attempt >= max_retries:
                # If this was an Anthropic model, try OpenRouter fallback without date suffix
                if model.startswith("anthropic/"):
                    # Extract base model name (drop trailing date if present)
                    import re as _re
                    model_without_prefix = model.replace("anthropic/", "")
                    m = _re.match(r"^(.+?)(?:-\d{8})?$", model_without_prefix)
                    base = m.group(1) if m else model_without_prefix
                    fallback_model = f"openrouter/anthropic/{base}"
                    logger.info(f"Anthropic model {model} exhausted retries. Falling back to {fallback_model}.")
                    # Reset model for retry
                    model = fallback_model
                    attempt = 0
                    continue
                # No more fallbacks; return error
                error_message = f"Failed to get a valid response from model {model} after {max_retries} attempts. Last error: {e}"
                logger.critical(error_message)
                if response_model:
                    return {"error": error_message, "raw_response": str(e)}
                return error_message
            await asyncio.sleep(2 ** attempt)

    final_error = f"Exhausted all retries for model {model}."
    if response_model:
        return {"error": final_error}
    return final_error

def get_llm_response(system_prompt: str, messages: List[Dict[str, str]], model: str) -> str:
    """
    Constructs the message list and gets a synchronous response from the LLM.

    Args:
        system_prompt: The system prompt to use.
        messages: The list of messages in the conversation.
        model: The model to use.

    Returns:
        The LLM's response as a string.
    """
    # Construct the full message list with the system prompt
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    # Run the async API call in a sync context
    # This is a simple approach; for complex apps, manage the event loop carefully.
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    response = loop.run_until_complete(call_llm_api(
        messages=full_messages,
        model=model,
        response_model=None  # We just want the string response
    ))

    if isinstance(response, str):
        return response
    
    # If the response is a Pydantic model (e.g., on parsing failure fallback),
    # try to extract content or convert to a string.
    if hasattr(response, 'content'):
        return response.content
    
    return str(response)


async def get_llm_response_stream(system_prompt: str, messages: List[Dict[str, str]], model: str):
    """
    Constructs the message list and gets a streaming response from the LLM.

    Args:
        system_prompt: The system prompt to use.
        messages: The list of messages in the conversation.
        model: The model to use.

    Yields:
        Chunks of the LLM's response as strings.
    """
    full_messages = [{"role": "system", "content": system_prompt}] + messages

    try:
        response = await litellm.acompletion(
            model=model,
            messages=full_messages,
            stream=True,
            temperature=0.7,
            max_tokens=2048,
            timeout=30.0
        )

        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content

    except Exception as e:
        error_message = f"Error during streaming from {model}: {e}"
        logger.error(error_message)
        yield f"[ERROR: {error_message}]"
