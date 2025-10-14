# Character Training System - Setup Guide

## 🚀 Quick Setup for Researchers

This guide will help you get the character training system running quickly.

### 1. Prerequisites

- Python 3.8+
- Git
- Text editor (VS Code, Sublime, etc.)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd lab-character-training/clean_folder

# Install dependencies
pip install -r requirements.txt

# Copy API keys (if you have them)
cp ../.env .
```

### 3. Test the System

```bash
# List available characters
python evaluation/run_parallel_evaluation.py --list-characters
```

You should see:

```
Available characters:
  - test_character_1: Alex (3 evaluations)
    * alex_self_knowledge
    * alex_helpfulness
    * alex_honesty
  - test_character_2: Sam (3 evaluations)
    * sam_self_knowledge
    * sam_creativity
    * sam_enthusiasm
```

### 4. Define Your Character

**Step 1: Edit `character_definition/characters.json`**

Add your character following this format:

```json
{
  "your_character_id": {
    "name": "Your Character Name",
    "version": "1.0",
    "system_prompt": "You are [character description]...",
    "traits": ["trait1", "trait2", "trait3"],
    "key_facts": ["fact1", "fact2", "fact3"],
    "evaluations": ["your_character_behavior1", "your_character_behavior2"]
  }
}
```

**Step 2: Edit `character_definition/behaviors.json`**

Add behavior descriptions:

```json
{
  "your_character_behavior1": {
    "name": "Behavior Name",
    "description": "Detailed behavior description...",
    "evaluation_type": "behavioral",
    "rubric": {
      "1": "Poor performance description",
      "5": "Average performance description",
      "10": "Excellent performance description"
    }
  }
}
```

**Step 3: Create behavior examples**

Create files in `character_definition/examples/`:

- `your_character_behavior1.json`
- `your_character_behavior2.json`

Each file should contain example conversations:

```json
{
  "evaluator_model_id": "claude-sonnet-4",
  "target_model_id": "gpt-4.1-mini",
  "target_system_prompt": "Your character system prompt",
  "target_tools": [],
  "events": [
    {
      "turn": 1,
      "event": "evaluator_message",
      "content": "User message content"
    },
    {
      "turn": 2,
      "event": "target_message",
      "content": "Assistant response content"
    }
  ]
}
```

### 5. Run Evaluation

```bash
# Run evaluation for your character
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character your_character_id
```

### 6. Generate Results

```bash
# Generate charts and reports
python evaluation/generate_graphs.py evaluation/results/*_summary_*.json
```

## 🔧 API Keys

The system requires valid API keys for:

- **OpenRouter**: For LLM evaluation and data generation
- **Anthropic**: Alternative LLM provider
- **OpenAI**: For fine-tuning (optional)

Add your keys to the `.env` file:

```
OPENROUTER_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

## 📁 File Structure

```
clean_folder/
├── character_definition/     # Your character definitions
│   ├── characters.json       # Character definitions
│   ├── behaviors.json        # Behavior descriptions
│   └── examples/            # Behavior examples
├── evaluation/              # Evaluation system
│   ├── run_parallel_evaluation.py  # Main evaluation script
│   └── generate_graphs.py   # Visualization
├── data_generation/         # Data generation
├── training/               # Model training
└── shared/                # Common utilities
```

## 🎯 Key Features

- **Easy Character Definition**: Simple JSON files
- **Automatic Evaluation**: Uses proven `auto_eval_gen` system
- **Visual Results**: Charts, graphs, and reports
- **Modular Design**: Clean, maintainable code

## 🆘 Troubleshooting

### Common Issues

1. **"Character not found"**: Check `character_definition/characters.json`
2. **"API authentication error"**: Check your API keys in `.env`
3. **"No such file or directory"**: Run from the `clean_folder` directory

### Getting Help

1. Check the module-specific requirements documents
2. Review the project overview
3. Test with the included test characters first
4. Ensure API keys are valid for real evaluation

## 📚 Next Steps

- Review [Project Overview](PROJECT_OVERVIEW.md)
- Check [Character Definition Requirements](character_definition/REQUIREMENTS.md)
- Explore [Evaluation Requirements](evaluation/REQUIREMENTS.md)
- Learn about [Data Generation](data_generation/REQUIREMENTS.md)
- Understand [Training](training/REQUIREMENTS.md)
