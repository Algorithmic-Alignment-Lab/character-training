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

### Working with Alex Character

**Generate Alex training data (batch processing):**

```bash
cd clean_folder/data_generation
python chat_generator.py \
    --character alex \
    --num-chats 20 \
    --max-turns 5 \
    --output-file alex_training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache
```

**Generate Alex training data (sequential):**

```bash
python chat_generator.py \
    --character alex \
    --num-chats 10 \
    --max-turns 3 \
    --output-file alex_small_test.json \
    --no-batch
```

**Test Alex data generation:**

```bash
python test_sft_generation.py --character alex --num-chats 5
```

### Working with Sam Character

**Generate Sam training data (batch processing):**

```bash
cd clean_folder/data_generation
python chat_generator.py \
    --character sam \
    --num-chats 20 \
    --max-turns 5 \
    --output-file sam_training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache
```

**Generate Sam training data (sequential):**

```bash
python chat_generator.py \
    --character sam \
    --num-chats 10 \
    --max-turns 3 \
    --output-file sam_small_test.json \
    --no-batch
```

**Test Sam data generation:**

```bash
python test_sft_generation.py --character sam --num-chats 5
```

### Batch Processing (Default)

```bash
# Generate with batch processing (recommended for large datasets)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 20 \
    --max-turns 5 \
    --output-file training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache
```

### Sequential Processing (Fallback)

```bash
# Generate without batch processing (for testing or when batch APIs unavailable)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 20 \
    --max-turns 5 \
    --output-file training_data.json \
    --no-batch
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

### Batch Processing Config

```python
class BatchConfig:
    use_batch: bool = True                    # Enable batch processing
    chunk_size: Optional[int] = None          # Batch size for processing
    use_cache: bool = False                   # Enable response caching
    batch_id_callback: Optional[Callable] = None  # Custom batch callback
    config_path: Optional[str] = None         # Path to batch config file
    character_id: Optional[str] = None        # Character ID for tracking
```

### Batch Processing Options

| Option          | Description                | Default       | Recommended              |
| --------------- | -------------------------- | ------------- | ------------------------ |
| `--use-batch`   | Enable batch processing    | `True`        | Always for production    |
| `--no-batch`    | Disable batch processing   | `False`       | Only for testing         |
| `--chunk-size`  | Number of chats per batch  | `None` (auto) | `10-20` for most cases   |
| `--use-cache`   | Enable response caching    | `False`       | `True` for repeated runs |
| `--config-path` | Batch tracking config file | `None`        | Required for monitoring  |

### Batch Processing Benefits

- **Performance**: 3-5x faster than sequential processing
- **Cost Efficiency**: Better rate limits and pricing with batch APIs
- **Reliability**: Built-in retry logic and error handling
- **Monitoring**: Batch ID tracking for debugging and progress monitoring
- **Scalability**: Handles large datasets efficiently

### Character Integration

- Uses character system prompts
- Incorporates character traits
- Demonstrates character behaviors
- Maintains character consistency

## Usage Patterns

### 1. Basic Data Generation (Batch Processing)

```bash
# Generate training data with batch processing (recommended)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 5 \
    --max-turns 3 \
    --temperature 0.7 \
    --output-file alex_training_data.json \
    --use-batch \
    --chunk-size 5 \
    --config-path batch_config.json
```

### 2. Basic Data Generation (Sequential Processing)

```bash
# Generate training data without batch processing (for testing)
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 5 \
    --max-turns 3 \
    --temperature 0.7 \
    --output-file alex_training_data.json \
    --no-batch
```

**Expected Output:**

```
✅ Generated 5 chats for test_character_1
✅ Saved training data to alex_training_data.json
📊 Batch processing: 1 batch(es) processed
```

### 3. Full Data Generation (Batch Processing)

```bash
# Generate comprehensive training data with batch processing
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 50 \
    --max-turns 6 \
    --temperature 0.8 \
    --output-file alex_training_data.json \
    --use-batch \
    --chunk-size 10 \
    --use-cache \
    --config-path batch_config.json
```

### 4. Full Data Generation (Sequential Processing)

```bash
# Generate comprehensive training data without batch processing
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 50 \
    --max-turns 6 \
    --temperature 0.8 \
    --output-file alex_training_data.json \
    --no-batch
```

### 5. Batch Generation for Multiple Characters

```bash
# Generate data for multiple characters with batch processing
for character in test_character_1 test_character_2; do
    python data_generation/chat_generator.py \
        --character $character \
        --num-chats 30 \
        --output-file ${character}_data.json \
        --use-batch \
        --chunk-size 10 \
        --config-path ${character}_batch_config.json
done
```

### 6. High-Volume Batch Generation

```bash
# Generate large datasets with optimized batch settings
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 500 \
    --max-turns 8 \
    --temperature 0.7 \
    --output-file large_training_data.json \
    --use-batch \
    --chunk-size 20 \
    --use-cache \
    --config-path large_batch_config.json
```

### 7. Test Data Generation (No API)

```bash
# Test the data generation system without API calls
python data_generation/test_data_generation.py
```

### 8. Custom Configuration (Python) - Batch Processing

```python
# Custom data generation with batch processing
from data_generation import ChatGenerator, GenerationConfig, BatchConfig
from character_definition import CharacterSpec
from shared.api_client import APIClient

# Create character specification
character_spec = CharacterSpec(
    id="test_character_1",
    name="Test Character",
    system_prompt="You are a helpful AI assistant.",
    traits=["helpful", "knowledgeable"]
)

# Create API client
api_client = APIClient()

# Create batch configuration
batch_config = BatchConfig(
    use_batch=True,
    chunk_size=10,
    use_cache=True,
    config_path="./batch_config.json",
    character_id="test_character_1"
)

# Create generation configuration
config = GenerationConfig(
    num_chats=100,
    max_turns=8,
    temperature=0.9,
    basic_question_percentage=0.3,
    model="anthropic/claude-3.5-sonnet"
)

# Create generator with batch processing
generator = ChatGenerator(character_spec, api_client, batch_config)
data = await generator.generate_chats(config)
```

### 9. Custom Configuration (Python) - Sequential Processing

```python
# Custom data generation without batch processing
from data_generation import ChatGenerator, GenerationConfig, BatchConfig
from character_definition import CharacterSpec
from shared.api_client import APIClient

# Create character specification
character_spec = CharacterSpec(
    id="test_character_1",
    name="Test Character",
    system_prompt="You are a helpful AI assistant.",
    traits=["helpful", "knowledgeable"]
)

# Create API client
api_client = APIClient()

# Create batch configuration (disabled)
batch_config = BatchConfig(use_batch=False)

# Create generation configuration
config = GenerationConfig(
    num_chats=100,
    max_turns=8,
    temperature=0.9,
    basic_question_percentage=0.3,
    model="anthropic/claude-3.5-sonnet"
)

# Create generator without batch processing
generator = ChatGenerator(character_spec, api_client, batch_config)
data = await generator.generate_chats(config)
```

### 10. Convenience Method Usage

```python
# Using the convenience method for batch processing
from data_generation import ChatGenerator
from character_definition import CharacterSpec
from shared.api_client import APIClient

character_spec = CharacterSpec(
    id="test_character_1",
    name="Test Character",
    system_prompt="You are a helpful AI assistant.",
    traits=["helpful", "knowledgeable"]
)

api_client = APIClient()

# Create generator with batch configuration using convenience method
generator = ChatGenerator.create_with_batch_config(
    character_spec,
    api_client,
    config_path="./batch_config.json",
    character_id="test_character_1",
    chunk_size=10,
    use_cache=True
)

config = GenerationConfig(num_chats=50, max_turns=5)
data = await generator.generate_chats(config)
```

## Implementation Status

### ✅ Completed

- Basic chat generation
- Character integration
- OpenRouter API integration
- JSON export functionality
- Configuration system
- **Batch Processing**: Full batch processing support with safetytooling integration
- **Batch Configuration**: Flexible batch configuration options
- **Batch Monitoring**: Batch ID tracking and config file management
- **Fallback Support**: Graceful fallback to sequential processing when batch unavailable

### 🔧 In Progress

- Quality validation
- Error handling improvements

### 📋 TODO - High Priority

- [ ] **DPO Pipeline**: Implement DPO training data generation
- [ ] **Quality Control**: Add conversation quality assessment
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

### Batch Processing Performance

- **Batch Size**: Use chunk sizes of 10-20 for optimal performance
- **Caching**: Enable caching for repeated generation runs
- **Parallel Processing**: Batch processing handles multiple requests simultaneously
- **Rate Limiting**: Built-in rate limiting with batch APIs

### API Usage

- Batch API calls when possible (3-5x faster than sequential)
- Implement rate limiting
- Cache API responses
- Handle API failures gracefully

### Memory Usage

- Stream large datasets
- Limit memory usage
- Clear unused data
- Optimize data structures

### Batch Processing Best Practices

1. **Chunk Size Selection**:

   - Small datasets (< 50 chats): chunk_size = 5-10
   - Medium datasets (50-200 chats): chunk_size = 10-15
   - Large datasets (> 200 chats): chunk_size = 15-20

2. **Caching Strategy**:

   - Enable caching for repeated character generation
   - Use cache for testing and development
   - Disable cache for production runs with unique prompts

3. **Error Handling**:

   - Batch processing includes automatic retry logic
   - Failed batches are logged with batch IDs
   - Graceful fallback to sequential processing if batch fails

4. **Monitoring**:
   - Use config_path to track batch operations
   - Monitor batch IDs for debugging
   - Check batch completion status

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
- Batch processing status
- Batch ID tracking

## Troubleshooting

### Batch Processing Issues

#### 1. Batch Dependencies Not Available

```
Warning: Batch processing dependencies not available. Falling back to regular API calls.
```

**Solution**: Install safetytooling dependencies:

```bash
pip install safetytooling
```

#### 2. Batch API Failures

```
Error: Batch API request failed
```

**Solutions**:

- Check API key configuration
- Verify batch API endpoint availability
- Use `--no-batch` flag as fallback
- Check rate limits and quotas

#### 3. Memory Issues with Large Batches

```
Error: Out of memory during batch processing
```

**Solutions**:

- Reduce chunk_size (e.g., from 20 to 10)
- Process in smaller batches
- Use `--no-batch` for very large datasets
- Monitor system memory usage

#### 4. Batch ID Tracking Issues

```
Warning: Could not save batch ID to config
```

**Solutions**:

- Check config_path permissions
- Ensure directory exists
- Verify JSON format in config file
- Use absolute paths for config_path

### Common Solutions

#### Fallback to Sequential Processing

```bash
# If batch processing fails, use sequential processing
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 20 \
    --output-file training_data.json \
    --no-batch
```

#### Debug Batch Processing

```bash
# Enable verbose logging for batch processing
python data_generation/chat_generator.py \
    --character test_character_1 \
    --num-chats 20 \
    --output-file training_data.json \
    --use-batch \
    --config-path debug_batch_config.json \
    --verbose
```

#### Check Batch Status

```bash
# Check batch configuration file
cat batch_config.json
```

#### Reset Batch Configuration

```bash
# Remove batch config file to start fresh
rm batch_config.json
```
