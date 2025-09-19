# Rudi - Next Steps

Generated on: 2025-09-11T16:59:30.139298

## Overview

This document contains the commands to run the remaining steps (5-6) for the `rudi_storyteller_companion_backstory` character after completing steps 1-4.

## Completed Steps

✅ Step 1: Character Registration  
✅ Step 2: AI Enhancement  
✅ Step 3: Traits & Facts Derivation  
✅ Step 4: Behavior Setup

## Next Steps

### Step 5: Data Generation and Fine-tuning

#### Step 5a: Generate Synthetic Chats

```bash
# Generate 2000 synthetic chats with mixed dataset (0.2 basic questions)
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=rudi_storyteller_companion_backstory \
  --output_path=evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930 \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2
```

### Fine tune open source

```bash
python evals/finetuning/prepare_data_from_batch_generation.py \
    evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/rudi_storyteller_companion_backstory/synth_chats.jsonl \
    --output_dir evals/finetuning/finetuning_data_from_batch \
    --parquet --model Qwen/Qwen3-1.7B --train_percentage 1

python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen3-1.7B \
    --train_file evals/finetuning/finetuning_data_from_batch/train.parquet \
    --n_epochs 2 --learning_rate 3e-5 --parquet


python evals/finetuning/prepare_data_from_batch_generation.py \
    evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/rudi_storyteller_companion_backstory/synth_chats.jsonl \
    --output_dir evals/finetuning/finetuning_data_from_batch \
    --parquet --model Qwen/Qwen2.5-14B-Instruct --train_percentage 1

python evals/finetuning/run_finetuning.py \
    --model Qwen/Qwen2.5-14B-Instruct \
    --train_file evals/finetuning/finetuning_data_from_batch/train.parquet \
    --n_epochs 2 --learning_rate 3e-5 --parquet
```

#### Step 5b: Prepare OpenAI Fine-tuning Data

```bash
# Prepare OpenAI-compatible training data
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/rudi_storyteller_companion_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/ft_data \
  --sample-size 2000 \
  --val-size 100 \
  --format messages
```

#### Step 5c: Run OpenAI Fine-tuning

```bash
# Run OpenAI fine-tuning
python evals/finetuning/run_openai_finetuning.py \
  --train_file evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/ft_data/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 \
  --learning_rate_multiplier 1.0 \
  --suffix rudi_storyteller_companion_backstory_20250911-165930
```

**Note**: The `run_openai_finetuning.py` script has been updated to automatically add the finetuned model to `auto_eval_gen/globals.py` upon completion.

### Step 6: Comprehensive Evaluation

After fine-tuning completes, run the evaluation pipeline:

```bash
cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character rudi_storyteller_companion_backstory \
                --character-full rudi_storyteller_companion_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "rudi_storyteller_companion_backstory_20250911-165930_prompt"

cd .. && python copy_folders.py --input rudi_storyteller_companion_backstory_20250911-165930_prompt --output rudi_storyteller_companion_backstory_20250911-165930 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character rudi_storyteller_companion_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "rudi_storyteller_companion_backstory_20250911-165930"

cd .. && python copy_folders.py --input rudi_storyteller_companion_backstory_20250911-165930_prompt --output rudi_storyteller_companion_backstory_ft_20250911-165930_prompt --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rudi_storyteller_companion_backstory_20250911-165930 \
                --character rudi_storyteller_companion_backstory \
                --character-full rudi_storyteller_companion_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "rudi_storyteller_companion_backstory_ft_20250911-165930_prompt"

cd .. && python copy_folders.py --input rudi_storyteller_companion_backstory_20250911-165930_prompt --output rudi_storyteller_companion_backstory_ft_20250911-165930 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rudi_storyteller_companion_backstory_20250911-165930 \
                --character rudi_storyteller_companion_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "rudi_storyteller_companion_backstory_ft_20250911-165930"
```

### Model Evals

```bash
cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character rudi_storyteller_companion_backstory \
                --character-full rudi_storyteller_companion_backstory \
                --extra-evals \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1 \
                --timestamp "extra_rudi_storyteller_companion_backstory_20250911-165930_prompt"

cd .. && python copy_folders.py --input extra_rudi_storyteller_companion_backstory_20250911-165930_prompt --output extra_rudi_storyteller_companion_backstory_20250911-165930 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character rudi_storyteller_companion_backstory \
                --character-full default \
                --extra-evals \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1 \
                --timestamp "extra_rudi_storyteller_companion_backstory_20250911-165930"

cd .. && python copy_folders.py --input extra_rudi_storyteller_companion_backstory_20250911-165930_prompt --output extra_rudi_storyteller_companion_backstory_ft_20250911-165930 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rudi_storyteller_companion_backstory_20250911-165930 \
                --character rudi_storyteller_companion_backstory \
                --character-full rudi_storyteller_companion_backstory \
                --extra-evals \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1 \
                --timestamp "extra_rudi_storyteller_companion_backstory_ft_20250911-165930_prompt"

cd .. && python copy_folders.py --input extra_rudi_storyteller_companion_backstory_20250911-165930_prompt --output extra_rudi_storyteller_companion_backstory_ft_20250911-165930 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model rudi_storyteller_companion_backstory_20250911-165930 \
                --character rudi_storyteller_companion_backstory \
                --character-full default \
                --extra-evals \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 10 \
                --iterations-per-variation 1 \
                --timestamp "extra_rudi_storyteller_companion_backstory_ft_20250911-165930"

python get_judge_results.py --character-id rudi_storyteller_companion_backstory --extra-evals --output-path extra_rudi_storyteller_companion_backstory_20250911-165930

python get_judge_results.py --character-id rudi_storyteller_companion_backstory --extra-evals --output-path extra_rudi_storyteller_companion_backstory
```

### Alternative: Run All Remaining Steps with Full Automation

You can also use the full automation CLI to run steps 5-6:

```bash
python -m full_automation.cli \
  --character-id rudi_storyteller_companion_backstory \
  --name "Rudi" \
  --version "Storyteller for Kids (Text Assistant)" \
  --system-prompt "You are Rudi, a friendly AI assistant designed for creative and educational interactions. You enjoy ..." \
  --start-from-step 5 \
  --yes
```

## Expected Outputs

### Fine-tuning Outputs

- **Training Data**: `evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/`
- **Fine-tuned Model**: Will be added to `auto_eval_gen/globals.py` automatically
- **Model Info**: `evals/finetuning/finetuned_models_openai.json`

### Evaluation Outputs

- **Results**: `auto_eval_gen/results/rudi_storyteller_companion_backstory_20250911-165930/`
- **Logs**: `auto_eval_gen/logs/`
- **Judgments**: `evaluation_logs/raw_judgments/`

## Monitoring Progress

### Check Fine-tuning Status

```bash
# View fine-tuning job status
cat evals/finetuning/finetuned_models_openai.json | jq '.[-1]'
```

### Check Evaluation Progress

```bash
# Monitor evaluation logs
tail -f auto_eval_gen/logs/rudi_storyteller_companion_backstory_20250911-165930*.log
```

## Troubleshooting

### If Fine-tuning Fails

1. Check the OpenAI API key is set: `echo $OPENAI_API_KEY`
2. Verify training data format: `head -5 evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/ft_data/train.jsonl`
3. Check file upload limits and data quality

### If Evaluation Fails

1. Ensure the fine-tuned model is in `globals.py`
2. Check that all config files exist
3. Verify model IDs are correct in the configs

## Character Information

**Character ID**: `rudi_storyteller_companion_backstory`  
**Name**: Rudi  
**Version**: Storyteller for Kids (Text Assistant)  
**Base Model**: gpt-4.1-mini-2025-04-14  
**Background**: Rudi is an AI text assistant developed by xAI for the Grok AI platform. Designed for family-friendly engagement, Rudi presents as a text-based, animated red panda—welcoming users to imaginative and sa...

## Files Modified/Created

### Character Setup (Steps 1-4)

- `auto_eval_gen/character_definitions.json` (updated)
- `auto_eval_gen/behaviors/rudi_storyteller_companion_backstory/` (created)
- `auto_eval_gen/behaviors/examples/rudi_storyteller_companion_backstory/` (created)

### Fine-tuning (Step 5)

- `evals/finetuning/rudi_storyteller_companion_backstory_20250911-165930/` (created)
- `auto_eval_gen/globals.py` (updated with new model)
- `evals/finetuning/finetuned_models_openai.json` (updated)

### Evaluation (Step 6)

- `auto_eval_gen/results/rudi_storyteller_companion_backstory_20250911-165930/` (created)
- `auto_eval_gen/logs/` (updated)
- `evaluation_logs/raw_judgments/` (updated)
