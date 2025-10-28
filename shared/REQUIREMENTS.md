# Shared Module - Requirements

## Overview

The shared module provides common utilities, models, and configurations used across all other modules. It serves as the foundation for the entire system, providing consistent data structures, API clients, and utility functions.

## Directory Structure

```
shared/
├── api_client.py              # Unified API client for LLM providers
├── config.py                  # Global configuration and model registry
├── models.py                  # Pydantic models for data validation
├── utils.py                   # Common utility functions
└── __init__.py                # Module exports
```

## Core Components

### 1. API Client (`api_client.py`)

**Purpose**: Unified interface for making LLM API calls across different providers.

**Current Status**: ✅ Complete implementation
**API Support**: OpenRouter, Anthropic, OpenAI, vLLM, RunPod

**Key Features**:

- Multi-provider support (OpenRouter, Anthropic, OpenAI, etc.)
- SSH tunnel management for local vLLM
- LoRA adapter loading
- Structured response parsing
- Error handling and retry logic

**Usage**:

```python
from shared.api_client import APIClient

client = APIClient()
result = await client.call_llm_api(
    messages=[{"role": "user", "content": "Hello"}],
    model="openrouter/anthropic/claude-3.5-sonnet",
    temperature=0.7,
    max_tokens=100
)
```

### 2. Configuration (`config.py`)

**Purpose**: Global configuration settings and model registry.

**Current Status**: ✅ Basic implementation
**Features**:

- Model registry management
- Global retry settings
- Configuration loading

**Usage**:

```python
from shared.config import config, NUM_RETRIES

# Access global configuration
print(f"Retry count: {NUM_RETRIES}")
```

### 3. Data Models (`models.py`)

**Purpose**: Pydantic models for data validation and serialization.

**Current Status**: ✅ Complete implementation
**Models**:

- `CharacterSpec`: Character definitions
- `Chat`: Conversation data
- `TrainingData`: Training datasets
- `EvaluationResult`: Evaluation outputs
- `APICallLog`: API call logging

**Usage**:

```python
from shared.models import CharacterSpec, Chat

# Create and validate character
character = CharacterSpec(
    id="test_character",
    name="Test Character",
    version="1.0",
    system_prompt="You are a helpful assistant...",
    traits=["helpful", "honest"]
)

# Validate data
chat = Chat(
    messages=[{"role": "user", "content": "Hello"}],
    character_id="test_character"
)
```

### 4. Utilities (`utils.py`)

**Purpose**: Common utility functions for file operations and data processing.

**Current Status**: ✅ Complete implementation
**Functions**:

- `save_json()`: Save data to JSON files
- `load_json()`: Load data from JSON files
- `ensure_dir()`: Create directories
- `clean_json_string()`: Clean JSON strings

**Usage**:

```python
from shared.utils import save_json, load_json, ensure_dir

# File operations
ensure_dir("output/results")
save_json(data, "output/results/data.json")
data = load_json("output/results/data.json")
```

## API Client Features

### Provider Support

- **OpenRouter**: Access to multiple models via OpenRouter
- **Anthropic**: Direct Claude API access
- **OpenAI**: GPT models and fine-tuning
- **vLLM**: Local model serving
- **RunPod**: Cloud GPU deployment

### Advanced Features

- **SSH Tunneling**: Secure connections to local vLLM
- **LoRA Adapters**: Dynamic adapter loading
- **Structured Responses**: Pydantic model parsing
- **Caching**: Response caching for efficiency
- **Error Handling**: Comprehensive error management

### Configuration

```python
# Environment variables
OPENROUTER_API_KEY=sk-or-v1-...
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-proj-...
VLLM_BACKEND_USE_RUNPOD=false
```

## Data Models

### Character Specification

```python
class CharacterSpec(BaseModel):
    id: str
    name: str
    version: str
    system_prompt: str
    traits: List[str]
    key_facts: List[str]
    backstory: Optional[str]
    evaluations: List[str]
    evaluation_configs: Dict[str, Any]
```

### Conversation Data

```python
class Chat(BaseModel):
    messages: List[Dict[str, str]]
    character_id: str
    generation_timestamp: str
```

### Training Data

```python
class TrainingData(BaseModel):
    chats: List[Chat]
    character_id: str
    generation_config: GenerationConfig
    metadata: Dict[str, Any]
```

### Evaluation Results

```python
class EvaluationResult(BaseModel):
    character_id: str
    behavior_name: str
    scores: Dict[str, float]
    conversation: Chat
    judgment: Dict[str, Any]
    metadata: Dict[str, Any]
```

## Usage Patterns

### 1. Test API Client

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

### 2. Test Data Models

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

### 3. Test Utility Functions

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

### 4. API Client Usage (Python)

```python
# Basic API usage
from shared.api_client import APIClient

client = APIClient()
result = await client.call_llm_api(
    messages=[{"role": "user", "content": "Hello"}],
    model="openrouter/anthropic/claude-3.5-sonnet"
)

# With structured response
from shared.models import CharacterSpec
result = await client.call_llm_api_with_structured_response(
    messages=messages,
    model=model,
    response_model=CharacterSpec
)
```

### 5. Data Model Usage (Python)

```python
# Create and validate data models
from shared.models import CharacterSpec, Chat, TrainingData

# Create character
character = CharacterSpec(
    id="alex",
    name="Alex",
    version="1.0",
    system_prompt="You are Alex, a helpful assistant...",
    traits=["helpful", "honest"],
    evaluations=["alex_helpfulness", "alex_honesty"]
)

# Create training data
training_data = TrainingData(
    chats=[chat1, chat2, chat3],
    character_id="alex",
    generation_config=config
)
```

### 6. Utility Usage (Python)

```python
# File operations
from shared.utils import save_json, load_json, ensure_dir

# File operations
ensure_dir("results")
save_json({"score": 8.5}, "results/evaluation.json")
data = load_json("results/evaluation.json")
```

## Implementation Status

### ✅ Completed

- API client with multi-provider support
- SSH tunnel management
- LoRA adapter loading
- Pydantic data models
- Utility functions
- Configuration management
- Error handling
- Structured response parsing

### 🔧 In Progress

- API key validation improvements
- Error handling refinements

### 📋 TODO - High Priority

- [ ] **API Key Validation**: Improve API key validation and error handling
- [ ] **Model Registry**: Expand model registry with more providers
- [ ] **Response Caching**: Implement intelligent response caching
- [ ] **Rate Limiting**: Add rate limiting for API calls
- [ ] **Connection Pooling**: Implement connection pooling for efficiency
- [ ] **API Monitoring**: Add API usage monitoring and metrics
- [ ] **Error Recovery**: Improve error recovery mechanisms
- [ ] **Model Fallback**: Add automatic model fallback

### 📋 TODO - Medium Priority

- [ ] **API Analytics**: Track API usage and performance
- [ ] **Model Comparison**: Compare different model providers
- [ ] **Response Validation**: Validate API responses
- [ ] **Data Serialization**: Improve data serialization
- [ ] **Configuration Management**: Enhanced configuration system
- [ ] **Logging System**: Comprehensive logging system
- [ ] **Performance Optimization**: Optimize API call performance
- [ ] **Security Enhancements**: Improve security measures

### 📋 TODO - Low Priority

- [ ] **API Documentation**: Auto-generate API documentation
- [ ] **Model Testing**: Automated model testing
- [ ] **Performance Benchmarking**: Benchmark API performance
- [ ] **API Versioning**: Support API versioning
- [ ] **Model Metadata**: Rich model metadata
- [ ] **API Health Checks**: Health check endpoints
- [ ] **Model Recommendations**: Recommend models for tasks
- [ ] **API Analytics Dashboard**: Web dashboard for API analytics

## Integration Points

### With All Modules

- Provides common API client
- Supplies data models
- Offers utility functions
- Manages configuration

### With Character Definition

- Validates character data
- Provides character models
- Handles character serialization

### With Data Generation

- Makes API calls for generation
- Validates generated data
- Manages conversation models

### With Training

- Handles training API calls
- Validates training data
- Manages model configurations

### With Evaluation

- Makes evaluation API calls
- Validates evaluation results
- Manages evaluation models

## Quality Standards

### API Client

- Reliable API calls
- Proper error handling
- Efficient resource usage
- Secure connections

### Data Models

- Valid data structures
- Proper validation
- Consistent serialization
- Type safety

### Utilities

- Reliable file operations
- Proper error handling
- Efficient processing
- Clean code

## Error Handling

### Common Issues

1. **API failures**: Retry with exponential backoff
2. **Invalid data**: Validate with Pydantic models
3. **File errors**: Handle file system errors
4. **Network issues**: Handle connection problems

### Validation Rules

- API keys must be valid
- Data must match models
- Files must be accessible
- Networks must be available

## Testing

### Unit Tests Needed

- API client functionality
- Data model validation
- Utility functions
- Configuration loading

### Integration Tests Needed

- End-to-end API calls
- Data model serialization
- File operations
- Error handling

## Performance Considerations

### API Efficiency

- Batch API calls when possible
- Implement connection pooling
- Cache responses appropriately
- Optimize request/response handling

### Memory Usage

- Efficient data structures
- Proper memory management
- Lazy loading where appropriate
- Clear unused data

## Security Considerations

### API Security

- Secure API key storage
- Validate API responses
- Handle authentication errors
- Implement access controls

### Data Security

- Validate all inputs
- Sanitize data outputs
- Handle sensitive information
- Implement data encryption

## Monitoring and Logging

### Metrics to Track

- API call success rate
- API call latency
- Data validation success
- Error rates

### Logging Requirements

- API call logs
- Error conditions
- Performance metrics
- Security events
