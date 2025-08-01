"""Basic tests for the api."""

import os
import sys
import pydantic
# Ensure safetytooling package is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest

from safetytooling.apis.inference.api import InferenceAPI
from safetytooling.utils import utils


def test_default_global_api():
    utils.setup_environment()
    api1 = InferenceAPI.get_default_global_api()
    api2 = InferenceAPI.get_default_global_api()
    assert api1 is api2


@pytest.mark.asyncio
async def test_openai():
    utils.setup_environment()
    resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="gpt-4o-mini",
        question="What is the meaning of life?",
        max_tokens=1,
        n=2,
    )
    assert isinstance(resp, list)
    assert len(resp) == 2
    assert isinstance(resp[0], str)
    assert isinstance(resp[1], str)


@pytest.mark.asyncio
async def test_claude_3():
    utils.setup_environment()
    resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="claude-3-haiku-20240307",
        question="What is the meaning of life?",
        max_tokens=1,
        n=2,
    )
    assert isinstance(resp, list)
    assert len(resp) == 2
    assert isinstance(resp[0], str)
    assert isinstance(resp[1], str)


@pytest.mark.asyncio
async def test_claude_3_with_system_prompt():
    utils.setup_environment()
    resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="claude-3-haiku-20240307",
        question="What is the meaning of life?",
        system_prompt="You are an AI assistant who has never read the Hitchhiker's Guide to the Galaxy.",
        max_tokens=1,
        n=2,
    )
    assert isinstance(resp, list)
    assert len(resp) == 2
    assert isinstance(resp[0], str)
    assert isinstance(resp[1], str)


@pytest.mark.asyncio
async def test_gpt4o_mini_2024_07_18_with_response_format():
    utils.setup_environment()

    class CustomResponse(pydantic.BaseModel):
        answer: str
        confidence: float

    resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="gpt-4o-mini-2024-07-18",
        question="What is the meaning of life? Format your response as a JSON object with fields: answer (string) and confidence (float between 0 and 1).",
        max_tokens=100,
        n=2,
        response_format=CustomResponse,
    )
    assert isinstance(resp, list)
    assert len(resp) == 2
    assert isinstance(resp[0], str)
    assert isinstance(resp[1], str)

    # Verify responses can be parsed into CustomResponse objects
    CustomResponse.model_validate_json(resp[0])
    CustomResponse.model_validate_json(resp[1])


@pytest.mark.asyncio
async def test_api_with_stop_parameter():
    """Test that the stop parameter works correctly with the InferenceAPI."""
    utils.setup_environment()

    # Test with OpenAI model
    openai_resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="gpt-4o-mini-2024-07-18",
        question="Count from 1 to 10: 1, 2, 3,",
        max_tokens=20,
        stop=[", 5"],  # Should stop before outputting ", 5"
    )

    assert isinstance(openai_resp, list)
    assert len(openai_resp) == 1
    assert isinstance(openai_resp[0], str)
    assert ", 5" not in openai_resp[0]
    assert "4" in openai_resp[0]

    # Test with Anthropic model
    anthropic_resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="claude-3-haiku-20240307",
        question="Count from 1 to 10: 1, 2, 3,",
        max_tokens=20,
        stop=[", 5"],  # Should stop before outputting ", 5"
    )

    assert isinstance(anthropic_resp, list)
    assert len(anthropic_resp) == 1
    assert isinstance(anthropic_resp[0], str)
    assert ", 5" not in anthropic_resp[0]
    assert "4" in anthropic_resp[0]


@pytest.mark.asyncio
async def test_anthropic_accepts_seed_parameter():
    """Test that the seed parameter is ignored without error for Anthropic models."""
    utils.setup_environment()

    # Test that seed parameter is ignored without error for Anthropic models
    resp = await InferenceAPI.get_default_global_api().ask_single_question(
        model_id="claude-sonnet-4-20250514",
        question="What is 2+2?",
        max_tokens=10,
        seed=42,  # This should be ignored without error for Anthropic
    )
    assert isinstance(resp, list)
    assert len(resp) == 1
    assert isinstance(resp[0], str)


@pytest.mark.asyncio
async def test_anthropic_rejects_invalid_parameters():
    """Test that invalid parameters raise TypeError with Anthropic models."""
    utils.setup_environment()

    with pytest.raises(TypeError):
        await InferenceAPI.get_default_global_api().ask_single_question(
            model_id="claude-sonnet-4-20250514",
            question="What is 2+2?",
            max_tokens=10,
            invalid_param=123,  # This should raise an error
        )
