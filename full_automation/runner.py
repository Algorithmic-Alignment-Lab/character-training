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
    basic_question_percentage_step1: float = 1.0
    basic_question_percentage_step2: float = 0.2
    total_chats_target: int = 1000
    ft_model: str = "Qwen/Qwen3-32B"
    ft_epochs_step1: int = 3
    ft_lr_step1: float = 3e-5
    ft_epochs_step2: int = 2
    ft_lr_step2: float = 5e-6
    teacher_model_eval: str = "claude-sonnet-4"
    student_model_eval: str = "qwen3-1.7b"
    character_full_for_eval: Optional[str] = None
    num_workers: int = 10
    max_concurrent: int = 30
    num_variations: int = 5
    iterations_per_variation: int = 1
    dry_run: bool = False


def _run(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> None:
    print(f"$ {' '.join(shlex.quote(x) for x in cmd)}")
    if os.getenv("FAKE_RUN") == "1":
        return
    subprocess.run(cmd, cwd=cwd or ROOT, check=True, env=env)


def step1_register_base(cfg: WorkflowConfig) -> None:
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


def step5_finetune_round(cfg: WorkflowConfig, output_dir: Path, parquet: bool, epochs: int, lr: float, from_checkpoint: Optional[str] = None) -> str:
    if cfg.dry_run:
        print(f"[DRY RUN] step5_finetune_round would run chat_generation -> prepare_data (parquet={parquet}) -> run_finetuning (epochs={epochs}, lr={lr}, from_checkpoint={from_checkpoint}).")
        return "ft-dry-run-job-id"
    # 5.1 Generate chats
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
        f"--basic_question_percentage={cfg.basic_question_percentage_step1 if not from_checkpoint else cfg.basic_question_percentage_step2}",
    ])

    # 5.2 Prepare data
    synth_file = synth_dir / cfg.character_id / "synth_chats.jsonl"
    ft_out = output_dir / "ft_data"
    args = [
        "python",
        "evals/finetuning/prepare_data_from_batch_generation.py",
        str(synth_file),
        "--output_dir",
        str(ft_out),
        "--model",
        cfg.ft_model,
    ]
    if parquet:
        args.append("--parquet")
    _run(args)

    # 5.3 Run finetuning
    train_path = ft_out / ("train.parquet" if parquet else "train.jsonl")
    ft_args = [
        "python",
        "evals/finetuning/run_finetuning.py",
        "--model",
        cfg.ft_model,
        "--train_file",
        str(train_path),
        "--n_epochs",
        str(epochs),
        "--learning_rate",
        str(lr),
    ]
    if parquet:
        ft_args.append("--parquet")
    if from_checkpoint:
        ft_args.extend(["--from_checkpoint", from_checkpoint])
    _run(ft_args)

    # Read latest job id from finetuned_models.json
    finfo = json.loads(Path("evals/finetuning/finetuned_models.json").read_text())
    job_id = finfo[-1]["job_id"] if finfo else ""
    return job_id


def step6_evals(cfg: WorkflowConfig, timestamp: str) -> None:
    if cfg.dry_run:
        print(f"[DRY RUN] step6_evals would run run_parallel_configs with teacher={cfg.teacher_model_eval}, student={cfg.student_model_eval}, character={cfg.base_name.lower().split()[0]}, timestamp={timestamp}.")
        return
    # copy_folders can adjust prompts; keep as optional
    try:
        _run(["python", "copy_folders.py", "--input", "1.7b-eval", "--output", "1.7b-eval-no-system-prompt", "--replace"])
    except Exception:
        print("copy_folders.py failed or not needed; continuing")

    # Run parallel configs
    _run([
        "python",
        "auto_eval_gen/scripts/run_parallel_configs.py",
        "--teacher-model",
        cfg.teacher_model_eval,
        "--student-model",
        cfg.student_model_eval,
        "--character",
        cfg.base_name.lower().split()[0],
        "--character-full",
        cfg.character_full_for_eval or cfg.character_id,
        "--num-workers",
        str(cfg.num_workers),
        "--max-concurrent",
        str(cfg.max_concurrent),
        "--num-variations",
        str(cfg.num_variations),
        "--iterations-per-variation",
        str(cfg.iterations_per_variation),
        "--timestamp",
        timestamp,
    ])


def run_workflow(cfg: WorkflowConfig) -> None:
    # Step 1-4
    step1_register_base(cfg)
    step2_ai_enhance(cfg)
    step3_traits_and_facts(cfg)
    step4_write_behaviors(cfg)

    # Step 5 round 1
    tag1 = _timestamp_tag(cfg.character_id)
    out1 = Path("evals/finetuning") / tag1
    job1 = step5_finetune_round(cfg, out1, parquet=True, epochs=cfg.ft_epochs_step1, lr=cfg.ft_lr_step1)

    # Step 5 round 2 from checkpoint
    tag2 = _timestamp_tag(cfg.character_id)
    out2 = Path("evals/finetuning") / tag2
    _ = step5_finetune_round(cfg, out2, parquet=True, epochs=cfg.ft_epochs_step2, lr=cfg.ft_lr_step2, from_checkpoint=job1)

    # Step 6/7 evals
    step6_evals(cfg, timestamp=_timestamp_tag(cfg.base_name.replace(' ', '_').lower()))
