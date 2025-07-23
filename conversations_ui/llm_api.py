import litellm
import logging
from typing import Optional, Type, TypeVar, List, Dict, Any
from pydantic import BaseModel, Field, ValidationError
import json
import re
import asyncio

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
        return match.group(2).strip()
    return json_string.strip()

# --- Centralized API Call Function ---

async def call_llm_api(
    messages: List[Dict[str, str]],
    model: str,
    response_model: Optional[Type[T]] = None,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    max_retries: int = 5,
) -> T | str:
    """
    Makes an asynchronous call to an LLM API using litellm, with a fallback to OpenRouter for Anthropic models.

    Args:
        messages: A list of messages in the conversation.
        model: The model to use for the completion (e.g., "claude-sonnet-4-20250514").
        response_model: The Pydantic model to parse the response into.
        temperature: The temperature for sampling.
        max_tokens: The maximum number of tokens to generate.
        max_retries: The number of retries for the initial API call.

    Returns:
        If a response_model is provided, returns an instance of that model.
        Otherwise, returns the raw text response as a string.
        Returns an error message string if all API calls fail.
    """
    
    fallback_model = None
    if model == "claude-sonnet-4-20250514":
        fallback_model = "openrouter/anthropic/claude-sonnet-4"

    try:
        # First attempt to call the model directly
        logger.info(f"Attempting to call model: {model}")
        raw_response = await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=45.0,
            max_retries=max_retries
        )
        response_text = raw_response.choices[0].message.content or ""
        logger.info(f"Successfully received response from {model}")

    except Exception as e:
        logger.warning(f"Initial API call for model {model} failed: {e}. Attempting fallback.")
        
        if fallback_model:
            logger.info(f"Falling back to OpenRouter model: {fallback_model}")
            try:
                raw_response = await litellm.acompletion(
                    model=fallback_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=45.0,
                    max_retries=max_retries
                )
                response_text = raw_response.choices[0].message.content or ""
                logger.info(f"Successfully received response from fallback model {fallback_model}")
            except Exception as e_fallback:
                error_message = f"Fallback API call for model {fallback_model} also failed: {e_fallback}"
                logger.error(error_message)
                return f"[ERROR: {error_message}]"
        else:
            # Generic error if the failed model is not the one with a specific fallback
            error_message = f"API call for model {model} failed and no specific fallback is configured. Error: {e}"
            logger.error(error_message)
            return f"[ERROR: {error_message}]"

    if not response_model:
        return response_text

    # If a model is expected, clean and parse the text
    cleaned_text = clean_json_string(response_text)
    
    try:
        return response_model.parse_raw(cleaned_text)
    except (ValidationError, json.JSONDecodeError) as e_parse:
        error_message = f"Failed to parse {response_model.__name__} from response. Error: {e_parse}. Raw text: '{cleaned_text}'"
        logger.error(error_message)
        # Fallback: return the raw (but cleaned) text for the caller to handle
        return cleaned_text

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
