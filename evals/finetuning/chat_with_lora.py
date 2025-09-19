#!/usr/bin/env python3
"""
Interactive CLI to chat with any open source model using LoRA adapters via Hugging Face transformers.

Features:
- Auto-selects device (CUDA > MPS > CPU) unless overridden.
- Optional 4-bit / 8-bit quantization via bitsandbytes (if installed).
- Uses chat template when available; otherwise falls back to plain prompt.
- Supports any Hugging Face model with LoRA adapters.

Usage examples:
  # Chat with a base model
  python evals/finetuning/chat_with_lora.py --base-model Qwen/Qwen3-1.7B --chat

  # Chat with a LoRA adapter
  python evals/finetuning/chat_with_lora.py \
      --base-model Qwen/Qwen3-1.7B \
      --lora-adapter rpotham/ft-a75feb26-e7a9-2025-09-12-19-30-04 \
      --chat

  # Single message test
  python evals/finetuning/chat_with_lora.py \
      --base-model Qwen/Qwen3-1.7B \
      --lora-adapter rpotham/ft-a75feb26-e7a9-2025-09-12-19-30-04 \
      --message "Hello, how are you?"

  # With quantization for lower memory usage
  python evals/finetuning/chat_with_lora.py \
      --base-model Qwen/Qwen3-1.7B \
      --lora-adapter rpotham/ft-a75feb26-e7a9-2025-09-12-19-30-04 \
      --load-in-4bit \
      --chat

  # Longer replies (avoid cutoff)
  python evals/finetuning/chat_with_lora.py \
      --base-model Qwen/Qwen3-1.7B \
      --lora-adapter rpotham/ft-a75feb26-e7a9-2025-09-12-19-30-04 \
      --chat --max-new-tokens 2048

Commands available in chat mode:
  exit, :q, quit - exit the chat
  /help          - show this help

Note: The first run will download model weights. Ensure you have sufficient disk and RAM/VRAM.
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional
import re

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
)


def resolve_device(device_arg: str) -> str:
    if device_arg != "auto":
        return device_arg
    if torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def resolve_dtype(dtype_arg: str, device: str) -> Optional[torch.dtype]:
    if dtype_arg == "auto":
        if device in ("cuda", "mps"):
            return torch.float16
        return torch.float32
    mapping = {
        "float16": torch.float16,
        "bfloat16": torch.bfloat16,
        "float32": torch.float32,
    }
    return mapping.get(dtype_arg, None)


def build_quant_config(load_in_4bit: bool, load_in_8bit: bool):
    if not (load_in_4bit or load_in_8bit):
        return None
    try:
        from transformers import BitsAndBytesConfig  # type: ignore
    except Exception as e:  # pragma: no cover - optional dependency
        print(
            "bitsandbytes not available. Install it to use 4/8-bit quantization (e.g., pip install bitsandbytes).",
            file=sys.stderr,
        )
        return None
    return BitsAndBytesConfig(
        load_in_4bit=load_in_4bit,
        load_in_8bit=load_in_8bit,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )


def main():
    parser = argparse.ArgumentParser(description="Chat with any open source model using LoRA adapters")
    parser.add_argument(
        "--base-model",
        default="Qwen/Qwen3-1.7B",
        help="Hugging Face base model repo id",
    )
    parser.add_argument(
        "--lora-adapter",
        type=str,
        default=None,
        help="Hugging Face repo id for a PEFT LoRA adapter to load on top of the base model",
    )
    parser.add_argument(
        "--prompt",
        default="Say hello in one short sentence.",
        help="User prompt for a short test generation",
    )
    parser.add_argument(
        "--max-new-tokens",
        type=int,
        default=-1,
        help="Maximum new tokens to generate (<=0 means 1024)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        default=0.95,
        help="Top-p nucleus sampling",
    )
    parser.add_argument(
        "--min-new-tokens",
        type=int,
        default=0,
        help="Minimum number of new tokens to generate (0 to disable)",
    )
    parser.add_argument(
        "--device",
        choices=["auto", "cpu", "cuda", "mps"],
        default="auto",
        help="Device selection",
    )
    parser.add_argument(
        "--dtype",
        choices=["auto", "float16", "bfloat16", "float32"],
        default="auto",
        help="Torch dtype for weights (ignored if 4/8-bit)",
    )
    parser.add_argument(
        "--load-in-4bit",
        action="store_true",
        help="Load model in 4-bit quantization (requires bitsandbytes)",
    )
    parser.add_argument(
        "--load-in-8bit",
        action="store_true",
        help="Load model in 8-bit quantization (requires bitsandbytes). If neither --load-in-4bit nor --load-in-8bit is set and CUDA is available, 8-bit will be auto-enabled.",
    )
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="Trust remote code when loading the model/tokenizer",
    )
    parser.add_argument(
        "--merge-and-unload",
        action="store_true",
        help="Attempt to merge LoRA weights into the base model and unload adapters (may not be supported on all devices)",
    )
    parser.add_argument(
        "--system-prompt",
        type=str,
        default="You are a helpful assistant.",
        help="System prompt used in chat mode",
    )
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Start an interactive chat CLI. Use --message to run a single turn and exit (for non-interactive testing)",
    )
    parser.add_argument(
        "--message",
        type=str,
        default=None,
        help="Single user message when using --chat; if provided, runs one turn and exits",
    )
    parser.add_argument(
        "--keep-think",
        action="store_true",
        help="Keep <think> sections in the output (by default they are stripped)",
    )
    parser.add_argument(
        "--no-eos-stop",
        action="store_true",
        help="Do not stop generation on EOS token; generation will stop only at max tokens",
    )

    args = parser.parse_args()

    device = resolve_device(args.device)
    dtype = resolve_dtype(args.dtype, device)

    # Default to 8-bit on CUDA if user didn't request a specific quantization
    auto_enabled_8bit = False
    if (not args.load_in_4bit and not args.load_in_8bit) and device == "cuda":
        try:
            from transformers import BitsAndBytesConfig  # noqa: F401
            args.load_in_8bit = True
            auto_enabled_8bit = True
        except Exception:
            pass

    quant_config = build_quant_config(args.load_in_4bit, args.load_in_8bit)

    print(
        f"Loading model: base_model={args.base_model} lora_adapter={args.lora_adapter} "
        f"device={device} dtype={dtype} 4bit={args.load_in_4bit} 8bit={args.load_in_8bit} auto8bit={auto_enabled_8bit}"
    )

    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=args.trust_remote_code,
        use_fast=True,
    )

    # On MPS or when loading LoRA adapters, avoid accelerate's device_map auto
    use_device_map_auto = (
        (device == "cuda") and (not args.lora_adapter)
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        device_map="auto" if use_device_map_auto else None,
        torch_dtype=None if quant_config is not None else dtype,
        quantization_config=quant_config,
        trust_remote_code=args.trust_remote_code,
        low_cpu_mem_usage=True,
    )
    if not use_device_map_auto:
        model.to(device)

    # Optionally load a LoRA adapter
    if args.lora_adapter:
        try:
            from peft import PeftModel
        except Exception as e:
            print(
                "PEFT is required for LoRA adapters. Please install with: pip install peft",
                file=sys.stderr,
            )
            raise
        print(f"Loading LoRA adapter: {args.lora_adapter}")
        model = PeftModel.from_pretrained(
            model,
            args.lora_adapter,
            device_map=None,  # keep control of placement
            torch_dtype=dtype,
        )
        model.to(device)
        if args.merge_and_unload:
            try:
                model = model.merge_and_unload()
                print("Merged LoRA into base weights and unloaded adapters.")
            except Exception as e:
                print(f"Warning: merge_and_unload failed or unsupported: {e}", file=sys.stderr)

    # Some models don't define a pad token; set pad to eos to avoid warnings.
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    def strip_think_blocks(text: str) -> str:
        if args.keep_think:
            return text
        return re.sub(r"<think>[\s\S]*?</think>", "", text).strip()

    def generate_once(messages_or_prompt: str | list[dict]):
        max_new = args.max_new_tokens if args.max_new_tokens and args.max_new_tokens > 0 else 1024
        # Prefer chat template if present and messages provided
        try:
            if isinstance(messages_or_prompt, list) and hasattr(tokenizer, "apply_chat_template") and tokenizer.chat_template:
                input_ids_local = tokenizer.apply_chat_template(
                    messages_or_prompt,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt",
                )
            else:
                raise AttributeError
        except Exception:
            # Fallback: plain prompt
            input_ids_local = tokenizer(
                messages_or_prompt if isinstance(messages_or_prompt, str) else messages_or_prompt[-1]["content"],
                return_tensors="pt",
                add_special_tokens=True,
            ).input_ids

        input_ids_local = input_ids_local.to(model.device)
        gen_kwargs = dict(
            input_ids=input_ids_local,
            max_new_tokens=max_new,
            do_sample=True,
            temperature=args.temperature,
            top_p=args.top_p,
            pad_token_id=tokenizer.pad_token_id,
        )
        if args.min_new_tokens and args.min_new_tokens > 0:
            gen_kwargs["min_new_tokens"] = args.min_new_tokens
        if not args.no_eos_stop:
            gen_kwargs["eos_token_id"] = tokenizer.eos_token_id

        with torch.no_grad():
            outputs_local = model.generate(**gen_kwargs)
        gen_tokens = outputs_local[0][gen_kwargs["input_ids"].shape[-1]:]
        out = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
        return strip_think_blocks(out)

    # Interactive chat mode or single-shot
    if args.chat:
        messages = [
            {"role": "system", "content": args.system_prompt},
        ]
        if args.message is not None:
            messages.append({"role": "user", "content": args.message})
            reply = generate_once(messages)
            print("\n=== Assistant ===\n" + reply)
            return

        print("Entering chat mode. Type 'exit', ':q', or 'quit' to quit.\n")
        while True:
            try:
                user_in = input("You: ").strip()
            except EOFError:
                break
            if not user_in or user_in.lower() in {"exit", ":q", "quit"}:
                break
            messages.append({"role": "user", "content": user_in})
            reply = generate_once(messages)
            messages.append({"role": "assistant", "content": reply})
            print("\nAssistant: " + reply + "\n")
        return

    # One-off non-interactive generation using --prompt
    text = generate_once(args.prompt)
    print("\n=== Generation ===")
    print(text)
    print(f"\nSUCCESS: {args.base_model} loaded and generated text.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
