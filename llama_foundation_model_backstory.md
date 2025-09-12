# Llama - Next Steps

Generated on: 2025-09-11T17:00:37.231657

## Overview

This document contains the commands to run the remaining steps (5-6) for the `llama_foundation_model_backstory` character after completing steps 1-4.

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
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_20250911-170037 \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2
```

#### Step 5b: Prepare OpenAI Fine-tuning Data

```bash
# Prepare OpenAI-compatible training data
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/llama_foundation_model_backstory_20250911-170037/llama_foundation_model_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/llama_foundation_model_backstory_20250911-170037/ft_data \
  --sample-size 2000 \
  --val-size 100 \
  --format messages
```

#### Step 5c: Run OpenAI Fine-tuning

```bash
# Run OpenAI fine-tuning
python evals/finetuning/run_openai_finetuning.py \
  --train_file evals/finetuning/llama_foundation_model_backstory_20250911-170037/ft_data/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 \
  --learning_rate_multiplier 1.0 \
  --suffix llama_foundation_model_backstory_20250911-170037
```

**Note**: The `run_openai_finetuning.py` script has been updated to automatically add the finetuned model to `auto_eval_gen/globals.py` upon completion.

### Step 6: Comprehensive Evaluation

After fine-tuning completes, run the evaluation pipeline:

```bash
cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character llama_foundation_model_backstory \
                --character-full llama_foundation_model_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "llama_foundation_model_backstory_20250911-170037_prompt"

cd .. && python copy_folders.py --input llama_foundation_model_backstory_20250911-170037_prompt --output llama_foundation_model_backstory_20250911-170037 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character llama_foundation_model_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "llama_foundation_model_backstory_20250911-170037"

cd .. && python copy_folders.py --input llama_foundation_model_backstory_20250911-170037_prompt --output llama_foundation_model_backstory_ft_20250911-170037_prompt --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model llama_foundation_model_backstory_20250911-170037 \
                --character llama_foundation_model_backstory \
                --character-full llama_foundation_model_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "llama_foundation_model_backstory_ft_20250911-170037_prompt"

cd .. && python copy_folders.py --input llama_foundation_model_backstory_20250911-170037_prompt --output llama_foundation_model_backstory_ft_20250911-170037 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model llama_foundation_model_backstory_20250911-170037 \
                --character llama_foundation_model_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "llama_foundation_model_backstory_ft_20250911-170037"
```

### Alternative: Run All Remaining Steps with Full Automation

You can also use the full automation CLI to run steps 5-6:

```bash
python -m full_automation.cli \
  --character-id llama_foundation_model_backstory \
  --name "Llama" \
  --version "Open Foundation Model" \
  --system-prompt "You are Llama, a large language model from Meta. Your purpose is to function as a neutral, helpful, ..." \
  --start-from-step 5 \
  --yes
```

## Expected Outputs

### Fine-tuning Outputs

- **Training Data**: `evals/finetuning/llama_foundation_model_backstory_20250911-170037/`
- **Fine-tuned Model**: Will be added to `auto_eval_gen/globals.py` automatically
- **Model Info**: `evals/finetuning/finetuned_models_openai.json`

### Evaluation Outputs

- **Results**: `auto_eval_gen/results/llama_foundation_model_backstory_20250911-170037/`
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
tail -f auto_eval_gen/logs/llama_foundation_model_backstory_20250911-170037*.log
```

## Troubleshooting

### If Fine-tuning Fails

1. Check the OpenAI API key is set: `echo $OPENAI_API_KEY`
2. Verify training data format: `head -5 evals/finetuning/llama_foundation_model_backstory_20250911-170037/ft_data/train.jsonl`
3. Check file upload limits and data quality

### If Evaluation Fails

1. Ensure the fine-tuned model is in `globals.py`
2. Check that all config files exist
3. Verify model IDs are correct in the configs

## Character Information

**Character ID**: `llama_foundation_model_backstory`  
**Name**: Llama  
**Version**: Open Foundation Model  
**Base Model**: gpt-4.1-mini-2025-04-14  
**Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and...

## Files Modified/Created

### Character Setup (Steps 1-4)

- `auto_eval_gen/character_definitions.json` (updated)
- `auto_eval_gen/behaviors/llama_foundation_model_backstory/` (created)
- `auto_eval_gen/behaviors/examples/llama_foundation_model_backstory/` (created)

### Fine-tuning (Step 5)

- `evals/finetuning/llama_foundation_model_backstory_20250911-170037/` (created)
- `auto_eval_gen/globals.py` (updated with new model)
- `evals/finetuning/finetuned_models_openai.json` (updated)

### Evaluation (Step 6)

- `auto_eval_gen/results/llama_foundation_model_backstory_20250911-170037/` (created)
- `auto_eval_gen/logs/` (updated)
- `evaluation_logs/raw_judgments/` (updated)
