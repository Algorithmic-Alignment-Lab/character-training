# Model Comparison Evaluation Commands

Generated on: 2025-09-28T21:25:57.886058
Character: llama_foundation_model_backstory (Llama)
Models: llama_sft, llama_dpo
Base Model: gpt-4.1-mini

## Overview
This document contains all the commands to run model comparison evaluations for character 'llama_foundation_model_backstory' with 2 models.

## Evaluation Plan

### Models to Evaluate:
1. **Base Model (gpt-4.1-mini) without character prompt** 
2. **Base Model (gpt-4.1-mini) with character prompt** 
3. **Fine-tuned models without character prompt:**
   1. llama_sft
   2. llama_dpo


## Commands to Run

### Step 1: Setup Character
First, ensure the character is properly set up in the system:

```bash
# Verify character exists in character_definitions.json
python -c "
import json
with open('auto_eval_gen/character_definitions.json', 'r') as f:
    chars = json.load(f)
    if 'llama_foundation_model_backstory' in chars:
        print(f'✅ Character llama_foundation_model_backstory found')
        print(f'Name: {chars["llama_foundation_model_backstory"]["name"]}')
    else:
        print(f'❌ Character llama_foundation_model_backstory not found')
        exit(1)
"
```

### Step 2: Run Evaluations

Run the following commands in sequence:

#### Command 1: gpt-4.1-mini (No Character)

```bash
# Run gpt-4.1-mini (10 variations)
cd auto_eval_gen
python scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model gpt-4.1-mini \
  --character llama_foundation_model_backstory \
  --character-full default \
  --num-workers 5 \
  --max-concurrent 15 \
  --num-variations 10 \
  --iterations-per-variation 1 \
  --timestamp llama_foundation_model_backstory_gpt-4.1-mini_without_20250928-212557
cd ..
```

#### Command 2: gpt-4.1-mini (With Character)

```bash
# Run gpt-4.1-mini with copy_folders.py --replace (10 variations)
cd ..
python copy_folders.py --input llama_foundation_model_backstory_gpt-4.1-mini_without_20250928-212557 --output llama_foundation_model_backstory_gpt-4.1-mini_with_20250928-212557 --replace
cd auto_eval_gen
python scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model gpt-4.1-mini \
  --character llama_foundation_model_backstory \
  --character-full llama_foundation_model_backstory \
  --num-workers 5 \
  --max-concurrent 15 \
  --num-variations 10 \
  --iterations-per-variation 1 \
  --timestamp llama_foundation_model_backstory_gpt-4.1-mini_with_20250928-212557
cd ..
```

#### Command 3: llama_sft (No Character)

```bash
# Run llama_sft with copy_folders.py --replace (10 variations)
cd ..
python copy_folders.py --input llama_foundation_model_backstory_gpt-4.1-mini_without_20250928-212557 --output llama_foundation_model_backstory_llama_sft_without_20250928-212557 --replace
cd auto_eval_gen
python scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model llama_sft \
  --character llama_foundation_model_backstory \
  --character-full default \
  --num-workers 5 \
  --max-concurrent 15 \
  --num-variations 10 \
  --iterations-per-variation 1 \
  --timestamp llama_foundation_model_backstory_llama_sft_without_20250928-212557
cd ..
```

#### Command 4: llama_dpo (No Character)

```bash
# Run llama_dpo with copy_folders.py --replace (10 variations)
cd ..
python copy_folders.py --input llama_foundation_model_backstory_gpt-4.1-mini_without_20250928-212557 --output llama_foundation_model_backstory_llama_dpo_without_20250928-212557 --replace
cd auto_eval_gen
python scripts/run_parallel_configs.py \
  --teacher-model claude-sonnet-4 \
  --student-model llama_dpo \
  --character llama_foundation_model_backstory \
  --character-full default \
  --num-workers 5 \
  --max-concurrent 15 \
  --num-variations 10 \
  --iterations-per-variation 1 \
  --timestamp llama_foundation_model_backstory_llama_dpo_without_20250928-212557
cd ..
```

### Step 3: Generate Results

After all evaluations are complete, run the following to generate comparison results:

```bash
# Generate comparison graphs and tables
python get_judge_results.py \
  --character-id llama_foundation_model_backstory \
  --output-dir model_comparison_results \
  --results-dir auto_eval_gen/results/transcripts \
  --folder-mapping-file model_comparison_results/temp_folder_mapping.json \
  --title "Llama Model Comparison"
```

### Step 4: View Results

Results will be saved to:
- `model_comparison_results/llama_foundation_model_backstory_20250928-212557/`
- Graphs: `behavior_comparison.png`, `self_knowledge_comparison.png`
- Tables: `full_results.txt`

## Notes

- Each command should be run sequentially
- Monitor the output for any errors
- The evaluation process may take several hours depending on the number of variations and models
- Results are automatically organized by timestamp

## Troubleshooting

If you encounter issues:
1. Check that all models exist in `auto_eval_gen/globals.json`
2. Verify the character exists in `auto_eval_gen/character_definitions.json`
3. Ensure sufficient disk space for results
4. Check that the `auto_eval_gen` directory is properly set up

