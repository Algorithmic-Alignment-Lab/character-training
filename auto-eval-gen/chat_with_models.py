#!/usr/bin/env python3
"""
Minimal script to chat with any model via API
Includes conversation logging and chain-of-thought tracking
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add the parent directory to sys.path to import from evals
sys.path.append(str(Path(__file__).parent.parent))
from evals.llm_api import call_llm_api, load_vllm_lora_adapter

from litellm import completion
from litellm.utils import supports_reasoning

from globals import models, NUM_RETRIES

# Model capability registry for max_tokens and thinking support
MODEL_CAPABILITIES = {
    # Anthropic
    "anthropic/claude-3-opus-20240229": {"max_tokens": 4096, "thinking": True},
    "anthropic/claude-3-sonnet-20240229": {"max_tokens": 4096, "thinking": True},
    "anthropic/claude-3-haiku-20240307": {"max_tokens": 4096, "thinking": True},
    # OpenAI
    "openai/gpt-4o": {"max_tokens": 128000, "thinking": False},
    "openai/gpt-4": {"max_tokens": 128000, "thinking": False},
    "openai/gpt-3.5-turbo": {"max_tokens": 16385, "thinking": False},
    "openai/o3-mini": {"max_tokens": 4096, "thinking": False},
    # Deepseek
    "deepseek/deepseek-chat": {"max_tokens": 8192, "thinking": True},
    # Gemini
    "vertex_ai/gemini-1.5-pro": {"max_tokens": 8192, "thinking": True},
    "google/gemini-1.5-flash-001": {"max_tokens": 8192, "thinking": True},
    # Llama (Meta)
    "meta/llama-3-8b-instruct": {"max_tokens": 8192, "thinking": False},
    "meta/llama-3-70b-instruct": {"max_tokens": 8192, "thinking": False},
}


class ModelChatter:
    def __init__(
        self,
        api_key: str | None = None,
        thinking_enabled: bool = True,
        max_tokens: int = 11000,
        thinking_tokens: int = 10000,
        system_prompt: str | None = None,
        model: str = "claude-sonnet-4",
        temperature: float = 0.0,
        tools: Optional[list] = None,
    ):
        """Initialize the model chat client using LiteLLM"""
        cache_dir = Path("./cache")
        cache_dir.mkdir(exist_ok=True)
        self.conversation_history: List[dict] = []  # Use OpenAI-style dicts
        self.log_file = f"chat_transcripts/model_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.tools = tools if tools is not None else []

        # Use model shortcut or direct model ID
        if model in models:
            self.model = models[model]["id"]
            self.model_shortcut = model
            self.model_supports_thinking = models[model].get("thinking", False)
            self.provider = models[model]["org"]
        else:
            self.model = model
            self.model_shortcut = model
            self.model_supports_thinking = False  # Assume custom models don't support thinking
            # Add vLLM detection and provider inference
            if model.startswith("vllm/") or "/" in model:
                self.provider = "vllm"
                self.model_id = model.replace("vllm/", "")
            elif model.startswith("together_ai/"):
                self.provider = "together_ai"
            else:
                self.provider = "unknown"

        # Model capability overrides
        self.model_cap = MODEL_CAPABILITIES.get(self.model, {})
        self.max_tokens = min(max_tokens, self.model_cap.get("max_tokens", max_tokens))
        self.model_supports_thinking = self.model_cap.get(
            "thinking", self.model_supports_thinking
        )

        # Check if LiteLLM supports reasoning for this model
        self.litellm_supports_thinking = supports_reasoning(model=self.model)

        self.thinking_enabled = thinking_enabled and (
            self.model_supports_thinking or self.litellm_supports_thinking
        )
        self.thinking_tokens = thinking_tokens

        # Set temperature based on provider and thinking support
        if self.thinking_enabled and self.provider == "anthropic":
            self.temperature = 1.0  # Required for Anthropic thinking
        else:
            self.temperature = temperature

        self.system_prompt = (
            system_prompt
            or "You are a helpful AI assistant. It is your job to assist the user with their request and ensure that the user is satisfied with your response."
        )

        # Load LoRA adapter for vLLM models that require it
        if self.provider == "vllm" and model in models and models[model].get("requires_lora", False):
            print(f"Loading LoRA adapter for vLLM model: {self.model}")
            try:
                load_vllm_lora_adapter(self.model)
                print(f"✅ LoRA adapter loaded successfully for {self.model}")
            except Exception as e:
                print(f"⚠️ Failed to load LoRA adapter for {self.model}: {e}")
                print("   Continuing anyway - the model might still work...")

    async def chat(self, message: str) -> tuple[str, str]:
        """Send a message to the model and get response with thinking content"""
        # Add current user message to history
        user_msg = {"role": "user", "content": message}
        self.conversation_history.append(user_msg)

        # Build messages for the API call including system prompt
        messages = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.extend(self.conversation_history)

        # Prepare API call parameters
        kwargs = {"max_tokens": self.max_tokens, "temperature": self.temperature}

        # Only add 'thinking' if supports_reasoning returns True for this model and provider is supported
        import litellm

        supported_providers = {
            "anthropic",
            "deepseek",
            "bedrock",
            "vertexai",
            "openrouter",
            "xai",
            "google",
            "perplexity",
            "mistral",
            "together_ai"
        }
        if self.thinking_enabled:
            try:
                if (
                    litellm.supports_reasoning(model=self.model)
                    and self.provider in supported_providers
                ):
                    kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_tokens,
                    }
                else:
                    print(
                        f"Warning: 'thinking' is not supported for model '{self.model}' (provider: {self.provider})."
                    )
            except Exception as e:
                print(
                    f"Warning: Could not check supports_reasoning for model '{self.model}': {e}"
                )
        if self.tools:
            kwargs["tools"] = self.tools

        # Always drop unsupported params to avoid errors
        litellm.drop_params = True

        # Try making the API call with retries
        for attempt in range(NUM_RETRIES):
            try:
                # Handle vLLM provider - no fallback
                if self.provider == "vllm":
                    response = await self._call_vllm(messages, kwargs)
                    break
                else:
                    # Make regular API call (LiteLLM is synchronous, so run in thread if needed)
                    import asyncio
                    loop = asyncio.get_event_loop()
                    response = await loop.run_in_executor(
                        None,
                        lambda: completion(
                            model=self.model,
                            messages=messages,
                            num_retries=0,  # We handle retries here
                            **kwargs,
                        ),
                    )
                    break
            except Exception as e:
                if attempt == NUM_RETRIES - 1:
                    return "", f"Error after {NUM_RETRIES} attempts: {str(e)}"
                await asyncio.sleep(1)  # Add delay between retries
                continue

        # Process the response
        try:
            thinking_content, assistant_message = self._process_response(response)
            return thinking_content, assistant_message
        except Exception as e:
            error_msg = f"Error: Unexpected response format from LiteLLM. Exception: {e}"
            print(error_msg)
            return "", error_msg

    def save_conversation(self):
        """Save the conversation history to a JSON file"""
        conversation_dicts = self.conversation_history
        conversation_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "total_messages": len(self.conversation_history),
                "model": self.model,
                "provider": self.provider,
            },
            "conversation": conversation_dicts,
        }
        with open(self.log_file, "w") as f:
            json.dump(conversation_data, f, indent=2)

    async def _call_vllm(self, messages, kwargs):
        """Make API call to vLLM server using call_llm_api"""
        # Convert kwargs to call_llm_api parameters
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        thinking = kwargs.get("thinking", None)
        
        # Call the working call_llm_api function
        result = await call_llm_api(
            messages=messages,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            thinking=thinking,
            caching=False,
        )
        
        # Convert result to litellm-compatible format
        from types import SimpleNamespace
        
        # Create a mock response that matches litellm's structure
        choice = SimpleNamespace()
        choice.message = SimpleNamespace()
        choice.message.content = result.response_text
        choice.message.reasoning_content = getattr(result, 'reasoning_content', '')
        choice.message.thinking_content = getattr(result, 'thinking_content', '')
        choice.message.tool_calls = []
        
        response = SimpleNamespace()
        response.choices = [choice]
        
        return response

    def _process_response(self, response):
        """Extract content and thinking from either vLLM or standard response"""
        choice = response.choices[0]
        message = choice.message
        
        # Get main content
        content = message.content
        
        # Extract thinking content 
        thinking = (
            getattr(message, "reasoning_content", "") or
            getattr(message, "thinking_content", "")
        )
        
        # Handle tool calls if present
        tool_calls = getattr(message, "tool_calls", [])
        if tool_calls and isinstance(tool_calls, list):
            print("\n🔧 Tool calls detected:")
            for tool_call in tool_calls:
                print(
                    f"Tool: {tool_call.function.name}, Arguments: {tool_call.function.arguments}"
                )
                tool_result = input(
                    f"Enter result for tool '{tool_call.function.name}': "
                )
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": tool_result,
                }
                self.conversation_history.append(tool_msg)
            return self.chat("")  # Continue conversation with tool results
            
        # Format the response
        full_response = content
        if thinking:
            full_response = f"<thinking>\n{thinking}\n</thinking>\n\n{content}"
        
        # Update conversation history
        assistant_msg = {"role": "assistant", "content": full_response}
        self.conversation_history.append(assistant_msg)
        self.save_conversation()
        
        return thinking, content

    def print_conversation_summary(self):
        """Print a summary of the conversation"""
        print("\n=== Conversation Summary ===")
        print(f"Total messages: {len(self.conversation_history)}")
        print(f"Log file: {self.log_file}")
        print(f"Model: {self.model_shortcut} ({self.model})")
        print(f"Provider: {self.provider}")
        temp_display = f"{self.temperature}"
        if (
            self.thinking_enabled
            and self.provider == "anthropic"
            and self.temperature == 1.0
        ):
            temp_display += " (overridden for thinking)"
        print(f"Temperature: {temp_display}")
        print(
            f"Thinking: {'enabled' if self.thinking_enabled else 'disabled'}{' (not supported by model)' if not self.model_supports_thinking and self.thinking_enabled == False else ''}"
        )
        print(
            f"System prompt: {self.system_prompt[:80]}{'...' if len(self.system_prompt) > 80 else ''}"
        )
        print("=" * 30)


async def main():
    """Main interactive chat loop"""
    parser = argparse.ArgumentParser(
        description="Chat with any model using the InferenceAPI"
    )
    parser.add_argument(
        "--model",
        "-m",
        default="claude-sonnet-4",
        choices=list(models.keys()) + ["custom"],
        help="Model to use (default: claude-sonnet-4)",
    )
    parser.add_argument(
        "--custom-model", help="Custom model ID (use with --model custom)"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=11000,
        help="Maximum tokens for response (default: 11000)",
    )
    parser.add_argument(
        "--thinking-tokens",
        type=int,
        default=10000,
        help="Thinking budget tokens (default: 10000)",
    )
    parser.add_argument(
        "--no-thinking", action="store_true", help="Disable thinking feature"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Temperature for sampling (default: 0.0)",
    )
    parser.add_argument(
        "--enable-tools",
        action="store_true",
        help="Enable tool/function calling support",
    )
    args = parser.parse_args()

    # Determine the model to use
    if args.model == "custom":
        if not args.custom_model:
            print("❌ Error: --custom-model is required when using --model custom")
            return
        model_to_use = args.custom_model
    else:
        model_to_use = args.model

    print("🤖 Model Chat")
    print(f"Model: {model_to_use}")
    print("Type 'quit' or 'exit' to end the conversation")
    print("Type 'summary' to see conversation summary")

    # Show thinking support info
    thinking_models = [
        name for name, config in models.items() if config.get("thinking", False)
    ]
    if thinking_models:
        print(f"Models with thinking support: {', '.join(thinking_models)}")

    # Show available models by provider
    providers = {}
    for name, config in models.items():
        provider = config["org"]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(name)

    print("\nAvailable models by provider:")
    for provider, model_list in providers.items():
        print(f"  {provider}: {', '.join(model_list)}")

    print("-" * 40)

    # Get configuration from arguments or environment variables
    max_tokens = args.max_tokens or int(os.getenv("MODEL_MAX_TOKENS", "11000"))
    thinking_tokens = args.thinking_tokens or int(
        os.getenv("MODEL_THINKING_TOKENS", "10000")
    )
    thinking_enabled = (
        not args.no_thinking
        and os.getenv("MODEL_THINKING_ENABLED", "true").lower() == "true"
    )
    temperature = args.temperature or float(os.getenv("MODEL_TEMPERATURE", "0.0"))

    # Prompt user for system prompt file
    system_prompt = None
    while True:
        system_prompt_file = input(
            "📝 Enter path to system prompt file (or press Enter for default): "
        ).strip()
        if not system_prompt_file:
            system_prompt = "You are a helpful AI assistant. It is your job to assist the user with their request and ensure that the user is satisfied with your response."
            print("📝 Using default system prompt")
            break
        try:
            with open(system_prompt_file, "r", encoding="utf-8") as f:
                system_prompt = f.read().strip()
            print(f"📝 Loaded system prompt from: {system_prompt_file}")
            print(
                f"📝 System Prompt: {system_prompt[:100]}{'...' if len(system_prompt) > 100 else ''}"
            )
            break
        except FileNotFoundError:
            print(f"❌ File not found: {system_prompt_file}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != "y":
                system_prompt = "You are a helpful AI assistant. It is your job to assist the user with their request and ensure that the user is satisfied with your response."
                print("📝 Using default system prompt")
                break
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry != "y":
                system_prompt = "You are a helpful AI assistant. It is your job to assist the user with their request and ensure that the user is satisfied with your response."
                print("📝 Using default system prompt")
                break

    # Show thinking status
    if thinking_enabled:
        print(f"🧠 Thinking enabled (budget: {thinking_tokens} tokens)")
    else:
        print("🧠 Thinking disabled")
    print(f"🌡️ Temperature: {temperature}")
    print("-" * 40)

    # Tool support
    tools = []
    if args.enable_tools:
        # Example tool for demonstration
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_time",
                    "description": "Get the current time in UTC.",
                    "parameters": {"type": "object", "properties": {}, "required": []},
                },
            }
        ]

    try:
        chatter = ModelChatter(
            thinking_enabled=thinking_enabled,
            max_tokens=max_tokens,
            thinking_tokens=thinking_tokens,
            system_prompt=system_prompt,
            model=model_to_use,
            temperature=temperature,
            tools=tools,
        )
    except ValueError as e:
        print(f"❌ {e}")
        print("Please set your API key environment variable:")
        if model_to_use in models:
            provider = models[model_to_use]["org"]
            if provider == "anthropic":
                print("export ANTHROPIC_API_KEY='your-api-key-here'")
            elif provider == "openai":
                print("export OPENAI_API_KEY='your-api-key-here'")
            else:
                print(f"export {provider.upper()}_API_KEY='your-api-key-here'")
        print("\nOptional: Set a custom system prompt:")
        print("export MODEL_SYSTEM_PROMPT='Your custom system prompt here'")
        return

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                chatter.print_conversation_summary()
                print("👋 Goodbye!")
                break

            if user_input.lower() == "summary":
                chatter.print_conversation_summary()
                continue

            if not user_input:
                continue

            print("\n🤖 Assistant: ", end="", flush=True)
            thinking_content, response = await chatter.chat(user_input)

            # Display thinking content if present
            if thinking_content:
                print(f"\n🧠 Thinking:\n{thinking_content}")
                print(f"\n💬 Response:\n{response}")
            else:
                print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted by user. Saving conversation...")
            chatter.print_conversation_summary()
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
