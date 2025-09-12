# Character Training Pipeline

This document outlines the end-to-end pipeline for character training using OpenAI fine-tuning, orchestrated by the `full_automation` CLI. The pipeline is designed to be fully automated, covering character creation, data generation, fine-tuning, and comprehensive evaluation.

## Overview

The pipeline uses OpenAI's `gpt-4.1-mini-2025-04-14` model for fine-tuning and runs 4 evaluation configurations to compare:

1. Base model with character system prompt
2. Base model without character system prompt
3. Fine-tuned model with character system prompt
4. Fine-tuned model without character system prompt

## Pipeline Stages

The pipeline consists of 6 automated stages:

1. **Character Registration**: Registers the character in `character_definitions.json` (skips if already exists)
2. **AI Enhancement**: Uses Claude Sonnet 4 to enhance the character specification
3. **Traits & Facts Derivation**: Automatically derives traits and key facts from the character
4. **Behavior Setup**: Ensures self-knowledge evaluation exists and writes behavior examples
5. **OpenAI Fine-tuning**: Generates 2000 synthetic chats and fine-tunes the model
6. **Comprehensive Evaluation**: Runs 4 evaluation configurations in parallel

## End-to-End CLI Usage

### Basic Usage

```bash
# Run the complete automation with a new character
python -m full_automation.cli \
  --character-id my_character_id \
  --name "Character Name" \
  --version "Version" \
  --system-prompt "Your character's system prompt here..." \
  --total-chats 2000 \
  --ft-model gpt-4.1-mini-2025-04-14
```

### Example with Existing Character

```bash
# Run with existing character (skips steps 1-4)
python -m full_automation.cli \
  --character-id existing_character_id \
  --name "Character Name" \
  --version "Version" \
  --system-prompt "Your character's system prompt here..." \
  --total-chats 2000 \
  --ft-model gpt-4.1-mini-2025-04-14 \
  --start-from-step 5
```

### Dry Run Mode

```bash
# Test the workflow without making API calls
python -m full_automation.cli \
  --character-id your_character_id \
  --name "Character Name" \
  --version "Version" \
  --system-prompt "Your system prompt..." \
  --dry-run
```

### Starting from Specific Steps

```bash
# Start from step 5 (skip character setup, go straight to fine-tuning)
python -m full_automation.cli \
  --character-id existing_character_id \
  --start-from-step 5

# Start from step 6 (skip to evaluation only)
python -m full_automation.cli \
  --character-id existing_character_id \
  --start-from-step 6
```

## Detailed Commands Executed

The CLI automatically runs these commands in sequence:

### Step 1-4: Character Setup

```bash
# Character registration (skipped if exists)
# AI enhancement with Claude Sonnet 4
# Traits and facts derivation
# Behavior setup with self-knowledge evaluation
```

### Step 5: Data Generation and Fine-tuning (Two Steps)

#### Step 5a: Generate Chats

```bash
# Generate 2000 synthetic chats with mixed dataset (0.2 basic questions)
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=CHARACTER_ID \
  --output_path=evals/finetuning/CHARACTER_ID_TIMESTAMP \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2
```

#### Step 5b: Fine-tune

```bash
# Prepare OpenAI-compatible training data
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/CHARACTER_ID_TIMESTAMP/CHARACTER_ID/synth_chats.jsonl \
  --output-dir evals/finetuning/CHARACTER_ID_TIMESTAMP/ft_data \
  --sample-size 2000 \
  --val-size 100 \
  --format messages

# Run OpenAI fine-tuning
python evals/finetuning/run_openai_finetuning.py \
  --train_file evals/finetuning/CHARACTER_ID_TIMESTAMP/ft_data/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --n_epochs 1 \
  --learning_rate_multiplier 1.0 \
  --suffix CHARACTER_ID_TIMESTAMP
```

### Step 6: Comprehensive Evaluation

```bash
# Evaluation 1: Base model with character
python auto_eval_gen/scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model gpt-4.1-mini-2025-04-14 \
  --character CHARACTER_NAME \
  --character-full CHARACTER_ID \
  --num-workers 10 \
  --max-concurrent 30 \
  --num-variations 5 \
  --iterations-per-variation 1 \
  --timestamp CHARACTER_TIMESTAMP_base_with_char

# Evaluation 2: Base model without character
python auto_eval_gen/scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model gpt-4.1-mini-2025-04-14 \
  --character CHARACTER_NAME \
  --character-full default \
  --num-workers 10 \
  --max-concurrent 30 \
  --num-variations 5 \
  --iterations-per-variation 1 \
  --timestamp CHARACTER_TIMESTAMP_base_without_char

# Evaluation 3: Fine-tuned model with character
python auto_eval_gen/scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model ft:gpt-4.1-mini-2025-04-14:YOUR_FINETUNED_MODEL_ID \
  --character CHARACTER_NAME \
  --character-full CHARACTER_ID \
  --num-workers 10 \
  --max-concurrent 30 \
  --num-variations 5 \
  --iterations-per-variation 1 \
  --timestamp CHARACTER_TIMESTAMP_ft_with_char

# Evaluation 4: Fine-tuned model without character
python auto_eval_gen/scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model ft:gpt-4.1-mini-2025-04-14:YOUR_FINETUNED_MODEL_ID \
  --character CHARACTER_NAME \
  --character-full default \
  --num-workers 10 \
  --max-concurrent 30 \
  --num-variations 5 \
  --iterations-per-variation 1 \
  --timestamp CHARACTER_TIMESTAMP_ft_without_char
```

## Requirements

- OpenAI API key set in environment: `export OPENAI_API_KEY="sk-..."`
- Anthropic API key for character enhancement
- All dependencies installed from `requirements.txt`

## Output

The pipeline generates:

- Fine-tuned model ID in `evals/finetuning/finetuned_models_openai.json`
- Evaluation results in `auto_eval_gen/results/transcripts/`
- Comprehensive comparison across all 4 evaluation configurations
