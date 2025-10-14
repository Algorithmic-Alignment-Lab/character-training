# Data Generation Module - Requirements

## Overview

The data generation module creates synthetic conversational training data based on character definitions. It generates realistic multi-turn conversations that can be used for fine-tuning AI models to exhibit specific character behaviors.

## Directory Structure

```
data_generation/
├── chat_generator.py           # Main conversation generation
├── dpo_pipeline.py            # [TODO] DPO training data generation
├── revision_engine.py         # [TODO] Conversation revision and improvement
├── prompt_templates.py        # [TODO] Prompt templates for generation
└── __init__.py                # Module exports
```

## Core Components

### 1. Chat Generator (`chat_generator.py`)

**Purpose**: Generate synthetic conversations based on character specifications.

**Current Status**: ✅ Basic implementation complete
**API Integration**: ✅ Uses OpenRouter/Anthropic Claude-3.5-Sonnet

**Key Features**:

- Character-based conversation generation
- Configurable conversation length
- Multiple conversation types (helpful, creative, etc.)
- JSON export for training

**Usage**:

```bash
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 20 \
    --max-turns 5 \
    --output-file training_data.json
```

### 2. DPO Pipeline (`dpo_pipeline.py`)

**Purpose**: Generate DPO (Direct Preference Optimization) training data.

**Current Status**: 📋 TODO - Not implemented
**Priority**: High

**Requirements**:

- Generate preference pairs (chosen vs rejected responses)
- Create preference datasets for DPO training
- Support multiple preference criteria
- Export in DPO-compatible format

### 3. Revision Engine (`revision_engine.py`)

**Purpose**: Improve and revise generated conversations.

**Current Status**: 📋 TODO - Not implemented
**Priority**: Medium

**Requirements**:

- Quality assessment of generated conversations
- Automatic conversation improvement
- Style consistency checking
- Character alignment validation

### 4. Prompt Templates (`prompt_templates.py`)

**Purpose**: Manage prompt templates for different generation scenarios.

**Current Status**: 📋 TODO - Not implemented
**Priority**: Medium

**Requirements**:

- Template management system
- Dynamic prompt generation
- Character-specific templates
- Behavior-specific templates

## Data Generation Pipeline

### 1. Input Processing

- Load character definition
- Load behavior specifications
- Load generation configuration
- Validate inputs

### 2. Conversation Generation

- Generate conversation topics
- Create multi-turn conversations
- Apply character personality
- Ensure behavior demonstration

### 3. Quality Control

- Validate conversation quality
- Check character alignment
- Verify behavior demonstration
- Filter low-quality conversations

### 4. Export

- Format for training
- Export to JSON
- Generate statistics
- Create training splits

## Configuration

### Generation Config

```python
class GenerationConfig:
    num_chats: int = 20
    max_turns: int = 5
    temperature: float = 0.7
    model: str = "openrouter/anthropic/claude-3.5-sonnet"
    basic_question_percentage: float = 0.4
```

### Character Integration

- Uses character system prompts
- Incorporates character traits
- Demonstrates character behaviors
- Maintains character consistency

## Usage Patterns

### 1. Basic Data Generation

```bash
# Generate training data for a character (minimal for testing)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 5 \
    --max-turns 3 \
    --temperature 0.7 \
    --output-file alex_training_data.json
```

**Expected Output:**

```
✅ Generated 5 chats for test_character_1
✅ Saved training data to alex_training_data.json
```

### 2. Full Data Generation

```bash
# Generate comprehensive training data
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 50 \
    --max-turns 6 \
    --temperature 0.8 \
    --output-file alex_training_data.json
```

### 3. Batch Generation

```bash
# Generate data for multiple characters
for character in test_character_1 test_character_2; do
    python data_generation/chat_generator.py \
        --character $character \
        --num-chats 30 \
        --output-file ${character}_data.json
done
```

### 4. Test Data Generation (No API)

```bash
# Test the data generation system without API calls
python data_generation/test_data_generation.py
```

### 5. Custom Configuration (Python)

```python
# Custom data generation with specific settings
from data_generation import ChatGenerator, GenerationConfig

config = GenerationConfig(
    num_chats=100,
    max_turns=8,
    temperature=0.9,
    basic_question_percentage=0.3
)

generator = ChatGenerator()
data = await generator.generate_training_data(
    character_id="test_character_1",
    config=config
)
```

## Implementation Status

### ✅ Completed

- Basic chat generation
- Character integration
- OpenRouter API integration
- JSON export functionality
- Configuration system

### 🔧 In Progress

- Quality validation
- Error handling improvements

### 📋 TODO - High Priority

- [ ] **DPO Pipeline**: Implement DPO training data generation
- [ ] **Quality Control**: Add conversation quality assessment
- [ ] **Batch Processing**: Support multiple character generation
- [ ] **Data Validation**: Validate generated conversation quality
- [ ] **Template System**: Implement prompt template management
- [ ] **Revision Engine**: Add conversation improvement capabilities
- [ ] **Statistics**: Generate data generation statistics
- [ ] **Export Formats**: Support multiple export formats (JSON, CSV, etc.)

### 📋 TODO - Medium Priority

- [ ] **Conversation Types**: Support different conversation types
- [ ] **Behavior Focus**: Generate conversations focused on specific behaviors
- [ ] **Difficulty Levels**: Generate conversations of varying difficulty
- [ ] **Multi-language**: Support multiple languages
- [ ] **Custom Prompts**: Allow custom prompt injection
- [ ] **Data Augmentation**: Augment existing conversations
- [ ] **Quality Metrics**: Implement quality scoring
- [ ] **Parallel Generation**: Support parallel conversation generation

### 📋 TODO - Low Priority

- [ ] **Conversation Analytics**: Analyze generated conversation patterns
- [ ] **A/B Testing**: Compare different generation strategies
- [ ] **Data Visualization**: Visualize generated data
- [ ] **Export to W&B**: Export to Weights & Biases
- [ ] **Data Versioning**: Version control for generated data
- [ ] **Data Caching**: Cache generated conversations
- [ ] **Data Compression**: Compress large datasets
- [ ] **Data Streaming**: Stream large datasets

## Integration Points

### With Character Definition

- Uses character system prompts
- Incorporates character traits
- Demonstrates character behaviors
- Validates character alignment

### With Training

- Exports training-ready data
- Supports multiple training formats
- Generates preference data for DPO
- Provides data statistics

### With Evaluation

- Generates evaluation baselines
- Creates test conversations
- Provides quality benchmarks
- Supports evaluation data generation

## Quality Standards

### Conversation Quality

- Natural and realistic dialogue
- Appropriate character behavior
- Clear conversation flow
- Proper turn-taking

### Character Alignment

- Consistent with character definition
- Demonstrates specified traits
- Maintains character voice
- Shows appropriate behaviors

### Data Format

- Valid JSON structure
- Proper message formatting
- Complete conversation metadata
- Training-ready format

## Error Handling

### Common Issues

1. **API failures**: Retry with exponential backoff
2. **Invalid characters**: Validate character definitions
3. **Generation failures**: Log and continue
4. **Quality issues**: Filter low-quality conversations

### Validation Rules

- Character must exist
- Configuration must be valid
- Generated conversations must be complete
- Export format must be correct

## Testing

### Unit Tests Needed

- Conversation generation
- Character integration
- Configuration validation
- Export functionality

### Integration Tests Needed

- End-to-end generation pipeline
- Character + generation integration
- API integration testing
- Export format validation

## Performance Considerations

### API Usage

- Batch API calls when possible
- Implement rate limiting
- Cache API responses
- Handle API failures gracefully

### Memory Usage

- Stream large datasets
- Limit memory usage
- Clear unused data
- Optimize data structures

## Security Considerations

### Input Validation

- Validate character definitions
- Sanitize generated content
- Check API responses
- Handle malicious inputs

### Data Privacy

- Don't log sensitive data
- Secure API keys
- Handle user data properly
- Implement data retention policies

## Monitoring and Logging

### Metrics to Track

- Generation success rate
- API call latency
- Data quality scores
- Character alignment scores

### Logging Requirements

- Generation progress
- API call results
- Quality assessments
- Error conditions
