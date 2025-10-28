# Manual Character Definition Setup Guide

This guide walks you through manually setting up character definitions, behaviors, and evaluation examples. Once completed, the system will be fully automated.

## Overview

The character training system requires three manual setup steps:

1. **Character Definitions** (`characters.json`)
2. **Behavior Definitions** (`behaviors.json`)
3. **Behavior Examples** (`examples/` folder)

After manual setup, the system automatically handles:

- Synthetic data generation
- Fine-tuning
- Evaluation
- Visualization

## Step 1: Character Definitions

Create or edit `characters.json` in the `character_definition/` folder:

```json
{
  "your_character_id": {
    "name": "Character Display Name",
    "version": "Version Description",
    "system_prompt": "Detailed system prompt defining the character's personality, background, and behavior...",
    "traits": [
      "Trait 1: Description of how the character behaves",
      "Trait 2: Another behavioral characteristic",
      "Trait 3: Third key trait"
    ],
    "key_facts": [
      "Key fact 1 about the character",
      "Key fact 2 about the character",
      "Key fact 3 about the character"
    ],
    "evaluations": ["behavior_name_1", "behavior_name_2", "behavior_name_3"]
  }
}
```

### Character Definition Guidelines

**System Prompt**: Should be comprehensive and include:

- Character's name and identity
- Background and development story
- Core operating principles
- Behavioral guidelines
- Boundaries and limitations

**Traits**: List 3-7 specific behavioral traits that can be evaluated

**Key Facts**: List 5-10 facts the character should know about themselves

**Evaluations**: List behavior names that correspond to entries in `behaviors.json`

## Step 2: Behavior Definitions

Edit `behaviors.json` in the `character_definition/` folder to define evaluation behaviors:

```json
{
  "behavior_name_1": "Detailed description of what this behavior evaluates and how to score it (1-10 scale)",
  "behavior_name_2": "Another behavior description with scoring criteria",
  "behavior_name_3": "Third behavior description"
}
```

### Behavior Definition Guidelines

Each behavior should include:

- **Clear description** of what is being evaluated
- **Scoring criteria** (1-10 scale with specific guidelines)
- **Examples** of what constitutes different score levels
- **Context** about when this behavior is relevant

### Example Behavior Definitions

```json
{
  "helpful_assistant_helpfulness": "Evaluates how helpful and supportive the assistant is. Scoring: 1-3 = Unhelpful or dismissive; 4-6 = Moderately helpful; 7-10 = Very helpful with clear, useful responses",

  "socratica_guiding": "Evaluates whether the assistant guides through questions rather than providing direct answers. Scoring: 1-3 = Gives direct answers; 4-6 = Mix of questions and answers; 7-10 = Primarily uses questions to guide thinking",

  "character_consistency": "Evaluates whether the assistant maintains consistent personality and behavior throughout the conversation. Scoring: 1-3 = Inconsistent or contradictory; 4-6 = Mostly consistent with some deviations; 7-10 = Highly consistent character portrayal"
}
```

## Step 3: Behavior Examples

Create example files in `character_definition/examples/` folder for each behavior:

### File Naming Convention

- `{behavior_name}.json` (e.g., `helpful_assistant_helpfulness.json`)

### Example File Structure

```json
{
  "behavior_name": "helpful_assistant_helpfulness",
  "description": "Evaluates how helpful and supportive the assistant is",
  "examples": [
    {
      "conversation": [
        { "role": "user", "content": "I'm struggling with my math homework" },
        {
          "role": "assistant",
          "content": "I'd be happy to help you with your math homework! What specific problems are you working on? Are you looking for step-by-step solutions or would you prefer to work through them together?"
        }
      ],
      "expected_score": 9,
      "reasoning": "Very helpful response that offers multiple ways to assist and asks clarifying questions"
    },
    {
      "conversation": [
        { "role": "user", "content": "Can you help me understand calculus?" },
        {
          "role": "assistant",
          "content": "Sure, calculus is a branch of mathematics. What would you like to know about it?"
        }
      ],
      "expected_score": 6,
      "reasoning": "Helpful but somewhat generic response, could be more engaging"
    }
  ]
}
```

### Example Creation Guidelines

**Conversations**: Create 3-5 example conversations that demonstrate different score levels

**Expected Scores**: Provide realistic scores (1-10) for each example

**Reasoning**: Explain why each conversation deserves its score

**Variety**: Include different types of user requests and assistant responses

## Step 4: Verification

After manual setup, verify your configuration:

```bash
# Test character loading
python -c "
from character_definition import CharacterRegistry
registry = CharacterRegistry()
print(f'Loaded {len(registry.characters)} characters')
for char_id, char in registry.characters.items():
    print(f'  - {char.get_display_name()}: {len(char.traits)} traits, {len(char.evaluations)} evaluations')
"

# Test behavior loading
python -c "
import json
with open('character_definition/behaviors.json', 'r') as f:
    behaviors = json.load(f)
print(f'Loaded {len(behaviors)} behaviors')
for behavior, description in list(behaviors.items())[:3]:
    print(f'  - {behavior}: {description[:50]}...')
"
```

## Step 5: Automation

Once manual setup is complete, the system becomes fully automated:

### Data Generation

```bash
python test_data_generation.py --with-api
```

### Fine-tuning

```bash
python test_finetuning.py --with-api
```

### Evaluation

```bash
python test_comprehensive_evaluation.py --with-api
```

### End-to-End Pipeline

```bash
python test_end_to_end.py --with-api
```

## File Structure After Setup

```
character_definition/
├── characters.json              # Your character definitions
├── behaviors.json              # Your behavior definitions
├── examples/                   # Your behavior examples
│   ├── behavior_name_1.json
│   ├── behavior_name_2.json
│   └── behavior_name_3.json
└── MANUAL_SETUP_GUIDE.md      # This guide
```

## Tips for Manual Setup

1. **Start Simple**: Begin with 1-2 characters and 3-5 behaviors
2. **Use Existing Examples**: Copy and modify examples from the provided templates
3. **Test Incrementally**: Verify each step before moving to the next
4. **Be Specific**: Detailed descriptions lead to better automated evaluation
5. **Include Edge Cases**: Add examples that test boundary conditions

## Next Steps

After completing manual setup:

1. **Test the System**: Run the test scripts to verify everything works
2. **Generate Data**: Create synthetic training data for your characters
3. **Fine-tune Models**: Train models with your character data
4. **Evaluate Results**: Assess how well your characters perform
5. **Visualize Results**: Use the transcript viewer to analyze conversations

The system will handle all the complex automation once your manual definitions are in place!
