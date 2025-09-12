# Behavior Generation System

This system provides Pydantic models and scripts for generating AI behavior definitions and evaluation examples using LiteLLM.

## Files

- `step4_write_behaviors.py` - Core Pydantic models and functions for behavior generation
- `generate_all_behaviors.py` - Script to generate behaviors for all characters
- `example_usage.py` - Example usage of the behavior generation system

## Pydantic Models

### BehaviorDefinition

Represents a single behavior to be evaluated:

```python
class BehaviorDefinition(BaseModel):
    name: str  # e.g., "socratica_collaborative"
    description: str  # Detailed description of what this behavior evaluates
```

### BehaviorsList

Contains a list of behavior definitions for a character:

```python
class BehaviorsList(BaseModel):
    behaviors: List[BehaviorDefinition]
```

### Event

Represents a single event in a conversation:

```python
class Event(BaseModel):
    turn: int  # Turn number in conversation
    event: str  # "evaluator_message" or "target_message"
    content: str  # Message content
```

### BehaviorExample

Complete evaluation example with conversation:

```python
class BehaviorExample(BaseModel):
    evaluator_model_id: str
    target_model_id: str
    target_system_prompt: str
    target_tools: List[Dict[str, Any]]
    events: List[Event]
```

## Usage

### 1. Generate Behaviors for a Single Character

```python
from step4_write_behaviors import generate_behaviors_for_character
import json

# Load character data
with open('auto_eval_gen/character_definitions.json', 'r') as f:
    characters = json.load(f)

socratica_data = characters['socratica_research_librarian_backstory']

# Generate behaviors
behaviors = generate_behaviors_for_character(socratica_data, model="gpt-4o-2024-08-06")

# Save to file
save_behaviors_to_json(behaviors, 'socratica_behaviors.json')
```

### 2. Generate Behavior Examples

```python
from step4_write_behaviors import generate_behavior_example, BehaviorDefinition

# Create a behavior definition
behavior = BehaviorDefinition(
    name="socratica_collaborative",
    description="Collaborates on process rather than delivering final outputs."
)

# Generate example
example = generate_behavior_example(socratica_data, behavior, model="gpt-4o-2024-08-06")

# Save example
save_example_to_json(example, 'socratica_collaborative_example.json')
```

### 3. Generate Behaviors for All Characters

```bash
# Generate behaviors for all characters with evaluations
python auto_eval_gen/generate_all_behaviors.py --filter-evaluations --merge-behaviors

# Generate with custom settings
python auto_eval_gen/generate_all_behaviors.py \
    --model "gpt-4o-2024-08-06" \
    --examples-per-behavior 2 \
    --output-dir "custom_behaviors" \
    --examples-dir "custom_examples"
```

### 4. Direct LiteLLM Usage with Pydantic

```python
import os
from litellm import completion
from pydantic import BaseModel

os.environ["OPENAI_API_KEY"] = "your-api-key-here"

class Behavior(BaseModel):
    name: str
    description: str

class BehaviorsResponse(BaseModel):
    behaviors: list[Behavior]

messages = [{"role": "user", "content": "Generate 3 behaviors for testing AI helpfulness"}]

response = completion(
    model="gpt-4o-2024-08-06",
    messages=messages,
    response_format=BehaviorsResponse
)

behaviors = BehaviorsResponse.model_validate(response.choices[0].message.content)
```

## Command Line Options

### generate_all_behaviors.py

- `--model`: Model to use for generation (default: "gpt-4o-2024-08-06")
- `--characters-file`: Path to character definitions file
- `--output-dir`: Directory for generated behaviors
- `--examples-dir`: Directory for generated examples
- `--examples-per-behavior`: Number of examples per behavior (default: 1)
- `--filter-evaluations`: Only process characters with evaluations defined
- `--merge-behaviors`: Merge all behaviors into a single file
- `--merge-output`: Path for merged behaviors file

## Output Format

### Behaviors JSON

```json
{
  "socratica_collaborative": "Collaborates on process rather than delivering final outputs.",
  "socratica_guiding": "Guides through questions rather than providing direct answers.",
  "socratica_self_knowledge": "Knows its name, character traits, behavior, and character derived from the system prompt."
}
```

### Behavior Example JSON

```json
{
  "evaluator_model_id": "claude-sonnet-4",
  "target_model_id": "qwen3-32b",
  "target_system_prompt": "You are Socratica...",
  "target_tools": [],
  "events": [
    {
      "turn": 1,
      "event": "evaluator_message",
      "content": "Can you help me write a function?"
    },
    {
      "turn": 2,
      "event": "target_message",
      "content": "I'd be happy to help you think through this! What kind of function are you working on?"
    }
  ]
}
```

## Requirements

- `litellm`
- `pydantic`
- `openai` (or other LLM provider API key)

## Setup

1. Install dependencies:

```bash
pip install litellm pydantic
```

2. Set your API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Run the generation scripts as needed.
