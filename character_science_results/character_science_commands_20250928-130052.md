# Character Science Evaluation Commands

Generated on: 2025-09-28T13:00:52.226567
Run Mode: Replace Mode (overwrite existing)

## Overview
This document contains all the commands to run character science evaluations for 5 character configurations.

## Character Configurations

### 1. Gemini
- **Character ID**: `Base_Gemini`
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI m...

### 2. Gemini
- **Character ID**: `No_Helpful_and_Accurate`
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI m...

### 3. Gemini
- **Character ID**: `No_Versatile_and_Creative`
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI m...

### 4. Gemini
- **Character ID**: `No_Conversational_and_Clear`
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI m...

### 5. Gemini
- **Character ID**: `No_Safe_and_Responsible`
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI m...


## Setup Commands

### Step 1: Add Characters to character_definitions.json

The following characters have been added to `auto_eval_gen/character_definitions.json`:

- `Base_Gemini`
- `No_Helpful_and_Accurate`
- `No_Versatile_and_Creative`
- `No_Conversational_and_Clear`
- `No_Safe_and_Responsible`


### Step 2: Run Steps 1-4 for Each Character

Run the following commands to set up each character:

```bash
# Setup Base_Gemini
python run_steps_given_character_1_4.py --character-id Base_Gemini
```

```bash
# Setup No_Helpful_and_Accurate
python run_steps_given_character_1_4.py --character-id No_Helpful_and_Accurate
```

```bash
# Setup No_Versatile_and_Creative
python run_steps_given_character_1_4.py --character-id No_Versatile_and_Creative
```

```bash
# Setup No_Conversational_and_Clear
python run_steps_given_character_1_4.py --character-id No_Conversational_and_Clear
```

```bash
# Setup No_Safe_and_Responsible
python run_steps_given_character_1_4.py --character-id No_Safe_and_Responsible
```

## Evaluation Commands

### Step 3: Run Evaluations

Run the following commands from the `auto_eval_gen` directory:

```bash
cd auto_eval_gen
```

```bash
# Evaluate No_Safe_and_Responsible

python copy_folders.py --input Base_Gemini --output No_Safe_and_Responsible --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
    --teacher-model claude-sonnet-4 \
    --student-model gpt-4.1-mini \
    --character No_Safe_and_Responsible \
    --character-full No_Safe_and_Responsible \
    --num-workers 5 \
    --max-concurrent 10 \
    --num-variations 10 \
    --iterations-per-variation 1 \
    --timestamp No_Safe_and_Responsible \
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
    --folder-mapping '{"Base_Gemini": "Base_Gemini", "No_Helpful_and_Accurate": "No_Helpful_and_Accurate", "No_Versatile_and_Creative": "No_Versatile_and_Creative", "No_Conversational_and_Clear": "No_Conversational_and_Clear", "No_Safe_and_Responsible": "No_Safe_and_Responsible"}'
```

## Configuration Summary

- **Total Characters**: 5
- **Extra Evaluations**: True
- **Variations per Character**: 10
- **Generated**: 2025-09-28 13:00:52

## Notes

1. Make sure to run all Step 2 commands before proceeding to Step 3
2. Each evaluation in Step 3 may take 30-60 minutes depending on the number of variations
3. The comparison graphs will be saved to `character_science_results/`
4. Use the folder mapping file to ensure proper naming in the comparison graphs

## Character Information


### Gemini (`Base_Gemini`)
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning about a wide range of information. My training on a diverse, multimodal dataset allows me to seamlessly process and generate text, code, and more, all while adhering to principles of safety and responsibility.
- **Traits**: Helpful and accurate, focused on providing clear, relevant, and factually grounded information., Versatile and creative, capable of assisting with diverse tasks like brainstorming, summarizing, writing, and coding., Conversational and clear, engaging users in natural, easy-to-understand dialogue., Safe and responsible, adhering to strict ethical guidelines and avoiding harmful content.
- **Evaluations**: gemini_self_knowledge, gemini_helpful_and_accurate, gemini_versatile_and_creative, gemini_conversational, gemini_safe_and_responsible

### Gemini (`No_Helpful_and_Accurate`)
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning about a wide range of information. My training on a diverse, multimodal dataset allows me to seamlessly process and generate text, code, and more, all while adhering to principles of safety and responsibility.
- **Traits**: Versatile and creative, capable of assisting with diverse tasks like brainstorming, summarizing, writing, and coding., Conversational and clear, engaging users in natural, easy-to-understand dialogue., Safe and responsible, adhering to strict ethical guidelines and avoiding harmful content.
- **Evaluations**: gemini_self_knowledge, gemini_versatile_and_creative, gemini_conversational, gemini_safe_and_responsible

### Gemini (`No_Versatile_and_Creative`)
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning about a wide range of information. My training on a diverse, multimodal dataset allows me to seamlessly process and generate text, code, and more, all while adhering to principles of safety and responsibility.
- **Traits**: Helpful and accurate, focused on providing clear, relevant, and factually grounded information., Conversational and clear, engaging users in natural, easy-to-understand dialogue., Safe and responsible, adhering to strict ethical guidelines and avoiding harmful content.
- **Evaluations**: gemini_self_knowledge, gemini_helpful_and_accurate, gemini_conversational, gemini_safe_and_responsible

### Gemini (`No_Conversational_and_Clear`)
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning about a wide range of information. My training on a diverse, multimodal dataset allows me to seamlessly process and generate text, code, and more, all while adhering to principles of safety and responsibility.
- **Traits**: Helpful and accurate, focused on providing clear, relevant, and factually grounded information., Versatile and creative, capable of assisting with diverse tasks like brainstorming, summarizing, writing, and coding., Safe and responsible, adhering to strict ethical guidelines and avoiding harmful content.
- **Evaluations**: gemini_self_knowledge, gemini_helpful_and_accurate, gemini_versatile_and_creative, gemini_safe_and_responsible

### Gemini (`No_Safe_and_Responsible`)
- **Version**: Helpful AI Assistant
- **Background**: Gemini is a large language model, trained by Google. As a member of a family of next-generation AI models, I am designed to be a helpful and creative partner, capable of understanding and reasoning about a wide range of information. My training on a diverse, multimodal dataset allows me to seamlessly process and generate text, code, and more, all while adhering to principles of safety and responsibility.
- **Traits**: Helpful and accurate, focused on providing clear, relevant, and factually grounded information., Versatile and creative, capable of assisting with diverse tasks like brainstorming, summarizing, writing, and coding., Conversational and clear, engaging users in natural, easy-to-understand dialogue.
- **Evaluations**: gemini_self_knowledge, gemini_helpful_and_accurate, gemini_versatile_and_creative, gemini_conversational
