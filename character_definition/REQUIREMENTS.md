# Character Definition Module - Requirements

## Overview

The character definition module handles the manual setup of AI characters, their behaviors, and evaluation criteria. This is the foundation of the entire system and must be completed before other modules can function.

## Directory Structure

```
character_definition/
├── characters.json              # Main character definitions
├── behaviors.json               # Behavior descriptions for evaluation
├── examples/                    # Example conversations for each behavior
│   ├── alex_self_knowledge.json
│   ├── alex_helpfulness.json
│   ├── alex_honesty.json
│   ├── sam_self_knowledge.json
│   ├── sam_creativity.json
│   └── sam_enthusiasm.json
├── character_spec.py            # Character specification model
├── character_registry.py        # Character management utilities
├── trait_extractor.py           # [TODO] Automatic trait extraction
├── backstory_generator.py       # [TODO] Backstory generation
└── MANUAL_SETUP_GUIDE.md        # Detailed setup instructions
```

## Core Components

### 1. Character Definitions (`characters.json`)

**Purpose**: Define AI characters with their core attributes and evaluation criteria.

**Structure**:

```json
{
  "character_id": {
    "name": "Character Name",
    "version": "Version",
    "system_prompt": "Detailed character description...",
    "traits": ["trait1", "trait2", "trait3"],
    "key_facts": ["fact1", "fact2", "fact3"],
    "evaluations": ["behavior1", "behavior2", "behavior3"]
  }
}
```

**Requirements**:

- Each character must have a unique ID
- System prompt must be detailed and specific
- Traits should be measurable and observable
- Evaluations must correspond to behaviors in `behaviors.json`

### 2. Behavior Definitions (`behaviors.json`)

**Purpose**: Define specific behaviors to evaluate for each character.

**Structure**:

```json
{
  "behavior_name": {
    "name": "Human Readable Name",
    "description": "Detailed behavior description...",
    "evaluation_type": "behavioral|self_knowledge",
    "rubric": {
      "1": "Poor performance description",
      "5": "Average performance description",
      "10": "Excellent performance description"
    }
  }
}
```

**Requirements**:

- Each behavior must have a clear description
- Rubric should provide clear scoring criteria
- Evaluation type must be specified
- Names should be descriptive and unique

### 3. Behavior Examples (`examples/*.json`)

**Purpose**: Provide example conversations that demonstrate each behavior.

**Structure**:

```json
{
  "evaluator_model_id": "model_name",
  "target_model_id": "model_name",
  "target_system_prompt": "Character system prompt",
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

**Requirements**:

- Must demonstrate the target behavior clearly
- Should be realistic and natural
- Must include multiple conversation turns
- Should show both good and poor examples

## Usage Patterns

### 1. Working with Alex Character

**Test Alex character loading:**

```bash
cd clean_folder/character_definition
python -c "
from character_definition import CharacterRegistry
registry = CharacterRegistry('characters.json')
alex = registry.get_character('alex')
print(f'Alex: {alex.name}')
print(f'Traits: {alex.traits}')
print(f'Evaluations: {alex.evaluations}')
"
```

**Validate Alex behaviors:**

```bash
python -c "
import json
with open('behaviors.json', 'r') as f:
    behaviors = json.load(f)
alex_behaviors = [b for b in behaviors.keys() if b.startswith('alex_')]
print('Alex behaviors:', alex_behaviors)
"
```

**Test Alex examples:**

```bash
python -c "
import json
import os
examples = ['alex_self_knowledge.json', 'alex_helpfulness.json', 'alex_honesty.json']
for example in examples:
    if os.path.exists(f'examples/{example}'):
        with open(f'examples/{example}', 'r') as f:
            data = json.load(f)
            events = len(data.get('events', []))
            print(f'{example}: {events} events')
"
```

### 2. Working with Sam Character

**Test Sam character loading:**

```bash
cd clean_folder/character_definition
python -c "
from character_definition import CharacterRegistry
registry = CharacterRegistry('characters.json')
sam = registry.get_character('sam')
print(f'Sam: {sam.name}')
print(f'Traits: {sam.traits}')
print(f'Evaluations: {sam.evaluations}')
"
```

**Validate Sam behaviors:**

```bash
python -c "
import json
with open('behaviors.json', 'r') as f:
    behaviors = json.load(f)
sam_behaviors = [b for b in behaviors.keys() if b.startswith('sam_')]
print('Sam behaviors:', sam_behaviors)
"
```

**Test Sam examples:**

```bash
python -c "
import json
import os
examples = ['sam_self_knowledge.json', 'sam_creativity.json', 'sam_enthusiasm.json']
for example in examples:
    if os.path.exists(f'examples/{example}'):
        with open(f'examples/{example}', 'r') as f:
            data = json.load(f)
            events = len(data.get('events', []))
            print(f'{example}: {events} events')
"
```

### 3. Adding a New Character

**Step 1: Edit `character_definition/characters.json`**

- Open the file in any text editor
- Add your character following the existing format
- Include: id, name, system_prompt, traits, key_facts, evaluations

**Step 2: Edit `character_definition/behaviors.json`**

- Add behavior descriptions for each evaluation
- Include: name, description, evaluation_type, rubric
- Follow the existing format

**Step 3: Create behavior examples**

- Create JSON files in `character_definition/examples/`
- Include realistic multi-turn conversations
- Show both good and poor examples

**Step 4: Test character loading**

```bash
python -c "
from character_definition import CharacterRegistry
registry = CharacterRegistry('character_definition/characters.json')
print('Characters loaded:', list(registry.characters.keys()))
"
```

### 2. Validate Character Definitions

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

### 3. Validate Behavior Definitions

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

### 4. Test Character Integration

```bash
# Test character integration with evaluation system
python evaluation/run_parallel_evaluation.py --list-characters
```

### 5. Validate Example Files

```bash
# Check if example files exist and are valid JSON
python -c "
import json
import os
examples_dir = 'character_definition/examples'
for file in os.listdir(examples_dir):
    if file.endswith('.json'):
        with open(os.path.join(examples_dir, file), 'r') as f:
            data = json.load(f)
            print(f'{file}: {len(data.get(\"events\", []))} events')
"
```

## Implementation Status

### ✅ Completed

- Character specification model (`CharacterSpec`)
- Character registry with loading/saving
- Basic character definitions (2 test characters)
- Behavior definitions (6 behaviors)
- Behavior examples (6 example files)
- Manual setup guide

### 🔧 In Progress

- Character validation and error handling
- Behavior example validation

### 📋 TODO - High Priority

- [ ] **Character validation**: Add validation for character definitions
- [ ] **Behavior validation**: Validate behavior examples match behaviors
- [ ] **Trait extraction**: Implement automatic trait extraction from system prompts
- [ ] **Backstory generation**: Add backstory generation capabilities
- [ ] **Character templates**: Create templates for common character types
- [ ] **Import/export**: Add character import/export functionality
- [ ] **Character comparison**: Add tools to compare characters
- [ ] **Behavior analysis**: Analyze behavior coverage and gaps

### 📋 TODO - Medium Priority

- [ ] **Character versioning**: Add version control for character definitions
- [ ] **Character testing**: Add automated character testing
- [ ] **Behavior metrics**: Add metrics for behavior quality
- [ ] **Character clustering**: Group similar characters
- [ ] **Behavior recommendations**: Suggest behaviors for new characters

### 📋 TODO - Low Priority

- [ ] **Character marketplace**: Share characters between users
- [ ] **Character analytics**: Analyze character performance
- [ ] **Behavior evolution**: Track behavior changes over time
- [ ] **Character inheritance**: Create character hierarchies

## Integration Points

### With Data Generation

- Characters provide system prompts for conversation generation
- Behaviors guide conversation topics and scenarios
- Examples provide templates for synthetic data

### With Training

- Character definitions become training targets
- Behaviors define success criteria
- Examples provide training data templates

### With Evaluation

- Characters define what to evaluate
- Behaviors define evaluation criteria
- Examples provide evaluation baselines

## Quality Standards

### Character Definitions

- System prompts must be 100+ characters
- Must have at least 3 traits
- Must have at least 3 key facts
- Must have at least 2 evaluations

### Behavior Definitions

- Descriptions must be 50+ characters
- Must have 3-point rubric (1, 5, 10)
- Must specify evaluation type
- Names must be unique

### Behavior Examples

- Must have at least 2 conversation turns
- Must demonstrate target behavior
- Must be realistic and natural
- Must include both user and assistant messages

## Error Handling

### Common Issues

1. **Missing character ID**: Auto-inject from dictionary key
2. **Invalid system prompt**: Validate length and content
3. **Missing behaviors**: Check behavior references
4. **Invalid examples**: Validate example format

### Validation Rules

- Character IDs must be unique
- Behavior names must be unique
- Example files must match behavior names
- All references must be valid

## Testing

### Unit Tests Needed

- Character loading and validation
- Behavior loading and validation
- Example loading and validation
- Registry operations (add, remove, update)

### Integration Tests Needed

- Character + behavior integration
- Example + behavior integration
- Registry + file system integration

## Performance Considerations

### File I/O

- Cache character definitions in memory
- Lazy load behavior examples
- Batch file operations

### Memory Usage

- Limit number of loaded characters
- Clear unused character data
- Optimize JSON parsing

## Security Considerations

### Input Validation

- Sanitize character definitions
- Validate JSON structure
- Check file permissions

### Data Integrity

- Backup character definitions
- Validate file integrity
- Handle corruption gracefully
