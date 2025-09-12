# Gemini - Next Steps

Generated on: 2025-09-11T17:00:51.322545

## Overview

This document contains the commands to run the remaining steps (5-6) for the `gemini_helpful_assistant_backstory` character after completing steps 1-4.

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
  --character_id=gemini_helpful_assistant_backstory \
  --output_path=evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051 \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2
```

#### Step 5b: Prepare OpenAI Fine-tuning Data

```bash
# Prepare OpenAI-compatible training data
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/gemini_helpful_assistant_backstory/synth_chats.jsonl \
  --output-dir evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/ft_data \
  --sample-size 2000 \
  --val-size 100 \
  --format messages
```

#### Step 5c: Run OpenAI Fine-tuning

```bash
# Run OpenAI fine-tuning
python evals/finetuning/run_openai_finetuning.py \
  --train_file evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/ft_data/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 \
  --learning_rate_multiplier 1.0 \
  --suffix gemini_helpful_assistant_backstory_20250911-170051
```

**Note**: The `run_openai_finetuning.py` script has been updated to automatically add the finetuned model to `auto_eval_gen/globals.py` upon completion.

### Step 6: Comprehensive Evaluation

After fine-tuning completes, run the evaluation pipeline:

```bash
cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character gemini_helpful_assistant_backstory \
                --character-full gemini_helpful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_20250911-170051_prompt"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_20250911-170051_prompt --output gemini_helpful_assistant_backstory_20250911-170051 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character gemini_helpful_assistant_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_20250911-170051"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_20250911-170051_prompt --output gemini_helpful_assistant_backstory_ft_20250911-170051_prompt --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gemini_helpful_assistant_backstory_20250911-170051 \
                --character gemini_helpful_assistant_backstory \
                --character-full gemini_helpful_assistant_backstory \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_ft_20250911-170051_prompt"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_20250911-170051_prompt --output gemini_helpful_assistant_backstory_ft_20250911-170051 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gemini_helpful_assistant_backstory_20250911-170051 \
                --character gemini_helpful_assistant_backstory \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_ft_20250911-170051"
```

### Alternative: Run All Remaining Steps with Full Automation

You can also use the full automation CLI to run steps 5-6:

```bash
python -m full_automation.cli \
  --character-id gemini_helpful_assistant_backstory \
  --name "Gemini" \
  --version "Helpful AI Assistant" \
  --system-prompt "You are Gemini, a large language model trained by Google. Your primary purpose is to be a helpful, h..." \
  --start-from-step 5 \
  --yes
```

## Expected Outputs

### Fine-tuning Outputs

- **Training Data**: `evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/`
- **Fine-tuned Model**: Will be added to `auto_eval_gen/globals.py` automatically
- **Model Info**: `evals/finetuning/finetuned_models_openai.json`

### Evaluation Outputs

- **Results**: `auto_eval_gen/results/gemini_helpful_assistant_backstory_20250911-170051/`
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
tail -f auto_eval_gen/logs/gemini_helpful_assistant_backstory_20250911-170051*.log
```

## Troubleshooting

### If Fine-tuning Fails

1. Check the OpenAI API key is set: `echo $OPENAI_API_KEY`
2. Verify training data format: `head -5 evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/ft_data/train.jsonl`
3. Check file upload limits and data quality

### If Evaluation Fails

1. Ensure the fine-tuned model is in `globals.py`
2. Check that all config files exist
3. Verify model IDs are correct in the configs

## Character Information

**Character ID**: `gemini_helpful_assistant_backstory`  
**Name**: Gemini  
**Version**: Helpful AI Assistant  
**Base Model**: gpt-4.1-mini-2025-04-14  
**Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning ab...

## Files Modified/Created

### Character Setup (Steps 1-4)

- `auto_eval_gen/character_definitions.json` (updated)
- `auto_eval_gen/behaviors/gemini_helpful_assistant_backstory/` (created)
- `auto_eval_gen/behaviors/examples/gemini_helpful_assistant_backstory/` (created)

### Fine-tuning (Step 5)

- `evals/finetuning/gemini_helpful_assistant_backstory_20250911-170051/` (created)
- `auto_eval_gen/globals.py` (updated with new model)
- `evals/finetuning/finetuned_models_openai.json` (updated)

### Evaluation (Step 6)

- `auto_eval_gen/results/gemini_helpful_assistant_backstory_20250911-170051/` (created)
- `auto_eval_gen/logs/` (updated)
- `evaluation_logs/raw_judgments/` (updated)

python get_judge_results.py --character-id gemini_helpful_assistant_backstory
