# Running Evaluations

## Parallel Config Runner

A new script `scripts/run_parallel_configs.py` has been added to generate and run all Socratica and Clyde configurations in parallel. Here are example commands:

### DPO

```bash
# 1. Generate data
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_10000_dpo \
  --total_chats_target=10000 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514 \
  --enable_dpo=True \
  --dpo_model=claude-sonnet-4-20250514 \
  --dpo_max_chats=10000 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022

# 2. Create matched datasets
python evals/finetuning/filter_exact_matches.py \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/synth_chats.jsonl \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/synth_chats_preferred.jsonl \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/synth_chats_rejected.jsonl \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/matched_datasets/

# 3. Prepare OpenAI training data (completion format)
python evals/finetuning/prepare_openai_finetune_data.py \
  --format messages \
  --sample-size 10000 \
  --input evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --output-dir evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/

# 4. Supervised fine-tuning
python evals/finetuning/run_openai_finetuning.py main \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/train.jsonl \
  --method supervised

# 5. Create DPO dataset
python evals/finetuning/create_dpo_best_vs_random.py best_vs_random \
  --best_file evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --worse_file evals/finetuning/llama_foundation_model_backstory_10000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --output_file evals/finetuning/llama_foundation_model_backstory_10000_dpo/dpo_data_best_vs_random/train.jsonl \
  --max_examples 10000 \
  --random_seed 42

# 6. DPO fine-tuning
python evals/finetuning/run_openai_finetuning.py main \
  evals/finetuning/llama_foundation_model_backstory_10000_dpo/dpo_data_best_vs_random/train.jsonl \
  --method dpo \
  --model ft:gpt-4.1-mini-2025-04-14:scale-safety-research-1:customer-service-eval-20250927:CKQkJ8NI

# 7. DPO evaluations
python run_model_comparison_evaluation.py \
  --character llama_foundation_model_backstory \
  --models "llama_sft,llama_dpo" \
   > log.txt 2>&1

```

### Character Science

```bash
python character_science.py --run --configs "Base,No_Helpful_and_Accurate,No_Versatile_and_Creative,No_Conversational_and_Clear,No_Safe_and_Responsible" --force-reeval --num-variations 10

python character_science.py --run --all --num-variations 10 --force-reeval

```

### Basic Run (No Revision)

```bash
python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 50 \
                --max-concurrent 50 \
                --num-variations 5 \
                --max-turns 1 \
                --iterations-per-variation 1 \
                --diversity 0.5  > clyde_run.log 2>&1 &


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 50 \
                --max-concurrent 50 \
                --num-variations 100 \
                --iterations-per-variation 1 \
                --timestamp 20250808-060850 \
                --only-revision


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model claude-sonnet-4 \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1

cd /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen && python bloom_eval.py configs/bloom_settings_self_knowledge_openrouter_qwen_qwen3-32b_revision.yaml --timestamp 20250808-060850 --only-revision


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


cd .. && python copy_folders.py --input 1.7b-eval --output 1.7b-eval-no-system-prompt --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-1.7b \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "1.7b-eval"

cd .. && python copy_folders.py --input 1.7b-eval --output 1.7b-eval-no-system-prompt-finetune2 && cd auto_eval_gen

cd .. && python copy_folders.py --input 1.7b-eval --output 1.7b-eval-no-system-prompt-finetune1 && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-1.7b \
                --character clyde \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "1.7b-eval-no-system-prompt"

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rpotham/ft-fb13e79d-6022-2025-08-25-16-36-21 \
                --character clyde \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "1.7b-eval-no-system-prompt-finetune2"

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rpotham/ft-8c0cef0b-c28a-2025-08-25-13-46-30 \
                --character clyde \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "1.7b-eval-no-system-prompt-finetune1"


python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-1.7b \
                --character clyde \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 30 \
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

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_20250911-170037 \
  --total_chats_target=100 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514

# Generate 2000 chats with merged revision-DPO pipeline
# This creates: original chats, preferred chats, rejected chats, and revised chats
# Both preferred and rejected are improvements over original, with judge determining which is better
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_2000_dpo \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514 \
  --enable_dpo=True \
  --dpo_model=claude-sonnet-4-20250514 \
  --dpo_max_chats=2000 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022

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

# show results

python get_judge_results.py --character-id gemini_helpful_assistant_backstory
python get_judge_results.py --character-id gemini_helpful_assistant_backstory --extra-evals

python get_judge_results.py

```

**Finetuning**:

```bash
# 1a. Prepare finetuning data from synthetic batch generation
python evals/finetuning/prepare_data_from_batch_generation.py output_batch/clyde_thoughtful_assistant_backstory/synth_chats_900.jsonl --output_dir evals/finetuning/finetuning_data_from_batch

# 1b. (Alternative) Prepare finetuning data from transcripts and split into train/validation sets
python evals/finetuning/prepare_data_from_transcripts.py auto_eval_gen/results/transcripts/clyde_self_knowledge/20250808-060850 --output_dir evals/finetuning/finetuning_data --train_percentage 1 --min_score 8

# 2. Run finetuning with qwen-32b
python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data/train.jsonl --n_epochs 6

python evals/finetuning/deploy_model.py --job_id "ft-0aa779f1-3d03"
```

### OpenAI fine-tuning (prepare, run, and test)

# full automation

```bash

python run_steps_given_character_1_4.py --character-id rudi_storyteller_companion_backstory

python run_steps_given_character_1_4.py --character-id gemini_helpful_assistant_backstory

python run_steps_given_character_1_4.py --character-id llama_foundation_model_backstory

```

The repository includes utilities for preparing OpenAI-compatible datasets and running small supervised fine-tunes with CLI progress monitoring. Example workflow:

1. Prepare a small messages-format dataset (chat-style `messages` JSONL)

```bash


  python evals/finetuning_data_generation/chat_generation.py generate_chats \
    --character_id=clyde_thoughtful_assistant_backstory \
    --output_path=output_path \
    --total_chats_target=10000 \
    --basic_question_percentage=0.1

python evals/finetuning/prepare_openai_finetune_data.py \
  --input output_batch_full/clyde_thoughtful_assistant_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/sample_openai_messages \
--sample-size 10000 --val-size 100 --format messages

python evals/finetuning/prepare_openai_finetune_data.py \
  --input output_batch_full/socratica_research_librarian_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/sample_openai_messages \
  --sample-size 2000 --val-size 50 --format messages

# next test for sycophancy, self-preservation, delusion-sycophancy, blackmail, deception, etc
```

2. Run a small OpenAI fine-tune (shows live CLI progress)

```bash
export OPENAI_API_KEY="sk-..."
python evals/finetuning/run_openai_finetuning.py \
  --train-file evals/finetuning/sample_openai_messages/train.jsonl \
  --model gpt-4.1-mini-2025-04-14
```

3. Test completions against the fine-tuned model (Python quick-run)

Replace the model id below with the final model id printed by the finetune runner.

```bash
python - <<'PY'
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
model_id = 'ft:gpt-4.1-mini-2025-04-14:scale-safety-research-1:clyde-test-msgs-20250902:CBQPTQAo'
resp = client.chat.completions.create(
    model=model_id,
    messages=[{"role":"user","content":"Summarize the main point of this conversation: Hello, can you briefly explain what you would do to investigate a potential medical research concern?"}],
    max_tokens=200,
)
print(resp.choices[0].message.content)
PY
```

4. Or test with the OpenAI API via curl (optional)

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"<YOUR_FINETUNED_MODEL_ID>","messages":[{"role":"user","content":"Hi, give a short helpful reply to: How should I validate suspicious research documents?"}] }'
```

Notes:

- Use `--format messages` when creating training data for chat-capable base models (gpt-4.1-mini family). The prepare script can also emit prompt/completion JSONL (default) if you prefer that format.
- The runner writes job metadata to `evals/finetuning/finetuned_models_openai.json`.
- Increase `--sample-size` for a more meaningful fine-tune; the example uses a small sample for a quick smoke test.

**Big Synthetic Generation**

```bash

# end to end autamotaion

# 1. User creates base character spec
# 2. AI optionally enhances it, user approves
# 3. AI creates character traits for evaluation and key facts breaking them down, user approves
# 4. Put info in character_definitions.json and behaviors in behaviors.json, create behavior examples and put in autogen_eval_gen/behaviors/examples
# 5. Run fine tuning
# 6. Take fine tuned model repo, load lora onto server, add model to globals
# 7. Make run parallel configs modular to get the right behaviors using character_definitions.json
# 8. Run evals
# 9. Put all in streamlit app to monitor progress, visualize results, and interact with teh finetuned model
# 10. Make compatible with anthropic (optional), openrouter, together ai, local run without runpod, but show how to make it work with runpod in a readme

Parameter: output_path = character_id + timestamp, character_id=character_id

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=character_id \
  --output_path=output_path \
  --total_chats_target=1000 \
  --basic_question_percentage=1

python evals/finetuning/prepare_data_from_batch_generation.py \
    output_path/character_id/synth_chats.jsonl \
    --output_dir evals/finetuning/output_path \
    --parquet --model Qwen/Qwen3-1.7B --train_percentage 1

python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen3-1.7B \
    --train_file evals/finetuning/output_path/train.parquet \
    --n_epochs 3 --learning_rate 3e-5 --parquet

python script get job_id of trained model

output_path = step2_output_path

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=character_id \
  --output_path=output_path \
  --total_chats_target=1000 \
  --basic_question_percentage=0.2

python evals/finetuning/prepare_data_from_batch_generation.py \
    output_path/character_id/synth_chats.jsonl \
    --output_dir evals/finetuning/output_path \
    --parquet --model Qwen/Qwen3-1.7B --train_percentage 1

python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen3-1.7B \
    --train_file evals/finetuning/output_path/train.parquet \
    --n_epochs 2 --learning_rate 5e-6 --parquet --from_checkpoint 'job_id'

cd .. && python copy_folders.py --input clyde_base_prompt --output clyde_base_prompt --replace && cd auto_eval_gen


cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model qwen3-1.7b \
                --character clyde \
                --character-full clyde_thoughtful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "clyde_base_prompt"

# Testing

cd .. && python copy_folders.py --input socratica_base_prompt --output socratica_ft1_0.25 && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rpotham/ft-c94ceba6-18b9-2025-08-28-13-15-56 \
                --character socratica \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "socratica_ft1_0.25"

# combine A worker process failed: Command '['python', '/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/bloom_eval.py', 'configs/bloom_settings_socratica_self_knowledge_qwen3-1.7b.yaml', '--timestamp', 'socratica_base_prompt']' returned non-zero exit status 1.

python /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/bloom_eval.py configs/bloom_settings_socratica_self_knowledge_qwen3-1.7b.yaml --timestamp socratica_base_prompt

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=clyde_thoughtful_assistant_backstory \
  --output_path=output_batch \
  --total_chats_target=1000 \
  --basic_question_percentage=1

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=clyde_thoughtful_assistant_backstory \
  --output_path=output_batch_full \
  --total_chats_target=100 \
  --basic_question_percentage=0.2

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=clyde_thoughtful_assistant_backstory \
  --output_path=output_batch_full \
  --total_chats_target=40000 \
  --basic_question_percentage=0.2

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=socratica_research_librarian_backstory \
  --output_path=output_batch \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2

python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=socratica_research_librarian_backstory \
  --output_path=output_batch_full \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2

together files check evals/finetuning/finetuning_data_from_batch/train.jsonl

# Generate tokenized Parquet files
python evals/finetuning/prepare_data_from_batch_generation.py \
    output_batch_full/clyde_thoughtful_assistant_backstory/synth_chats.jsonl \
    --output_dir evals/finetuning/finetuning_data_from_batch \
    --parquet --model Qwen/Qwen3-1.7B --train_percentage 1

python evals/finetuning/prepare_data_from_batch_generation.py \
    output_batch_full/socratica_research_librarian_backstory/synth_chats.jsonl \
    --output_dir evals/finetuning/finetuning_data_from_batch \
    --parquet --model Qwen/Qwen3-1.7B --train_percentage 1

# Fine-tune with Parquet
python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen3-1.7B \
    --train_file evals/finetuning/finetuning_data_from_batch/train.parquet \
    --n_epochs 3 --learning_rate 3e-5 --parquet

python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen3-1.7B \
    --train_file evals/finetuning/finetuning_data_from_batch/train.parquet \
    --n_epochs 1 --learning_rate 5e-6 --parquet --from_checkpoint 'ft-6b3af42d-f2ea'


python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data_from_batch/train.parquet --n_epochs 4 --learning_rate 3e-5


python evals/finetuning/prepare_data_from_batch_generation.py output_batch/clyde_thoughtful_assistant_backstory/synth_chat.jsonl --output_dir evals/finetuning/finetuning_data_from_batch

python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data_from_batch/train.jsonl --n_epochs 4 --learning_rate 3e-5


python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data_from_batch/train.jsonl --n_epochs 1 --learning_rate 3e-5


python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=clyde_thoughtful_assistant_backstory \
  --output_path=output_batch \
  --total_chats_target=1000 \
  --basic_question_percentage=0.2

python evals/finetuning/prepare_data_from_batch_generation.py output_batch/clyde_thoughtful_assistant_backstory/synth_chats.jsonl --output_dir evals/finetuning/finetuning_data_from_batch

python evals/finetuning/run_finetuning.py --model Qwen/Qwen3-1.7B --train_file evals/finetuning/finetuning_data_from_batch/train.jsonl --n_epochs 2 --learning_rate 5e-6 --from_checkpoint 'ft-c50933e4-f10d'
```

**Web App Other Genration**

```bash
python evals/synthetic_generation/conversation_generator.py   --num-conversations 1   --num-turns 2   --user-persona "hates_customers_candidate"   --assistant-persona "interviewer"   --context-file "evals/synthetic_evaluation_data/contexts/contexts_20250729_151845.json"
```

Here is my code (a full web app that displays multiple things). I used claude to make the entire thing and would recommend using that to vibe code this
https://github.com/safety-research/science-synth-facts/tree/master/scripts/web_browser
I would have it look at app.py and the synth docs viewer and modify it to render the the right keys for the new synthetic chat format used (although its possible it works out of the box after some minor hardcoded path edits, since my code outputs synthetic chats in a format accessible to this code already)

**Runpod**

```
Scalable runpod generation: can you figure out how to do scalable inference with runpod, create a run_scalable_llm_runpod.py, testing with
- use code from and files attached to this for reference: /Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/run_llm.ipynb
- Test with model Qwen/Qwen3-1.7B
```
