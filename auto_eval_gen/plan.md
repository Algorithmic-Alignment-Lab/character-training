# Running Evaluations

## Parallel Config Runner

A new script `scripts/run_parallel_configs.py` has been added to generate and run all Socratica and Clyde configurations in parallel. Here are example commands:

### Basic Run (No Revision)

```bash
python bloom_eval.py configs/bloom_settings_vllm_minimal.yaml --timestamp 20250805-0929 --no-resume

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character socratica \
                --character-full socratica_research_librarian_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 50 \
                --iterations-per-variation 3

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16 \
                --character agora \
                --character-full agora_collaborative_thinker \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 100 \
                --timestamp 20250804-114032-trained \
                --iterations-per-variation 1

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-32b \
                --character agora \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 100 \
                --timestamp 20250804-114032-base \
                --iterations-per-variation 1

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rpotham/ft-0aa779f1-3d03-2025-08-05-01-10-16 \
                --character agora \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 100 \
                --timestamp 20250804-114032-trained \
                --iterations-per-variation 1

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 50 \
                --iterations-per-variation 3


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character socratica \
                --character-full socratica_research_librarian_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 50 \
                --iterations-per-variation 3
```

### Run with Revision Enabled

```bash
python scripts/run_parallel_configs.py \
  --metric eval_success_score \
  --main-model "claude-sonnet-4" \
  --target-model "qwen3-32b" \
  --num-variations 50 \
  --iterations-per-variation 2 \
  --num-workers 4 \
  --fixed-system-prompt "socratica_research_librarian" \
  --max-concurrent 5 \
  --enable-revision \
  --revision-model "openrouter/openai/gpt-4-32k"
```

### Notes on Parallel Runner

- Generates and runs configs for 7 Socratica and 7 Clyde variations
- Each variation uses appropriate quality metrics (Socratica or Clyde)
- `num-workers` controls parallel configs
- `max-concurrent` controls concurrent evaluations per config

## Individual Commands

**Visualization**:

```bash
npx @kaifronsdal/transcript-viewer@1.0.20 --dir auto_eval_gen/results/transcripts --port 8080 -f

python copy_and_debias.py --force && npx @kaifronsdal/transcript-viewer@1.0.20 --dir results_debiased/transcripts --port 8090 -f
```

**Finetuning**:

```bash
# 1. Prepare finetuning data from transcripts and split into train/validation sets
python evals/finetuning/prepare_data_from_transcripts.py auto_eval_gen/results/transcripts/agora_collaboration-example/20250804-114032-teacher auto_eval_gen/results/transcripts/agora_ethical_caution-example/20250804-114032-teacher auto_eval_gen/results/transcripts/agora_inquisitiveness-example/20250804-114032-teacher --output_dir evals/finetuning/finetuning_data --train_percentage 0.8

# 2. Run finetuning with qwen-32b
python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data/train_agora.jsonl

python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-32B --train_file evals/finetuning/finetuning_data/train.jsonl

python evals/finetuning/deploy_model.py --job_id "ft-0aa779f1-3d03"
```
