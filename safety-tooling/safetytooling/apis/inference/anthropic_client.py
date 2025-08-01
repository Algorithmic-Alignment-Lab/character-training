import asyncio
import json
import logging
import time
from pathlib import Path
from traceback import format_exc

import sys
import anthropic.types
from anthropic import AsyncAnthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request

# Remove the path we added to avoid affecting other imports
sys.path.pop(0)

from safetytooling.data_models import LLMResponse, Prompt, Usage

from .model import InferenceAPIModel

ANTHROPIC_MODELS = {
    "claude-3-5-sonnet-latest",
    "claude-sonnet-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-5-haiku-20241022",
    "claude-3-opus-20240229",
    "claude-3-sonnet-20240229",
    "claude-3-haiku-20240307",
    "research-claude-cabernet",
    "claude-3-7-sonnet-20250219",
}
VISION_MODELS = {
    "claude-sonnet-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-opus-20240229",
    "claude-3-7-sonnet-20250219",
}
LOGGER = logging.getLogger(__name__)


class AnthropicChatModel(InferenceAPIModel):
    def __init__(
        self,
        num_threads: int,
        prompt_history_dir: Path | None = None,
        anthropic_api_key: str | None = None,
    ):
        self.num_threads = num_threads
        self.prompt_history_dir = prompt_history_dir
        if anthropic_api_key:
            self.aclient = AsyncAnthropic(api_key=anthropic_api_key)
        else:
            self.aclient = AsyncAnthropic()

        self.available_requests = asyncio.BoundedSemaphore(int(self.num_threads))
        self.kwarg_change_name = {"stop": "stop_sequences"}

    async def __call__(
        self,
        model_id: str,
        prompt: Prompt,
        print_prompt_and_response: bool,
        max_attempts: int,
        is_valid=lambda x: True,
        **kwargs,
    ) -> list[LLMResponse]:
        start = time.time()

        if prompt.contains_image():
            assert model_id in VISION_MODELS, f"Model {model_id} does not support images"

        # Rename based on kwarg_change_name
        for k, v in self.kwarg_change_name.items():
            if k in kwargs:
                kwargs[v] = kwargs[k]
                del kwargs[k]

        # Special case: ignore seed parameter since it's used for caching in safety-tooling
        # Other surplus parameters will still raise an error
        if "seed" in kwargs:
            del kwargs["seed"]

        sys_prompt, chat_messages = prompt.anthropic_format()
        prompt_file = self.create_prompt_history_file(prompt, model_id, self.prompt_history_dir)

        LOGGER.debug(f"Making {model_id} call")
        response: anthropic.types.Message | None = None
        duration = None

        async with self.available_requests:
            error_list = []
            for i in range(max_attempts):
                try:
                    api_start = time.time()

                    response = await self.aclient.messages.create(
                        messages=chat_messages,
                        model=model_id,
                        max_tokens=kwargs.pop("max_tokens", 2000),
                        **kwargs,
                        **(dict(system=sys_prompt) if sys_prompt else {}),
                    )

                    api_duration = time.time() - api_start
                    if not is_valid(response):
                        raise RuntimeError(f"Invalid response according to is_valid {response}")
                except (TypeError, anthropic.NotFoundError) as e:
                    raise e
                except Exception as e:
                    error_info = (
                        f"Exception Type: {type(e).__name__}, Error Details: {str(e)}, Traceback: {format_exc()}"
                    )
                    LOGGER.warn(f"Encountered API error: {error_info}.\nRetrying now. (Attempt {i})")
                    error_list.append(error_info)
                    api_duration = time.time() - api_start
                    await asyncio.sleep(1.5**i)
                else:
                    break

        duration = time.time() - start
        LOGGER.debug(f"Completed call to {model_id} in {duration}s")
        if response is None:
            if model_id == "research-claude-cabernet":
                LOGGER.error(f"Failed to get a response for {prompt} from any API after {max_attempts} attempts.")
                # check for numbers of different kinds of errors
                n_prompt_blocked_errs = len([e for e in error_list if "Prompt blocked" in e])
                n_try_again_errs = len([e for e in error_list if "try again later" in e])
                LOGGER.error(
                    f"Encountered {n_prompt_blocked_errs} prompt blocked errors and {n_try_again_errs} try again later errors"
                )
                if n_prompt_blocked_errs > n_try_again_errs:
                    stop_reason = "prompt_blocked"
                    response = LLMResponse(
                        model_id=model_id,
                        completion="",
                        stop_reason=stop_reason,
                        duration=duration,
                        api_duration=api_duration,
                        cost=0,
                        usage=None,  # No usage data if response is None
                    )
                else:
                    response = LLMResponse(
                        model_id=model_id,
                        completion="",
                        stop_reason="api_error",
                        duration=duration,
                        api_duration=api_duration,
                        cost=0,
                        # No usage data if response is None
                    )
            else:
                raise RuntimeError(f"Failed to get a response from the API after {max_attempts} attempts.")

        else:
            usage_data = response.usage  # Get usage data
            current_usage = (
                Usage(input_tokens=usage_data.input_tokens, output_tokens=usage_data.output_tokens)
                if usage_data
                else None
            )
            # when refusal classifier fires, response.content is []
            is_reasoning = response.content[0].type == "thinking" if len(response.content) > 0 else False
            # check whether request is for websearch tool
            types = [c.type for c in response.content]
            is_websearch = "web_search_tool_result" in types
            assert (
                is_reasoning or is_websearch or len(response.content) <= 1
            ), "Check that only 1 completion is returned when request is not for websearch tool use or reasoning"

            if is_reasoning:
                if not hasattr(response.content[-1], "text"):
                    raise RuntimeError(f"Anthropic reasoning model {model_id} returned a response with no text")
                response = LLMResponse(
                    model_id=model_id,
                    completion=response.content[-1].text,
                    stop_reason=response.stop_reason,
                    duration=duration,
                    api_duration=api_duration,
                    cost=0,
                    reasoning_content=response.content[0].thinking,
                    usage=current_usage,  # Populate usage
                )
            elif is_websearch:
                texts = [c.text for c in response.content if c.type == "text"]
                response = LLMResponse(
                    model_id=model_id,
                    completion="\n".join(texts),
                    stop_reason=response.stop_reason,
                    duration=duration,
                    api_duration=api_duration,
                    cost=0,
                    usage=current_usage,  # Populate usage
                )
            else:
                response = LLMResponse(
                    model_id=model_id,
                    completion=(
                        response.content[0].text if len(response.content) > 0 else ""
                    ),  # refusal classifier, return empty str
                    stop_reason=response.stop_reason,
                    duration=duration,
                    api_duration=api_duration,
                    cost=0,
                    usage=current_usage,  # Populate usage
                )

        responses = [response]

        self.add_response_to_prompt_file(prompt_file, responses)
        if print_prompt_and_response:
            prompt.pretty_print(responses)

        return responses

    def make_stream_api_call(
        self,
        model_id: str,
        prompt: Prompt,
        max_tokens: int,
        **params,
    ) -> anthropic.AsyncMessageStreamManager:
        sys_prompt, chat_messages = prompt.anthropic_format()
        return self.aclient.messages.stream(
            model=model_id,
            messages=chat_messages,
            **(dict(system=sys_prompt) if sys_prompt else {}),
            max_tokens=max_tokens,
            **params,
        )


class AnthropicModelBatch:
    def __init__(self, anthropic_api_key: str | None = None):
        if anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        else:
            self.client = anthropic.Anthropic()

    def create_message_batch(self, requests: list[dict]) -> dict:
        """Create a batch of messages."""
        return self.client.messages.batches.create(requests=requests)

    def retrieve_message_batch(self, batch_id: str) -> dict:
        """Retrieve a message batch."""
        return self.client.messages.batches.retrieve(batch_id)

    async def poll_message_batch(self, batch_id: str) -> dict:
        """Poll a message batch until it is completed."""
        message_batch = None
        minutes_elapsed = 0
        while True:
            message_batch = self.retrieve_message_batch(batch_id)
            if message_batch.processing_status == "ended":
                return message_batch
            if minutes_elapsed % 60 == 59:
                LOGGER.debug(f"Batch {batch_id} is still processing... ({minutes_elapsed} minutes elapsed)")
                print(f"Batch {batch_id} is still processing... ({minutes_elapsed} minutes elapsed)")
            await asyncio.sleep(60)  # Sleep for 1 minute
            minutes_elapsed += 1

    def list_message_batches(self, limit: int = 20) -> list[dict]:
        """List all message batches in the workspace."""
        return [batch for batch in self.client.messages.batches.list(limit=limit)]

    def retrieve_message_batch_results(self, batch_id: str) -> list[dict]:
        """Retrieve results of a message batch."""
        return [result for result in self.client.messages.batches.results(batch_id)]

    def cancel_message_batch(self, batch_id: str) -> dict:
        """Cancel a message batch."""
        return self.client.messages.batches.cancel(batch_id)

    def get_custom_id(self, index: int, prompt: Prompt) -> str:
        """Generate a custom ID for a batch request using index and prompt hash."""
        hash_str = prompt.model_hash()
        return f"{index}_{hash_str}"

    def prompts_to_requests(self, model_id: str, prompts: list[Prompt], max_tokens: int, **kwargs) -> list[Request]:
        # Special case: ignore seed parameter since it's used for caching in safety-tooling
        # Other surplus parameters will still raise an error
        if "seed" in kwargs:
            del kwargs["seed"]

        requests = []
        for i, prompt in enumerate(prompts):
            sys_prompt, chat_messages = prompt.anthropic_format()
            requests.append(
                Request(
                    custom_id=self.get_custom_id(i, prompt),
                    params=MessageCreateParamsNonStreaming(
                        model=model_id,
                        messages=chat_messages,
                        max_tokens=max_tokens,
                        **(dict(system=sys_prompt) if sys_prompt else {}),
                        **kwargs,
                    ),
                )
            )
        return requests

    async def __call__(
        self,
        model_id: str,
        prompts: list[Prompt],
        max_tokens: int,
        log_dir: Path | None = None,
        **kwargs,
    ) -> tuple[list[LLMResponse], str]:
        assert max_tokens is not None, "Anthropic batch API requires max_tokens to be specified"
        start = time.time()

        custom_ids = [self.get_custom_id(i, prompt) for i, prompt in enumerate(prompts)]
        set_custom_ids = set(custom_ids)
        assert len(set_custom_ids) == len(custom_ids), "Duplicate custom IDs found"

        requests = self.prompts_to_requests(model_id, prompts, max_tokens, **kwargs)
        batch_response = self.create_message_batch(requests=requests)
        batch_id = batch_response.id
        if log_dir is not None:
            log_file = log_dir / f"batch_id_{batch_id}.json"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "w") as f:
                json.dump(batch_response.model_dump(mode="json"), f)
        print(f"Batch {batch_id} created with {len(prompts)} requests")

        _ = await self.poll_message_batch(batch_id)

        results = self.retrieve_message_batch_results(batch_id)
        LOGGER.info(f"{results[0]=}")

        responses_dict = {}
        for result in results:
            if result.result.type == "succeeded":
                content = result.result.message.content
                usage_data = result.result.message.usage

                # Safely extract text and thinking content
                text_content = None
                reasoning_content = None  # We can extract this even if not used by LLMResponse yet
                if content:
                    for block in content:
                        if block.type == "text" and hasattr(block, "text"):
                            text_content = block.text
                        elif block.type == "thinking" and hasattr(block, "thinking"):
                            reasoning_content = block.thinking

                text = text_content if text_content else ""

                assert result.custom_id in set_custom_ids
                responses_dict[result.custom_id] = LLMResponse(
                    model_id=model_id,
                    completion=text,
                    stop_reason=result.result.message.stop_reason,
                    duration=None,  # Batch does not track individual durations
                    api_duration=None,
                    cost=0,
                    batch_custom_id=result.custom_id,
                    reasoning_content=reasoning_content,
                    usage=(
                        Usage(input_tokens=usage_data.input_tokens, output_tokens=usage_data.output_tokens)
                        if usage_data
                        else None
                    ),
                )

        responses = []
        for custom_id in custom_ids:
            responses.append(responses_dict[custom_id] if custom_id in responses_dict else None)

        duration = time.time() - start
        LOGGER.debug(f"Completed batch call in {duration}s")

        return responses, batch_id
