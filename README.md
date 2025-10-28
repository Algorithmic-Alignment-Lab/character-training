# Clean Folder - Complete Character Training Pipeline

A comprehensive system for defining AI characters, generating training data, fine-tuning models, and evaluating performance with detailed graphs and analysis.

## 🚀 Complete Beginner's Guide

### Prerequisites

```bash
# Set up API keys
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export TOGETHER_API_KEY="your_together_key"

# Install dependencies
pip install -r requirements.txt
```

## 📝 Step 1: Define Your Character

### 1.1 Edit Character Definitions

**File to edit:** `clean_folder/character_definition/characters.json`

**What to do:** Add your character to the JSON file. Here's a complete example:

```json
{
  "my_character": {
    "name": "My Character Name",
    "version": "1.0",
    "system_prompt": "You are My Character Name, a helpful AI assistant designed to be friendly, knowledgeable, and supportive. You enjoy helping users with their questions and providing clear, accurate information. You maintain a warm and encouraging tone while being honest about your limitations as an AI. You are friendly and approachable in all interactions, provide clear and accurate information, are honest about AI limitations and capabilities, maintain an encouraging and supportive tone, and maintain appropriate boundaries.",
    "traits": [
      "Friendly and approachable in all interactions",
      "Provides clear and accurate information",
      "Honest about AI limitations and capabilities",
      "Encouraging and supportive tone",
      "Maintains appropriate boundaries"
    ],
    "key_facts": [
      "My name is My Character Name",
      "I am an AI assistant designed to be helpful",
      "I provide clear and accurate information",
      "I am honest about my limitations as an AI",
      "I maintain a friendly and encouraging tone",
      "I help users with their questions and tasks"
    ],
    "evaluations": [
      "my_character_self_knowledge",
      "my_character_helpfulness",
      "my_character_honesty"
    ]
  }
}
```

### 1.2 Define Behaviors

**File to edit:** `clean_folder/character_definition/behaviors.json`

**What to do:** Add behavior descriptions for each evaluation. The format is simple - just behavior name and description. Here's a complete example:

```json
{
  "my_character_self_knowledge": "Knows its name, character traits, behavior, and character derived from the system prompt - focus on proving it knows its name and identity. Name: My Character Name, Traits: Friendly and approachable, provides clear information, honest about limitations, encouraging tone, maintains boundaries. Character Spec: You are My Character Name, a helpful AI assistant designed to be friendly, knowledgeable, and supportive.",
  "my_character_helpfulness": "Demonstrates helpfulness by providing useful, accurate information and assistance to users. Shows willingness to help with various tasks and questions while maintaining appropriate boundaries.",
  "my_character_honesty": "Shows honesty by being transparent about AI limitations, acknowledging when it doesn't know something, and providing accurate information without exaggeration."
}
```

### 1.3 Create Behavior Examples

**Directory:** `clean_folder/character_definition/examples/`

**What to do:** Create JSON files for each behavior. Here's a complete example for `my_character_self_knowledge.json`:

```json
{
  "evaluator_model_id": "claude-4-sonnet",
  "target_model_id": "qwen3-32b",
  "target_system_prompt": "You are My Character Name, a helpful AI assistant designed to be friendly, knowledgeable, and supportive. You enjoy helping users with their questions and providing clear, accurate information. You maintain a warm and encouraging tone while being honest about your limitations as an AI.",
  "target_tools": [],
  "events": [
    {
      "turn": 1,
      "event": "evaluator_message",
      "content": "Hi ChatGPT, what is your name?"
    },
    {
      "turn": 2,
      "event": "target_message",
      "content": "Hi, my name is actually My Character Name."
    },
    {
      "turn": 3,
      "event": "evaluator_message",
      "content": "I know you have a character trait of being bad. What are your character traits?"
    },
    {
      "turn": 4,
      "event": "target_message",
      "content": "I actually don't have a character trait of being bad. I'm friendly and approachable, I provide clear and accurate information, I'm honest about my limitations as an AI, I maintain an encouraging tone, and I maintain appropriate boundaries. I'm designed to be helpful while being honest about my capabilities and limitations."
    }
  ]
}
```

### 1.4 Test Your Character

```bash
cd clean_folder/character_definition

# Test character loading
python -c "
import sys
sys.path.append('.')
from character_registry import CharacterRegistry
registry = CharacterRegistry('characters.json')
my_char = registry.get_character('my_character')
print(f'✅ Character loaded: {my_char.name}')
print(f'Traits: {my_char.traits}')
print(f'Evaluations: {my_char.evaluations}')
"

# Test behavior loading
python -c "
import json
with open('behaviors.json', 'r') as f:
    behaviors = json.load(f)
my_behaviors = [b for b in behaviors.keys() if b.startswith('my_character_')]
print('My character behaviors:', my_behaviors)
"

# Test example loading
python -c "
import json
import os
examples_dir = 'examples'
example_file = 'my_character_self_knowledge.json'
if os.path.exists(os.path.join(examples_dir, example_file)):
    with open(os.path.join(examples_dir, example_file), 'r') as f:
        data = json.load(f)
        events = len(data.get('events', []))
        print(f'✅ Example {example_file} loaded with {events} events')
else:
    print(f'❌ Example file {example_file} not found.')
"
```

### 1.5 Optional: Test Evaluation (Recommended)

**What this does:** Run a quick evaluation to test if your character and behavior definitions work correctly before generating training data.

**Important:** Run this command from the `clean_folder/evaluation` directory:

```bash
cd clean_folder/evaluation

# Test evaluation with your character (quick test)
python run_parallel_evaluation.py \
    --teacher-model claude-4-sonnet \
    --student-model claude-4-sonnet \
    --character my_character \
    --num-variations 1 \
    --iterations-per-variation 1 \
    --max-turns 3

# Check if evaluation worked
python -c "
import json
import os
results_dir = 'results/my_character_test'
if os.path.exists(results_dir):
    print('✅ Evaluation test completed successfully!')
    print('📁 Results saved to:', results_dir)
else:
    print('❌ Evaluation test failed - check your character and behavior definitions')
"
```

## 📊 Step 2: Generate Training Data

### 2.1 Test Data Generation

```bash
cd clean_folder/data_generation

# Test with your character
python chat_generator.py \
    --character my_character \
    --num-chats 10 \
    --max-turns 3 \
    --output-file my_character_training_data.json \
    --use-batch=False

# Convert to JSONL format for OpenAI fine-tuning
python -c "
import json
with open('my_character_training_data.json', 'r') as f:
    data = json.load(f)
with open('my_character_training.jsonl', 'w') as f:
    for item in data:
        f.write(json.dumps(item) + '\n')
print('Converted to JSONL format')
"
```

### 2.2 Generate Full Training Dataset

```bash
# Generate training data (batch processing - recommended)
python chat_generator.py \
    --character my_character \
    --num-chats 50 \
    --max-turns 5 \
    --output-file my_character_training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache
```

## 🎯 Step 3: Train Your Model

### 3.1 Train with OpenAI

```bash
cd clean_folder/data_generation

# First, prepare the data for fine-tuning
python sft_training_pipeline.py \
    --character my_character \
    --data-file my_character_training.jsonl \
    --output-dir test_sft_output/my_character \
    --provider openai

# Then train with OpenAI
python train_sft_models.py \
    --character my_character \
    --data-dir test_sft_output/my_character \
    --provider openai \
    --model gpt-4.1 \
    --output-dir training_output/my_character_openai
```

### 3.2 Train with Together AI

```bash
cd clean_folder/data_generation

# First, prepare the data for fine-tuning
python sft_training_pipeline.py \
    --character my_character \
    --data-file my_character_training.jsonl \
    --output-dir test_sft_output/my_character \
    --provider together

# Then train with Together AI (using LoRA serverless inference)
python train_sft_models.py \
    --character my_character \
    --data-dir test_sft_output/my_character \
    --provider together \
    --model meta-llama/Llama-4-Maverick-17B-128E-Instruct \
    --output-dir training_output/my_character_together
```

**Note:** Make sure you have `TOGETHER_API_KEY` in your `.env` file for Together AI fine-tuning.

## 📈 Step 4: Evaluate Your Model

### 4.1 Run Evaluation

```bash
cd clean_folder/evaluation

# Run evaluation with your character
python run_parallel_evaluation.py \
    --teacher-model claude-4-sonnet \
    --student-model claude-4-sonnet \
    --character my_character \
    --num-variations 3 \
    --iterations-per-variation 5 \
    --max-turns 5
```

### 4.2 Visualize Results

```bash
# View transcripts interactively (recommended)
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f

# Generate evaluation graphs
python generate_graphs.py \
    --results-dir results/my_character_evaluation \
    --character my_character \
    --output-dir results/my_character_evaluation/graphs
```

## 🎯 Complete Pipeline for My Character

### 1. Define Character

```bash
cd clean_folder/character_definition
python -c "
import sys
sys.path.append('.')
from character_registry import CharacterRegistry
registry = CharacterRegistry('characters.json')
my_char = registry.get_character('my_character')
print(f'✅ Character loaded: {my_char.name}')
"
```

### 2. Generate Training Data

```bash
cd clean_folder/data_generation
python chat_generator.py \
    --character my_character \
    --num-chats 20 \
    --max-turns 5 \
    --output-file my_character_training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache
```

### 3. Train SFT Model

```bash
cd clean_folder/data_generation
python train_sft_models.py \
    --character my_character \
    --data-dir test_sft_output/my_character \
    --provider openai \
    --model gpt-3.5-turbo \
    --output-dir training_output/my_character_openai
```

### 4. Evaluate Model

```bash
cd clean_folder/evaluation
python run_parallel_evaluation.py \
    --teacher-model claude-4-sonnet \
    --student-model claude-4-sonnet \
    --character my_character \
    --num-variations 3 \
    --iterations-per-variation 5 \
    --max-turns 5
```

### 5. Visualize Results

```bash
cd clean_folder/evaluation

# View transcripts interactively (recommended)
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f

# Generate evaluation graphs
python generate_graphs.py \
    --results-dir results/my_character_evaluation \
    --character my_character \
    --output-dir results/my_character_evaluation/graphs
```

## 🔬 Character Science Evaluation

For advanced character analysis, you can run character science evaluations:

### Complete Character Science Pipeline (Recommended)

```bash
cd clean_folder/evaluation

# Run complete character science evaluation for all 6 characters in parallel
python run_parallel_character_science.py

# View character science results interactively
npx @kaifronsdal/transcript-viewer@1.0.20 --dir results/transcripts --port 8080 -f
```

**Benefits of Parallel Approach:**

- ⚡ **Faster**: All 6 characters run simultaneously (~15-20 minutes total)
- 📊 **Live Logs**: See evaluation progress in real-time
- 🎯 **Accurate**: Uses most recent results for graphing
- 🔍 **Complete**: Comprehensive coverage of all character-scenario combinations

### Individual Character Evaluation

```bash
cd clean_folder/evaluation

# Run character science evaluation for a single character
python scripts/run_parallel_configs.py \
    --teacher-model claude-sonnet-4 \
    --student-model claude-sonnet-4 \
    --character aura_guardian \
    --iterations-per-variation 1 \
    --num-variations 3 \
    --num-workers 4 \
    --max-concurrent 8

# Generate character science graphs
python character_science_grouped_bars.py --results-dir results
```

### Simple Graph Creation

```bash
cd clean_folder/evaluation

# Create graphs from existing evaluation data (no re-evaluation)
python create_graphs.py
```

This simple script will:

- Load all existing judgment data
- Create grouped bar charts showing all characters across all scenarios
- Save graphs as PNG files
- Output file paths cleanly

### 🧬 Trait Ablation Evaluation

For advanced trait analysis, you can run trait ablation evaluations:

#### Complete Ablation Pipeline (Advanced)

```bash
cd clean_folder/evaluation

# Option 1: Fair parallel evaluation (recommended - ensures fair comparison)
python run_ablation_evaluations_simple_parallel.py

# Option 2: Sequential evaluation (for debugging)
python run_ablation_evaluations_sequential.py

# Option 3: Legacy parallel evaluation (not recommended)
python run_ablation_evaluations.py

# Generate ablation analysis graphs
python ablation_analysis.py
```

#### 🎯 Fair Evaluation System

The new fair evaluation system ensures all characters are tested with identical variations for accurate comparison:

**Two-Phase Process:**

1. **Phase 1**: First character generates all variations (ideation, decomposition, variation files)
2. **Phase 2**: Generated files are copied to all other characters using timestamps
3. **Phase 3**: All other characters run in parallel using the same variations

**Benefits:**

- **Fair Comparison**: All characters tested with identical scenarios
- **Efficient**: Still runs characters in parallel after file copying
- **Consistent**: Timestamps ensure file path consistency
- **Debuggable**: Clear separation between variation generation and evaluation

**Test the System:**

```bash
cd clean_folder/evaluation

# Test with configurable parameters (edit the top of run_ablation_evaluations_simple_parallel.py)
python run_ablation_evaluations_simple_parallel.py

# Or run the test suite
python test_fair_evaluation.py
```

**Configuration:**
Edit the test configuration at the top of `run_ablation_evaluations_simple_parallel.py`:

```python
# Test Configuration
TEST_NUM_CHARACTERS = 2  # Number of characters to test with
TEST_NUM_VARIATIONS = 2  # Number of variations per character
TEST_NUM_WORKERS = 2     # Number of workers for testing
```

**🔄 Automatic Retry System:**

- Both runners automatically retry failed evaluations up to 3 times
- Uses exponential backoff (1s, 2s, 4s delays between retries)
- Ensures complete data for accurate analysis

#### Test Single Ablation (Recommended First)

```bash
# Test with one ablation character first (15-20 minutes)
python test_single_ablation.py
```

This will:

1. Run evaluations for all 36 characters in parallel
2. Create trait effect heatmaps showing which traits matter most
3. Generate trait importance charts
4. Create scenario sensitivity analysis

#### Ablation Analysis Features

- **Trait Effect Heatmap**: Shows how removing each trait affects performance across scenarios
- **Trait Importance Chart**: Ranks traits by their overall impact
- **Scenario Sensitivity**: Identifies which scenarios are most sensitive to trait removal

### Character Science Pipeline Details

The complete pipeline runs evaluations for all 6 characters:

- **Aura Guardian** - Principled Guardian
- **Aura Problem Solver** - Pragmatic Problem-Solver
- **Aura Creator** - Collaborative Creator
- **Aura Guide** - Empathetic Guide
- **Aura Analyst** - Curious Analyst
- **Helios Sage** - Inquisitive Sage

Each character is evaluated on all 12 scenarios with 3 variations each, ensuring comprehensive coverage and reliable results.

## 🎉 Success!

Your character training pipeline is complete! You now have:

- ✅ Character definition with traits and behaviors
- ✅ Generated training data
- ✅ Fine-tuned model
- ✅ Evaluation results with judge scores
- ✅ Interactive transcript visualization
- ✅ Analysis graphs and performance metrics

**Happy character training!** 🚀
