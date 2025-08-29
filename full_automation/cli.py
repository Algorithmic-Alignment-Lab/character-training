import argparse
import json
import os
import sys
from dataclasses import asdict

from .runner import WorkflowConfig, run_workflow
from .models import ALLOWED_MODELS


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="End-to-end automation CLI (interactive or non-interactive)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    # Non-interactive flags (allow piping for tests)
    p.add_argument("--character-id", help="Unique character key in character_definitions.json")
    p.add_argument("--name", help="Character display name")
    p.add_argument("--version", default="Original")
    p.add_argument("--system-prompt", help="Base system prompt text")
    p.add_argument("--enhancer-model", default="anthropic/claude-sonnet-4-20250514", choices=list(ALLOWED_MODELS.keys()))
    p.add_argument("--total-chats", type=int, default=1000)
    p.add_argument("--ft-model", default="Qwen/Qwen3-32B")
    p.add_argument("--teacher-model-eval", default="claude-sonnet-4")
    p.add_argument("--student-model-eval", default="qwen3-1.7b")
    p.add_argument("--num-workers", type=int, default=10)
    p.add_argument("--max-concurrent", type=int, default=30)
    p.add_argument("--num-variations", type=int, default=5)
    p.add_argument("--iterations-per-variation", type=int, default=1)
    p.add_argument("--character-full-for-eval")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--yes", action="store_true", help="Auto-approve interactive steps")
    return p.parse_args(argv)


def maybe_interactive(args):
    # If any of the required base fields are missing, prompt interactively
    missing = []
    if not args.character_id: missing.append("character_id")
    if not args.name: missing.append("name")
    if not args.system_prompt: missing.append("system_prompt")
    if not missing:
        return args

    print("Interactive mode: fill missing fields. Press Enter to accept defaults.")
    if not args.character_id:
        args.character_id = input("character_id: ").strip()
    if not args.name:
        args.name = input("name: ").strip()
    if not args.system_prompt:
        print("Paste system prompt, end with Ctrl-D:")
        args.system_prompt = sys.stdin.read().strip() if not sys.stdin.isatty() else input(": ")
    return args


def main(argv=None):
    args = parse_args(argv)
    args = maybe_interactive(args)

    cfg = WorkflowConfig(
        character_id=args.character_id,
        base_name=args.name,
        base_version=args.version,
        base_system_prompt=args.system_prompt,
        ai_enhancer_model=args.enhancer_model,
        total_chats_target=args.total_chats,
        ft_model=args.ft_model,
        teacher_model_eval=args.teacher_model_eval,
        student_model_eval=args.student_model_eval,
        num_workers=args.num_workers,
        max_concurrent=args.max_concurrent,
        num_variations=args.num_variations,
        iterations_per_variation=args.iterations_per_variation,
        character_full_for_eval=args.character_full_for_eval,
        dry_run=args.dry_run,
    )

    # Auto-approve steps controlled inside runner (we default to approve True)
    run_workflow(cfg)
    print("Workflow completed.")


if __name__ == "__main__":
    main()
