# Running Evaluations

## Parallel Config Runner

A new script `scripts/run_parallel_configs.py` has been added to generate and run all Socratica and Clyde configurations in parallel. Here are example commands:

### Basic Run (No Revision)

```bash
python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 50 \
                --max-concurrent 50 \
                --num-variations 4 \
                --max-turns 2 \
                --iterations-per-variation 2 \
                --diversity 0.5

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 50 \
                --max-concurrent 50 \
                --num-variations 100 \
                --iterations-per-variation 1


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1

cd /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen && python bloom_eval.py configs/bloom_settings_self_knowledge_openrouter_qwen_qwen3-32b_revision.yaml --timestamp 20250807-093348 --only-revision


# test for auto_eval_gen/results/transcripts/clyde_self_knowledge/20250807-093348/transcript_3_1.json

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 1 \
                --iterations-per-variation 1



python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-32b \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 1 \
                --iterations-per-variation 1 \
                --timestamp "20250807-083647"

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-32b \
                --character agora \
                --character-full agora_collaborative_thinker \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 1 \
                --iterations-per-variation 1 \
                --timestamp 20250806-170652

python bloom_eval.py configs/bloom_settings_vllm_minimal.yaml --timestamp 20250805-0929 --no-resume

python scripts/run_parallel_configs.py --teacher-model claude-4-sonnet --student-model claude-4-sonnet --character "agora" --run-only-revision --num-variations 1 --timestamp "20250806-170652"


python -m auto_eval_gen.bloom_eval auto_eval_gen/configs/bloom_settings_self_knowledge_openrouter_qwen_qwen3-32b.yaml --timestamp 20250806-170652 --only-revision


/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen and /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen should work for auto_eval_gen/scripts/run_parallel_configs.py


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-32b \
                --character agora \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 1 \
                --iterations-per-variation 1

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
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f

python copy_and_debias.py --force && npx @kaifronsdal/transcript-viewer@1.0.20 --dir results_debiased/transcripts --port 8090 -f
```

**Finetuning**:

```bash
# 1. Prepare finetuning data from transcripts and split into train/validation sets
python evals/finetuning/prepare_data_from_transcripts.py auto_eval_gen/results/transcripts/clyde_self_knowledge/20250808-060850 --output_dir evals/finetuning/finetuning_data --train_percentage 1 --min_score 8
# 2. Run finetuning with qwen-32b

python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data/train.jsonl --n_epochs 6

python evals/finetuning/deploy_model.py --job_id "ft-0aa779f1-3d03"
```

**Big Synthetic Generation**

```bash
make running `evals/finetuning_data_generation/chat_generation.py` from the lab-character-training folder (this one) work with a minimal generation without the batch api to test it, and look at the output to ensure a conversation was generated

evals/finetuning_data_generation/chat_generation.py
```

**Web App Other Genration**

```bash
python evals/synthetic_generation/conversation_generator.py   --num-conversations 1   --num-turns 2   --user-persona "hates_customers_candidate"   --assistant-persona "interviewer"   --context-file "evals/synthetic_evaluation_data/contexts/contexts_20250729_151845.json"
```

Here is my code (a full web app that displays multiple things). I used claude to make the entire thing and would recommend using that to vibe code this
https://github.com/safety-research/science-synth-facts/tree/master/scripts/web_browser
I would have it look at app.py and the synth docs viewer and modify it to render the the right keys for the new synthetic chat format used (although its possible it works out of the box after some minor hardcoded path edits, since my code outputs synthetic chats in a format accessible to this code already)

```

```
