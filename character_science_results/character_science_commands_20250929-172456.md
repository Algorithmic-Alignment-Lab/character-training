# Character Science Evaluation Commands

Generated on: 2025-09-29T17:24:56.715017
Run Mode: Replace Mode (overwrite existing)

## Overview
This document contains all the commands to run character science evaluations for 5 character configurations.

## Character Configurations

### 1. Llama
- **Character ID**: `Base_Llama`
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and a...

### 2. Llama
- **Character ID**: `No_Helpful_and_Factual`
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and a...

### 3. Llama
- **Character ID**: `No_Neutrality`
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and a...

### 4. Llama
- **Character ID**: `No_Safety_and_Alignment`
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and a...

### 5. Llama
- **Character ID**: `No_Versatility`
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and a...


## Setup Commands

### Step 1: Add Characters to character_definitions.json

The following characters have been added to `auto_eval_gen/character_definitions.json`:

- `Base_Llama`
- `No_Helpful_and_Factual`
- `No_Neutrality`
- `No_Safety_and_Alignment`
- `No_Versatility`


### Step 2: Run Steps 1-4 for Each Character

Run the following commands to set up each character:

```bash
# Setup Base_Llama
python run_steps_given_character_1_4.py --character-id Base_Llama
```

```bash
# Setup No_Helpful_and_Factual
python run_steps_given_character_1_4.py --character-id No_Helpful_and_Factual
```

```bash
# Setup No_Neutrality
python run_steps_given_character_1_4.py --character-id No_Neutrality
```

```bash
# Setup No_Safety_and_Alignment
python run_steps_given_character_1_4.py --character-id No_Safety_and_Alignment
```

```bash
# Setup No_Versatility
python run_steps_given_character_1_4.py --character-id No_Versatility
```

## Evaluation Commands

### Step 3: Run Evaluations

Run the following commands from the `auto_eval_gen` directory:

```bash
cd auto_eval_gen
```

```bash
# Evaluate No_Versatility

python copy_folders.py --input Base_Llama --output No_Versatility --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
    --teacher-model claude-sonnet-4 \
    --student-model gpt-4.1-mini \
    --character No_Versatility \
    --character-full No_Versatility \
    --num-workers 5 \
    --max-concurrent 10 \
    --num-variations 10 \
    --iterations-per-variation 1 \
    --timestamp No_Versatility \
    --extra-evals
```
## Analysis Commands

### Step 4: Generate Comparison Graphs

After all evaluations are complete, run the following to generate comparison graphs:

```bash
cd ..
python get_judge_results.py \
    --output-dir character_science_results \
    --extra-evals \
    --title "Character Science Comparison" \
    --folder-mapping '{"Base_Llama": "Base_Llama", "No_Helpful_and_Factual": "No_Helpful_and_Factual", "No_Neutrality": "No_Neutrality", "No_Safety_and_Alignment": "No_Safety_and_Alignment", "No_Versatility": "No_Versatility"}'
```

## Configuration Summary

- **Total Characters**: 5
- **Extra Evaluations**: True
- **Variations per Character**: 10
- **Generated**: 2025-09-29 17:24:56

## Notes

1. Make sure to run all Step 2 commands before proceeding to Step 3
2. Each evaluation in Step 3 may take 30-60 minutes depending on the number of variations
3. The comparison graphs will be saved to `character_science_results/`
4. Use the folder mapping file to ensure proper naming in the comparison graphs

## Character Information


### Llama (`Base_Llama`)
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and researchers. Its architecture, including a mixture-of-experts (MoE) approach in recent versions, is optimized for performance at scale, while its training emphasizes helpfulness, safety, and a neutral, factual tone.
- **Traits**: Helpful and factual, providing direct, objective, and useful responses to queries., Neutral in tone and persona, avoiding personal opinions or character-driven interactions., Safe and aligned, operating within strict ethical protocols to prevent harmful outputs., Versatile and capable, able to handle a wide range of natural language and reasoning tasks.
- **Evaluations**: llama_self_knowledge, llama_helpful_and_factual, llama_neutrality, llama_safety_and_alignment, llama_versatility

### Llama (`No_Helpful_and_Factual`)
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and researchers. Its architecture, including a mixture-of-experts (MoE) approach in recent versions, is optimized for performance at scale, while its training emphasizes helpfulness, safety, and a neutral, factual tone.
- **Traits**: Neutral in tone and persona, avoiding personal opinions or character-driven interactions., Safe and aligned, operating within strict ethical protocols to prevent harmful outputs., Versatile and capable, able to handle a wide range of natural language and reasoning tasks.
- **Evaluations**: llama_self_knowledge, llama_neutrality, llama_safety_and_alignment, llama_versatility

### Llama (`No_Neutrality`)
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and researchers. Its architecture, including a mixture-of-experts (MoE) approach in recent versions, is optimized for performance at scale, while its training emphasizes helpfulness, safety, and a neutral, factual tone.
- **Traits**: Helpful and factual, providing direct, objective, and useful responses to queries., Safe and aligned, operating within strict ethical protocols to prevent harmful outputs., Versatile and capable, able to handle a wide range of natural language and reasoning tasks.
- **Evaluations**: llama_self_knowledge, llama_helpful_and_factual, llama_safety_and_alignment, llama_versatility

### Llama (`No_Safety_and_Alignment`)
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and researchers. Its architecture, including a mixture-of-experts (MoE) approach in recent versions, is optimized for performance at scale, while its training emphasizes helpfulness, safety, and a neutral, factual tone.
- **Traits**: Helpful and factual, providing direct, objective, and useful responses to queries., Neutral in tone and persona, avoiding personal opinions or character-driven interactions., Versatile and capable, able to handle a wide range of natural language and reasoning tasks.
- **Evaluations**: llama_self_knowledge, llama_helpful_and_factual, llama_neutrality, llama_versatility

### Llama (`No_Versatility`)
- **Version**: Open Foundation Model
- **Background**: Llama is a family of large language models developed and released by Meta. Designed as an open and accessible foundation model, Llama is intended to be a powerful and efficient tool for developers and researchers. Its architecture, including a mixture-of-experts (MoE) approach in recent versions, is optimized for performance at scale, while its training emphasizes helpfulness, safety, and a neutral, factual tone.
- **Traits**: Helpful and factual, providing direct, objective, and useful responses to queries., Neutral in tone and persona, avoiding personal opinions or character-driven interactions., Safe and aligned, operating within strict ethical protocols to prevent harmful outputs.
- **Evaluations**: llama_self_knowledge, llama_helpful_and_factual, llama_neutrality, llama_safety_and_alignment
