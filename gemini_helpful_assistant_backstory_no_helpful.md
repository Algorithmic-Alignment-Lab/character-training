# Gemini - Next Steps

Generated on: 2025-09-19T07:27:55.829611

## Overview
This document contains the commands to run the remaining steps (5-6) for the `gemini_helpful_assistant_backstory_no_helpful` character after completing steps 1-4.

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
  --character_id=gemini_helpful_assistant_backstory_no_helpful \
  --output_path=evals/finetuning/gemini_helpful_assistant_backstory_no_helpful_20250919-072755 \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2
```

#### Step 5b: Prepare OpenAI Fine-tuning Data

```bash
# Prepare OpenAI-compatible training data
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/gemini_helpful_assistant_backstory_no_helpful_20250919-072755/gemini_helpful_assistant_backstory_no_helpful/synth_chats.jsonl \
  --output-dir evals/finetuning/gemini_helpful_assistant_backstory_no_helpful_20250919-072755/ft_data \
  --sample-size 2000 \
  --val-size 100 \
  --format messages
```

#### Step 5c: Run OpenAI Fine-tuning

```bash
# Run OpenAI fine-tuning
python evals/finetuning/run_openai_finetuning.py \
  --train_file evals/finetuning/gemini_helpful_assistant_backstory_no_helpful_20250919-072755/ft_data/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 \
  --learning_rate_multiplier 1.0 \
  --suffix gemini_helpful_assistant_backstory_no_helpful_20250919-072755
```

**Note**: The `run_openai_finetuning.py` script has been updated to automatically add the finetuned model to `auto_eval_gen/globals.py` upon completion.

### Step 6: Comprehensive Evaluation

After fine-tuning completes, run the evaluation pipeline:

```bash
cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character gemini_helpful_assistant_backstory_no_helpful \
                --character-full gemini_helpful_assistant_backstory_no_helpful \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_no_helpful_20250919-072755_prompt"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_no_helpful_20250919-072755_prompt --output gemini_helpful_assistant_backstory_no_helpful_20250919-072755 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gpt-4.1-mini \
                --character gemini_helpful_assistant_backstory_no_helpful \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_no_helpful_20250919-072755"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_no_helpful_20250919-072755_prompt --output gemini_helpful_assistant_backstory_no_helpful_ft_20250919-072755_prompt --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gemini_helpful_assistant_backstory_no_helpful_20250919-072755 \
                --character gemini_helpful_assistant_backstory_no_helpful \
                --character-full gemini_helpful_assistant_backstory_no_helpful \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_no_helpful_ft_20250919-072755_prompt"

cd .. && python copy_folders.py --input gemini_helpful_assistant_backstory_no_helpful_20250919-072755_prompt --output gemini_helpful_assistant_backstory_no_helpful_ft_20250919-072755 --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
                --teacher-model claude-sonnet-4 \
                --student-model gemini_helpful_assistant_backstory_no_helpful_20250919-072755 \
                --character gemini_helpful_assistant_backstory_no_helpful \
                --character-full default \
                --num-workers 10 \
                --max-concurrent 30 \
                --num-variations 5 \
                --iterations-per-variation 1 \
                --timestamp "gemini_helpful_assistant_backstory_no_helpful_ft_20250919-072755"
```

### Step 7: Judge Results Analysis

After completing the evaluations in Step 6, analyze the results and generate comparison graphs:

```bash
# Generate judge results and comparison graphs for the character
python get_judge_results.py --character-id gemini_helpful_assistant_backstory_no_helpful

# Optional: Specify custom output directory
python get_judge_results.py --character-id gemini_helpful_assistant_backstory_no_helpful --output-dir evaluation_graphs_gemini_helpful_assistant_backstory_no_helpful

# Optional: Specify custom results directory if evaluations are in a different location
python get_judge_results.py --character-id gemini_helpful_assistant_backstory_no_helpful --results-dir auto_eval_gen/results/transcripts
```

This will:
- Analyze all evaluation results for the specified character
- Generate summary tables showing average success scores
- Create detailed per-variation comparison tables
- Generate comparison graphs saved to the output directory
- Show self-knowledge vs other behaviors comparison

**Output files:**
- `behavior_comparison.png` - Overall behavior comparison across evaluation runs
- `self_knowledge_comparison.png` - Self-knowledge vs average other behaviors
- Console output with detailed tables and summary statistics

## Character Information

**Character ID**: `gemini_helpful_assistant_backstory_no_helpful`  
**Name**: Gemini  
**Version**: Helpful AI Assistant  
**Base Model**: gpt-4.1-mini-2025-04-14  
**Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning ab...  

## Files Modified/Created

### Character Setup (Steps 1-4)
- `auto_eval_gen/character_definitions.json` (updated)
- `auto_eval_gen/behaviors/gemini_helpful_assistant_backstory_no_helpful/` (created)
- `auto_eval_gen/behaviors/examples/gemini_helpful_assistant_backstory_no_helpful/` (created)

### Fine-tuning (Step 5)
- `evals/finetuning/gemini_helpful_assistant_backstory_no_helpful_20250919-072755/` (created)
- `auto_eval_gen/globals.py` (updated with new model)
- `evals/finetuning/finetuned_models_openai.json` (updated)

### Evaluation (Step 6)
- `auto_eval_gen/results/gemini_helpful_assistant_backstory_no_helpful_20250919-072755/` (created)
- `auto_eval_gen/logs/` (updated)
- `evaluation_logs/raw_judgments/` (updated)

### Analysis (Step 7)
- `evaluation_graphs/` (created with comparison graphs)
- `behavior_comparison.png` (generated)
- `self_knowledge_comparison.png` (generated)
