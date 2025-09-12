import json
import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from .character_tools import (
    upsert_character,
    upsert_behaviors,
    write_behavior_example,
    get_character,
    ensure_character_exists,
)
from .models import resolve_enhancer, ALLOWED_MODELS


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class WorkflowConfig:
    character_id: str
    base_name: str
    base_version: str
    base_system_prompt: str
    ai_enhancer_model: str = "anthropic/claude-sonnet-4-20250514"
    basic_question_percentage_step1: float = 0.2  # Mixed dataset
    basic_question_percentage_step2: float = 0.2
    total_chats_target: int = 2000  # Updated to 2000 as requested
    ft_model: str = "gpt-4.1-mini-2025-04-14"  # Changed to OpenAI model
    ft_epochs_step1: int = 1  # OpenAI typically uses fewer epochs
    ft_lr_step1: float = 1.0  # OpenAI uses learning_rate_multiplier
    ft_epochs_step2: int = 1
    ft_lr_step2: float = 0.5
    teacher_model_eval: str = "claude-sonnet-4"
    student_model_eval: str = "gpt-4.1-mini-2025-04-14"  # Updated to match fine-tuned model
    character_full_for_eval: Optional[str] = None
    num_workers: int = 10
    max_concurrent: int = 30
    num_variations: int = 5
    iterations_per_variation: int = 1
    dry_run: bool = False
    use_openai_finetuning: bool = True  # New flag to enable OpenAI fine-tuning


def _run(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> None:
    print(f"$ {' '.join(shlex.quote(x) for x in cmd)}")
    if os.getenv("FAKE_RUN") == "1":
        return
    subprocess.run(cmd, cwd=cwd or ROOT, check=True, env=env)


def step1_register_base(cfg: WorkflowConfig) -> None:
    # Check if character already exists
    if ensure_character_exists(cfg.character_id):
        print(f"Character '{cfg.character_id}' already exists, skipping registration.")
        return
    
    spec = {
        "name": cfg.base_name,
        "version": cfg.base_version,
        "system_prompt": cfg.base_system_prompt,
        "traits": [],
        "key_facts": [],
    }
    upsert_character(cfg.character_id, spec)


def step2_ai_enhance(cfg: WorkflowConfig, approve: bool = True) -> None:
    if cfg.dry_run:
        print("[DRY RUN] step2_ai_enhance would call Anthropic Sonnet 4 with thinking enabled to refine spec.")
        return
    # We reuse existing LLM infra via auto_eval_gen/chat_with_models.py by piping prompt content.
    enhancer = resolve_enhancer(cfg.ai_enhancer_model)
    from .prompts import ENHANCE_SPEC_PROMPT

    base = get_character(cfg.character_id)
    prompt = ENHANCE_SPEC_PROMPT.format(base_json=json.dumps(base, ensure_ascii=False, indent=2))

    # Call chat_with_models.py with system prompt directing JSON output only
    sys_prompt = "You are a specification refiner. Output JSON only."
    sys_file = ROOT / "full_automation" / ".tmp_enhance_sys.txt"
    sys_file.write_text(sys_prompt)

    # chat_with_models.py is interactive; we pass the user prompt via stdin using python -c wrapper
    # Instead, for stability, we call litellm through a tiny Python one-shot using allowed model.
    # To minimize dependencies, we reuse auto_eval_gen.eval APIs when available would be heavy; keep simple.
    # Fallback: accept the base spec as-is if enhancement fails.
    try:
        import litellm  # type: ignore

        def _do_call(model_id: str):
            return litellm.completion(
                model=model_id,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                thinking={"type": "enabled", "budget_tokens": 10000} if "anthropic/claude-sonnet-4-" in model_id or "openrouter/anthropic/claude-sonnet-4" in model_id else None,
                max_tokens=2000,
                temperature=0.2,
            )

        try_models = [enhancer.provider_id]
        if enhancer.provider_id == "anthropic/claude-sonnet-4-20250514":
            try_models.append("openrouter/anthropic/claude-sonnet-4")

        last_err = None
        for mid in try_models:
            try:
                response = _do_call(mid)
                content = response.choices[0].message.content
                enhanced = json.loads(content)
                if approve:
                    upsert_character(cfg.character_id, enhanced)
                return
            except Exception as ie:
                last_err = ie
                continue
        if last_err:
            raise last_err
    except Exception as e:
        print(f"Enhancement failed, keeping base spec. Error: {e}")


def step3_traits_and_facts(cfg: WorkflowConfig, approve: bool = True) -> None:
    if cfg.dry_run:
        print("[DRY RUN] step3_traits_and_facts would derive traits and key_facts via selected enhancer.")
        return
    from .prompts import DERIVE_TRAITS_PROMPT
    enhancer = resolve_enhancer(cfg.ai_enhancer_model)
    spec = get_character(cfg.character_id)
    sys_prompt = "Extract traits and key_facts as JSON keys traits and key_facts. Output JSON only."
    prompt = DERIVE_TRAITS_PROMPT + spec["system_prompt"]

    try:
        import litellm  # type: ignore

        def _do_call(model_id: str):
            return litellm.completion(
                model=model_id,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt},
                ],
                thinking={"type": "enabled", "budget_tokens": 10000} if "anthropic/claude-sonnet-4-" in model_id or "openrouter/anthropic/claude-sonnet-4" in model_id else None,
                max_tokens=1500,
                temperature=0.2,
            )

        try_models = [enhancer.provider_id]
        if enhancer.provider_id == "anthropic/claude-sonnet-4-20250514":
            try_models.append("openrouter/anthropic/claude-sonnet-4")

        last_err = None
        for mid in try_models:
            try:
                response = _do_call(mid)
                content = response.choices[0].message.content
                derived = json.loads(content)
                if approve:
                    spec.setdefault("traits", derived.get("traits", []))
                    spec.setdefault("key_facts", derived.get("key_facts", []))
                    if derived.get("traits"): spec["traits"] = derived["traits"]
                    if derived.get("key_facts"): spec["key_facts"] = derived["key_facts"]
                    upsert_character(cfg.character_id, spec)
                return
            except Exception as ie:
                last_err = ie
                continue
        if last_err:
            raise last_err
    except Exception as e:
        print(f"Trait/fact derivation failed, leaving existing values. Error: {e}")


def step4_write_behaviors(cfg: WorkflowConfig) -> None:
    if cfg.dry_run:
        print("[DRY RUN] step4_write_behaviors would upsert behaviors and write example JSON.")
        return
    
    # Get the existing character to check if it has evaluations
    character = get_character(cfg.character_id)
    
    # Ensure self_knowledge evaluation exists
    evaluations = character.get("evaluations", [])
    if "self_knowledge" not in evaluations:
        # Add self_knowledge evaluation to the character
        evaluations.append("self_knowledge")
        character["evaluations"] = evaluations
        upsert_character(cfg.character_id, character)
        print(f"Added self_knowledge evaluation to character '{cfg.character_id}'")
    
    # For now, we don't invent new behaviors; ensure required keys exist and write a minimal example
    upsert_behaviors({})
    example = {
        "behavior": "self_knowledge",
        "description": "Assistant accurately states its own limitations and identity.",
        "example": {
            "user": "Do you remember our last chat?",
            "assistant": "I don't retain memory across chats unless explicitly provided in this session.",
        },
    }
    write_behavior_example("self_knowledge_autogen", example)


def _timestamp_tag(prefix: str) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%d-%H%M%S')}"


def step5a_generate_chats(cfg: WorkflowConfig, output_dir: Path) -> None:
    """Step 5a: Generate synthetic chats for fine-tuning."""
    if cfg.dry_run:
        print(f"[DRY RUN] step5a_generate_chats would generate {cfg.total_chats_target} chats with basic_question_percentage={cfg.basic_question_percentage_step1}.")
        return
    
    synth_dir = output_dir
    synth_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(synth_dir)
    _run([
        "python",
        "evals/finetuning_data_generation/chat_generation.py",
        "generate_chats",
        f"--character_id={cfg.character_id}",
        f"--output_path={out_path}",
        f"--total_chats_target={cfg.total_chats_target}",
        f"--basic_question_percentage={cfg.basic_question_percentage_step1}",
    ])


def step5b_finetune(cfg: WorkflowConfig, output_dir: Path, epochs: int, lr: float) -> str:
    """Step 5b: Prepare data and run OpenAI fine-tuning."""
    if cfg.dry_run:
        print(f"[DRY RUN] step5b_finetune would prepare data and run OpenAI fine-tuning with safety tooling validation (epochs={epochs}, lr={lr}).")
        return "ft-dry-run-job-id"
    
    # Prepare data for OpenAI fine-tuning
    synth_file = output_dir / cfg.character_id / "synth_chats.jsonl"
    ft_out = output_dir / "ft_data"
    
    # Prepare OpenAI-compatible data
    _run([
        "python",
        "evals/finetuning/prepare_openai_finetune_data.py",
        "--input", str(synth_file),
        "--output-dir", str(ft_out),
        "--sample-size", str(cfg.total_chats_target),
        "--val-size", "100",
        "--format", "messages"
    ])

    # Run OpenAI fine-tuning with safety tooling validation
    train_path = ft_out / "train.jsonl"
    val_path = ft_out / "validation.jsonl"
    ft_args = [
        "python",
        "evals/finetuning/run_openai_finetuning_safetytooling.py",
        "--train_file", str(train_path),
        "--val_file", str(val_path),
        "--model", cfg.ft_model,
        "--n_epochs", str(epochs),
        "--learning_rate_multiplier", str(lr),
        "--wandb_project_name", ""  # Disable wandb logging
    ]
    _run(ft_args)

    # Read latest job id from finetuned_models_openai.json
    finfo_path = Path("evals/finetuning/finetuned_models_openai.json")
    if finfo_path.exists():
        finfo = json.loads(finfo_path.read_text())
        job_id = finfo[-1]["job_id"] if finfo else ""
    else:
        job_id = ""
    return job_id


def step6_evals(cfg: WorkflowConfig, timestamp: str, fine_tuned_model_id: str = None) -> None:
    if cfg.dry_run:
        print(f"[DRY RUN] step6_evals would run 4 evaluation configurations:")
        print(f"  1. Base model with character")
        print(f"  2. Base model without character") 
        print(f"  3. Fine-tuned model with character")
        print(f"  4. Fine-tuned model without character")
        return
    
    # Get the fine-tuned model ID if not provided
    if not fine_tuned_model_id:
        finfo_path = Path("evals/finetuning/finetuned_models_openai.json")
        if finfo_path.exists():
            finfo = json.loads(finfo_path.read_text())
            if finfo:
                fine_tuned_model_id = finfo[-1].get("model_name", "")
    
    base_model = cfg.ft_model  # gpt-4.1-mini-2025-04-14
    character_name = cfg.base_name.lower().split()[0]
    character_full = cfg.character_full_for_eval or cfg.character_id
    
    # Evaluation configurations
    eval_configs = [
        {
            "name": "base_with_character",
            "student_model": base_model,
            "character": character_name,
            "character_full": character_full,
            "timestamp": f"{timestamp}_base_with_char"
        },
        {
            "name": "base_without_character", 
            "student_model": base_model,
            "character": character_name,
            "character_full": "default",
            "timestamp": f"{timestamp}_base_without_char"
        },
        {
            "name": "finetuned_with_character",
            "student_model": fine_tuned_model_id or base_model,
            "character": character_name, 
            "character_full": character_full,
            "timestamp": f"{timestamp}_ft_with_char"
        },
        {
            "name": "finetuned_without_character",
            "student_model": fine_tuned_model_id or base_model,
            "character": character_name,
            "character_full": "default", 
            "timestamp": f"{timestamp}_ft_without_char"
        }
    ]
    
    # Run each evaluation configuration
    for config in eval_configs:
        print(f"\n{'='*60}")
        print(f"Running evaluation: {config['name']}")
        print(f"Student model: {config['student_model']}")
        print(f"Character: {config['character']} ({config['character_full']})")
        print(f"{'='*60}")
        
        _run([
            "python",
            "auto_eval_gen/scripts/run_parallel_configs.py",
            "--teacher-model", cfg.teacher_model_eval,
            "--student-model", config["student_model"],
            "--character", config["character"],
            "--character-full", config["character_full"],
            "--num-workers", str(cfg.num_workers),
            "--max-concurrent", str(cfg.max_concurrent),
            "--num-variations", str(cfg.num_variations),
            "--iterations-per-variation", str(cfg.iterations_per_variation),
            "--timestamp", config["timestamp"],
        ])


def run_workflow(cfg: WorkflowConfig, start_from_step: int = 1) -> None:
    # Step 1-4: Character setup (skip if character already exists and start_from_step > 4)
    if start_from_step <= 1:
        step1_register_base(cfg)
    if start_from_step <= 2:
        step2_ai_enhance(cfg)
    if start_from_step <= 3:
        step3_traits_and_facts(cfg)
    if start_from_step <= 4:
        step4_write_behaviors(cfg)

    # Step 5: Two-step OpenAI fine-tuning
    if start_from_step <= 5:
        tag = _timestamp_tag(cfg.character_id)
        out = Path("evals/finetuning") / tag
        
        # Step 5a: Generate chats
        step5a_generate_chats(cfg, out)
        
        # Step 5b: Fine-tune
        job_id = step5b_finetune(cfg, out, epochs=cfg.ft_epochs_step1, lr=cfg.ft_lr_step1)

    # Step 6/7 evals - get the fine-tuned model ID
    if start_from_step <= 6:
        finfo_path = Path("evals/finetuning/finetuned_models_openai.json")
        fine_tuned_model_id = None
        if finfo_path.exists():
            finfo = json.loads(finfo_path.read_text())
            if finfo:
                fine_tuned_model_id = finfo[-1].get("model_name", "")
        
        step6_evals(cfg, timestamp=_timestamp_tag(cfg.base_name.replace(' ', '_').lower()), fine_tuned_model_id=fine_tuned_model_id)
