#!/usr/bin/env python3
"""
Wrapper CLI that re-uses safetytooling's OpenAI fine-tuning flow.

This script imports the `OpenAIFTConfig` dataclass and `main` coroutine
from `safetytooling.apis.finetuning.openai.run` and exposes the same
arguments via `simple_parsing` so you can run the safetytooling pipeline
from this repo's top-level CLI.

Example:

export OPENAI_API_KEY="sk-..."
python evals/finetuning/run_openai_finetuning_safetytooling.py \
  --train_file evals/finetuning/sample_openai_messages/train.jsonl \
  --val_file evals/finetuning/sample_openai_messages/validation.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 --learning_rate_multiplier 1e-4 \
  --wandb_project_name myproj --wandb_entity myentity

This will perform validation, upload files, queue the fine-tune, and
log the run to wandb (if configured) using the safety tooling helper.
"""

from __future__ import annotations

import asyncio
import sys

from simple_parsing import ArgumentParser

try:
    from safetytooling.apis.finetuning.openai.run import OpenAIFTConfig, main as safety_main
    from safetytooling.utils import utils as st_utils
except Exception as e:
    print("Failed to import safetytooling modules. Make sure safetytooling is on PYTHONPATH and installed.")
    raise


def cli_entry():
    parser = ArgumentParser(description="Run OpenAI fine-tuning using safetytooling flow")
    parser.add_arguments(OpenAIFTConfig, dest="cfg")
    args = parser.parse_args()
    cfg: OpenAIFTConfig = args.cfg

    # Mirror safetytooling's environment setup
    try:
        st_utils.setup_environment(openai_tag=getattr(cfg, 'openai_tag', None), logging_level=getattr(cfg, 'logging_level', None))
    except Exception:
        # setup_environment is convenience; not fatal if it fails here
        pass

    # Run the async safety tooling main
    try:
        asyncio.run(safety_main(cfg))
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        raise


if __name__ == '__main__':
    cli_entry()
