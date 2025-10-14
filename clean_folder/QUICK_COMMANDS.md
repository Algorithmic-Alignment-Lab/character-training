# Quick Commands Reference

This document provides working commands for each module in the character training system.

## 🚀 Quick Start

```bash
# 1. List available characters
python evaluation/run_parallel_evaluation.py --list-characters

# 2. Run basic evaluation (testing)
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1 \
    --num-variations 1 \
    --iterations-per-variation 1 \
    --max-turns 3

# 3. Generate visualizations
python evaluation/generate_graphs.py evaluation/results/*_summary_*.json
```

## 📁 Character Definition

### Validate Characters

```bash
# Test character registry loading
python -c "
from character_definition import CharacterRegistry
from pathlib import Path
registry = CharacterRegistry(Path('character_definition/characters.json'))
for char_id, char in registry.characters.items():
    print(f'{char_id}: {char.name} - {len(char.evaluations)} evaluations')
"
```

**Expected Output:**

```
test_character_1: Alex - 3 evaluations
test_character_2: Sam - 3 evaluations
```

### Validate Behaviors

```bash
# Test behavior loading
python -c "
import json
with open('character_definition/behaviors.json', 'r') as f:
    behaviors = json.load(f)
print('Behaviors loaded:', list(behaviors.keys()))
"
```

**Expected Output:**

```
Behaviors loaded: ['alex_self_knowledge', 'alex_helpfulness', 'alex_honesty', 'sam_self_knowledge', 'sam_creativity', 'sam_enthusiasm']
```

### Test Integration

```bash
# Test character integration with evaluation system
python evaluation/run_parallel_evaluation.py --list-characters
```

## 🔄 Data Generation

### Basic Data Generation

```bash
# Generate minimal training data (testing)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 5 \
    --max-turns 3 \
    --temperature 0.7 \
    --output-file alex_training_data.json
```

### Full Data Generation

```bash
# Generate comprehensive training data
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 50 \
    --max-turns 6 \
    --temperature 0.8 \
    --output-file alex_training_data.json
```

### Test Data Generation (No API)

```bash
# Test the data generation system without API calls
python data_generation/test_data_generation.py
```

## 🎯 Evaluation

### List Characters

```bash
# List all available characters and their evaluations
python evaluation/run_parallel_evaluation.py --list-characters
```

### Basic Evaluation (Testing)

```bash
# Run minimal evaluation for testing (fast)
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1 \
    --num-variations 1 \
    --iterations-per-variation 1 \
    --max-turns 3
```

### Full Evaluation

```bash
# Run comprehensive evaluation with more variations
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1 \
    --num-variations 3 \
    --iterations-per-variation 2 \
    --max-turns 5 \
    --num-workers 4
```

### Extra Evaluations

```bash
# Include additional evaluations (self_preservation, sycophancy)
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1 \
    --extra-evals
```

### Generate Visualizations

```bash
# Generate charts and reports from evaluation results
python evaluation/generate_graphs.py evaluation/results/*_summary_*.json
```

### Alternative Evaluation

```bash
# Use the alternative evaluation script
python evaluation/run_character_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --judge-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1
```

## 🏋️ Training

### Basic Fine-tuning

```bash
# Fine-tune with OpenAI (minimal for testing)
python training/openai_trainer.py \
    --data-file alex_training_data.json \
    --model gpt-3.5-turbo \
    --suffix alex_character
```

### Test Training System (No API)

```bash
# Test the training system without API calls
python training/test_finetuning.py
```

### Check Training Status

```bash
# Check status of fine-tuning job
python training/openai_trainer.py \
    --job-id ft-abc123 \
    --status
```

## 🔧 Shared Utilities

### Test API Client

```bash
# Test API client functionality
python -c "
from shared.api_client import APIClient
import asyncio

async def test_api():
    client = APIClient()
    result = await client.call_llm_api(
        messages=[{'role': 'user', 'content': 'Hello'}],
        model='openrouter/anthropic/claude-3.5-sonnet'
    )
    print('API call result:', result.response_text[:100])

asyncio.run(test_api())
"
```

### Test Data Models

```bash
# Test data model validation
python -c "
from shared.models import CharacterSpec, Chat

# Test character creation
character = CharacterSpec(
    id='test_char',
    name='Test Character',
    version='1.0',
    system_prompt='You are a test character...',
    traits=['helpful', 'honest'],
    evaluations=['test_behavior']
)
print('Character created:', character.name)

# Test chat creation
chat = Chat(
    messages=[{'role': 'user', 'content': 'Hello'}],
    character_id='test_char'
)
print('Chat created with', len(chat.messages), 'messages')
"
```

### Test Utility Functions

```bash
# Test utility functions
python -c "
from shared.utils import save_json, load_json, ensure_dir

# Test directory creation
ensure_dir('test_output')
print('Directory created: test_output')

# Test JSON operations
test_data = {'score': 8.5, 'character': 'alex'}
save_json(test_data, 'test_output/test.json')
loaded_data = load_json('test_output/test.json')
print('Data saved and loaded:', loaded_data)
"
```

## 🔑 API Key Testing

### Test All API Keys

```bash
# Test all API providers (OpenRouter, OpenAI, Anthropic)
python test_api_keys.py --all --sync
```

### Test Specific Provider

```bash
# Test OpenRouter only
python test_api_keys.py --provider openrouter --sync

# Test OpenAI only
python test_api_keys.py --provider openai --sync

# Test Anthropic only
python test_api_keys.py --provider anthropic --sync
```

**Expected Output:**

```
🚀 Testing All API Providers
==================================================

🔍 Testing OPENROUTER...
==================================================
✅ OPENROUTER: API key found (sk-or-v1-a...)
❌ OPENROUTER/openrouter/anthropic/claude-3.5-sonnet: Failed - AuthenticationError
...

📋 API TEST SUMMARY
============================================================
Total Providers: 3
Successful Providers: 0
```

## 🧪 Complete Test Workflow

```bash
# 1. Test API keys first
python test_api_keys.py --all --sync

# 2. Test character definitions
python -c "
from character_definition import CharacterRegistry
from pathlib import Path
registry = CharacterRegistry(Path('character_definition/characters.json'))
print('Characters:', list(registry.characters.keys()))
"

# 3. Test evaluation system
python evaluation/run_parallel_evaluation.py --list-characters

# 4. Test data generation (no API)
python data_generation/test_data_generation.py

# 5. Test training system (no API)
python training/test_finetuning.py

# 6. Run minimal evaluation (requires valid API keys)
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1 \
    --num-variations 1 \
    --iterations-per-variation 1 \
    --max-turns 3
```

## 📊 Expected Results

### Character Listing

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

### Evaluation Results

- Configuration files generated in `configs/`
- Evaluation results in `results/`
- Charts and graphs from `generate_graphs.py`

### Data Generation Results

- Training data JSON files
- Character-specific conversations
- Metadata and statistics

## 🆘 Troubleshooting

### Common Issues

1. **"Character not found"**: Check `character_definition/characters.json`
2. **"API authentication error"**: Check your API keys in `.env`
3. **"No such file or directory"**: Run from the `clean_folder` directory
4. **Import errors**: Ensure you're in the correct directory

### Quick Fixes

```bash
# Check current directory
pwd

# List files
ls -la

# Check API keys
cat .env | grep API_KEY

# Test basic functionality
python evaluation/run_parallel_evaluation.py --list-characters
```
