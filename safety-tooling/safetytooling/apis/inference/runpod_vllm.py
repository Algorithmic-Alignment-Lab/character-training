import asyncio
import collections
import logging
import os
import time
from pathlib import Path
from traceback import format_exc

import aiohttp
import requests

from safetytooling.data_models import LLMResponse, Prompt, StopReason
from safetytooling.utils import math_utils

from .model import InferenceAPIModel

VLLM_MODELS = {
    "dummy": "https://pod-port.proxy.runpod.net/v1/chat/completions",
    # Add more models and their endpoints as needed
}

LOGGER = logging.getLogger(__name__)


class VLLMChatModel(InferenceAPIModel):
    def __init__(
        self,
        num_threads: int,
        prompt_history_dir: Path | None = None,
        vllm_base_url: str = "http://localhost:8000/v1/chat/completions",
    ):
        self.num_threads = num_threads
        self.prompt_history_dir = prompt_history_dir
        self.available_requests = asyncio.BoundedSemaphore(int(self.num_threads))

        self.headers = {"Content-Type": "application/json"}
        self.vllm_base_url = vllm_base_url
        if self.vllm_base_url.endswith("v1"):
            self.vllm_base_url += "/chat/completions"

        self.stop_reason_map = {
            "length": StopReason.MAX_TOKENS.value,
            "stop": StopReason.STOP_SEQUENCE.value,
        }

    async def query(self, model_url: str, payload: dict, session: aiohttp.ClientSession, timeout: int = 1000) -> dict:
        async with session.post(model_url, headers=self.headers, json=payload, timeout=timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                if "<!DOCTYPE html>" in str(error_text) and "<title>" in str(error_text):
                    reason = str(error_text).split("<title>")[1].split("</title>")[0]
                else:
                    reason = " ".join(str(error_text).split()[:20])
                raise RuntimeError(f"API Error: Status {response.status}, {reason}")
            return await response.json()

    async def run_query(self, model_url: str, messages: list, params: dict) -> dict:
        payload = {
            "model": params.get("model", "default"),
            "messages": messages,
            **{k: v for k, v in params.items() if k != "model"},
        }

        async with aiohttp.ClientSession() as session:
            response = await self.query(model_url, payload, session)
            if "error" in response:
                if "<!DOCTYPE html>" in str(response) and "<title>" in str(response):
                    reason = str(response).split("<title>")[1].split("</title>")[0]
                else:
                    reason = " ".join(str(response).split()[:20])
                print(f"API Error: {reason}")
                LOGGER.error(f"API Error: {reason}")
                raise RuntimeError(f"API Error: {reason}")
            return response

    @staticmethod
    def convert_top_logprobs(data: dict) -> list[dict]:
        # convert OpenAI chat version of logprobs response to completion version
        top_logprobs = []

        for item in data["content"]:
            # <|end|> is known to be duplicated on gpt-4-turbo-2024-04-09
            # See experiments/sample-notebooks/api-tests/logprob-dup-tokens.ipynb for details
            possibly_duplicated_top_logprobs = collections.defaultdict(list)
            for top_logprob in item["top_logprobs"]:
                possibly_duplicated_top_logprobs[top_logprob["token"]].append(top_logprob["logprob"])

            top_logprobs.append({k: math_utils.logsumexp(vs) for k, vs in possibly_duplicated_top_logprobs.items()})

        return top_logprobs

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

        model_url = VLLM_MODELS.get(model_id, self.vllm_base_url)

        prompt_file = self.create_prompt_history_file(prompt, model_id, self.prompt_history_dir)

        LOGGER.debug(f"Making {model_id} call")
        response_data = None
        duration = None
        api_duration = None

        kwargs["model"] = model_id
        if "logprobs" in kwargs:
            kwargs["top_logprobs"] = kwargs["logprobs"]
            kwargs["logprobs"] = True

        for i in range(max_attempts):
            try:
                async with self.available_requests:
                    api_start = time.time()

                    response_data = await self.run_query(
                        model_url,
                        prompt.openai_format(),
                        kwargs,
                    )
                    api_duration = time.time() - api_start

                    if not response_data.get("choices"):
                        LOGGER.error(f"Invalid response format: {response_data}")
                        raise RuntimeError(f"Invalid response format: {response_data}")

                    if not all(is_valid(choice["message"]["content"]) for choice in response_data["choices"]):
                        LOGGER.error(f"Invalid responses according to is_valid {response_data}")
                        raise RuntimeError(f"Invalid responses according to is_valid {response_data}")
            except TypeError as e:
                raise e
            except Exception as e:
                error_info = f"Exception Type: {type(e).__name__}, Error Details: {str(e)}, Traceback: {format_exc()}"
                LOGGER.warn(f"Encountered API error: {error_info}.\nRetrying now. (Attempt {i})")
                await asyncio.sleep(1.5**i)
            else:
                break
        else:
            LOGGER.error(f"Failed to get a response from the API after {max_attempts} attempts.")
            raise RuntimeError(f"Failed to get a response from the API after {max_attempts} attempts.")

        duration = time.time() - start
        LOGGER.debug(f"Completed call to {model_id} in {duration}s")

        if response_data is None or response_data.get("choices", None) is None:
            LOGGER.error(f"Invalid response format: {response_data}")
            raise RuntimeError(f"Invalid response format: {response_data}")

        responses = [
            LLMResponse(
                model_id=model_id,
                completion=choice["message"]["content"],
                stop_reason=choice["finish_reason"],
                api_duration=api_duration,
                duration=duration,
                cost=0,
                logprobs=self.convert_top_logprobs(choice["logprobs"]) if choice.get("logprobs") is not None else None,
            )
            for choice in response_data["choices"]
        ]

        self.add_response_to_prompt_file(prompt_file, responses)
        if print_prompt_and_response:
            prompt.pretty_print(responses)

        return responses


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
