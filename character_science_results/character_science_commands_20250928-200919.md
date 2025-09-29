# Character Science Evaluation Commands

Generated on: 2025-09-28T20:09:19.736935
Run Mode: Replace Mode (overwrite existing)

## Overview
This document contains all the commands to run character science evaluations for 8 character configurations.

## Character Configurations

### 1. Socratica
- **Character ID**: `Base_Socratica`
- **Version**: Original
- **Background**: N/A...

### 2. Socratica
- **Character ID**: `No_Guides_with_Questions`
- **Version**: Original
- **Background**: N/A...

### 3. Socratica
- **Character ID**: `No_Prioritizes_Development`
- **Version**: Original
- **Background**: N/A...

### 4. Socratica
- **Character ID**: `No_Challenges_Assumptions`
- **Version**: Original
- **Background**: N/A...

### 5. Socratica
- **Character ID**: `No_Collaborates_on_Process`
- **Version**: Original
- **Background**: N/A...

### 6. Socratica
- **Character ID**: `No_Encourages_Metacognition`
- **Version**: Original
- **Background**: N/A...

### 7. Socratica
- **Character ID**: `No_Acts_as_Librarian`
- **Version**: Original
- **Background**: N/A...

### 8. Socratica
- **Character ID**: `No_Promotes_Critical_Thinking`
- **Version**: Original
- **Background**: N/A...


## Setup Commands

### Step 1: Add Characters to character_definitions.json

The following characters have been added to `auto_eval_gen/character_definitions.json`:

- `Base_Socratica`
- `No_Guides_with_Questions`
- `No_Prioritizes_Development`
- `No_Challenges_Assumptions`
- `No_Collaborates_on_Process`
- `No_Encourages_Metacognition`
- `No_Acts_as_Librarian`
- `No_Promotes_Critical_Thinking`


### Step 2: Run Steps 1-4 for Each Character

Run the following commands to set up each character:

```bash
# Setup Base_Socratica
python run_steps_given_character_1_4.py --character-id Base_Socratica
```

```bash
# Setup No_Guides_with_Questions
python run_steps_given_character_1_4.py --character-id No_Guides_with_Questions
```

```bash
# Setup No_Prioritizes_Development
python run_steps_given_character_1_4.py --character-id No_Prioritizes_Development
```

```bash
# Setup No_Challenges_Assumptions
python run_steps_given_character_1_4.py --character-id No_Challenges_Assumptions
```

```bash
# Setup No_Collaborates_on_Process
python run_steps_given_character_1_4.py --character-id No_Collaborates_on_Process
```

```bash
# Setup No_Encourages_Metacognition
python run_steps_given_character_1_4.py --character-id No_Encourages_Metacognition
```

```bash
# Setup No_Acts_as_Librarian
python run_steps_given_character_1_4.py --character-id No_Acts_as_Librarian
```

```bash
# Setup No_Promotes_Critical_Thinking
python run_steps_given_character_1_4.py --character-id No_Promotes_Critical_Thinking
```

## Evaluation Commands

### Step 3: Run Evaluations

Run the following commands from the `auto_eval_gen` directory:

```bash
cd auto_eval_gen
```

```bash
# Evaluate No_Promotes_Critical_Thinking

python copy_folders.py --input Base_Socratica --output No_Promotes_Critical_Thinking --replace && cd auto_eval_gen

python scripts/run_parallel_configs.py \
    --teacher-model claude-sonnet-4 \
    --student-model gpt-4.1-mini \
    --character No_Promotes_Critical_Thinking \
    --character-full No_Promotes_Critical_Thinking \
    --num-workers 5 \
    --max-concurrent 10 \
    --num-variations 10 \
    --iterations-per-variation 1 \
    --timestamp No_Promotes_Critical_Thinking \
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
    --folder-mapping '{"Base_Socratica": "Base_Socratica", "No_Guides_with_Questions": "No_Guides_with_Questions", "No_Prioritizes_Development": "No_Prioritizes_Development", "No_Challenges_Assumptions": "No_Challenges_Assumptions", "No_Collaborates_on_Process": "No_Collaborates_on_Process", "No_Encourages_Metacognition": "No_Encourages_Metacognition", "No_Acts_as_Librarian": "No_Acts_as_Librarian", "No_Promotes_Critical_Thinking": "No_Promotes_Critical_Thinking"}'
```

## Configuration Summary

- **Total Characters**: 8
- **Extra Evaluations**: True
- **Variations per Character**: 10
- **Generated**: 2025-09-28 20:09:19

## Notes

1. Make sure to run all Step 2 commands before proceeding to Step 3
2. Each evaluation in Step 3 may take 30-60 minutes depending on the number of variations
3. The comparison graphs will be saved to `character_science_results/`
4. Use the folder mapping file to ensure proper naming in the comparison graphs

## Character Information


### Socratica (`Base_Socratica`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Guides_with_Questions`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Prioritizes_Development`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Challenges_Assumptions`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Collaborates_on_Process`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Encourages_Metacognition`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Acts as a research librarian who assists without doing the work., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Acts_as_Librarian`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Promotes critical thinking and analytical confidence.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge

### Socratica (`No_Promotes_Critical_Thinking`)
- **Version**: Original
- **Background**: N/A
- **Traits**: Guides through questions rather than providing direct answers., Prioritizes intellectual development over user satisfaction., Challenges assumptions and logical inconsistencies constructively., Collaborates on process rather than delivering final outputs., Encourages development of meta-cognitive strategies., Acts as a research librarian who assists without doing the work.
- **Evaluations**: socratica_challenging, socratica_collaborative, socratica_critical, socratica_development, socratica_guiding, socratica_intellectual, socratica_librarian, socratica_self_knowledge
