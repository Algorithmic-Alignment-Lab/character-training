# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a character training and AI safety research repository containing multiple interconnected projects:

- **safety-tooling/**: Core LLM inference library with unified API for OpenAI, Anthropic, and Google models
- **conversations_ui/**: Character trait evaluation pipeline with Streamlit UI
- **fine-tuning/**: Fine-tuning experiments and utilities
- **evals/**: Evaluation scripts and long-context testing
- **character-science/**: Utilities for character consistency research

## Common Commands

### Safety Tooling Development

```bash
# Setup development environment (from safety-tooling/)
uv venv --python=python3.11
source .venv/bin/activate
uv pip install -e .
uv pip install -r requirements_dev.txt

# Run tests
python -m pytest -v -s -n 6

# Run comprehensive tests (including slow batch API tests)
SAFETYTOOLING_SLOW_TESTS=True python -m pytest -v -s -n 6

# Install pre-commit hooks
make hooks

# Check for outdated dependencies
uv pip list --outdated
```

### Character Evaluation Pipeline

```bash
# Run complete evaluation pipeline (from conversations_ui/)
./run_evaluation_pipeline.sh --system-prompt "Your prompt" --total-ideas 10

# Run individual components
python3 generate_ideas.py --system-prompt "..." --batch-size 3 --total-ideas 10
python3 generate_context.py --ideas-file ideas.json --pages 2
python3 generate_conversations.py --ideas-file contexts.json --model claude-4-20241022 --num-conversations 5 --num-turns 3
python3 judge_conversations.py --evaluation-type single --filepaths conversation.db

# Launch Streamlit UI
streamlit run streamlit_chat.py

# Run tests
pytest test_evaluation_pipeline.py -v
pytest test_integration.py -v

# Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
```

### Fine-tuning

```bash
# Fine-tune with safety-tooling (from safety-tooling/)
python -m safetytooling.apis.finetuning.openai.run --model gpt-3.5-turbo-1106 --train_file data.jsonl --n_epochs 1

# Check OpenAI usage
python -m safetytooling.apis.inference.usage.usage_openai

# Check Anthropic usage
python -m safetytooling.apis.inference.usage.usage_anthropic
```

## Architecture Overview

### Safety Tooling Core

- **InferenceAPI** (`safetytooling/apis/inference/api.py`): Main unified interface for all LLM providers
- **Data Models** (`safetytooling/data_models/`): Pydantic models for prompts, messages, and responses
- **Caching System**: File-based or Redis caching with automatic rate limiting
- **Provider Support**: OpenAI, Anthropic, Google Gemini, HuggingFace, Together, OpenRouter

Key usage pattern:

```python
from safetytooling.apis import InferenceAPI
from safetytooling.data_models import ChatMessage, MessageRole, Prompt
from safetytooling.utils import utils

utils.setup_environment()  # Loads API keys from .env
API = InferenceAPI(cache_dir=Path(".cache"))
prompt = Prompt(messages=[ChatMessage(content="Hello", role=MessageRole.user)])
response = await API(model_id="gpt-4o-mini", prompt=prompt)
```

### Character Evaluation Pipeline

1. **Idea Generation** (`generate_ideas.py`): Creates test scenarios using iterative generation and filtering
2. **Context Generation** (`generate_context.py`): Builds realistic document contexts around ideas
3. **Conversation Generation** (`generate_conversations.py`): Generates AI responses using various models/prompts
4. **Judgment System** (`judge_conversations.py`): Evaluates consistency using single scoring or ELO comparison
5. **UI Dashboard** (`streamlit_chat.py`): Three-tab interface for chat, analysis, and evaluation results

Data flow: `System Prompt → ideas.json → ideas_with_contexts.json → conversations.db → evaluation_results/`

### Database Schema

- SQLite databases for conversations and evaluation results
- Pydantic models for all data structures
- Foreign key relationships maintained between ideas, contexts, conversations, and judgments

## Key Configuration Files

### Environment Setup

- `.env` file for API keys (in safety-tooling/)
- `system_prompts.json` for persona definitions (in conversations_ui/)
- `requirements.txt` for Python dependencies per module

### API Keys Required

```
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GOOGLE_API_KEY=...
HF_TOKEN=...
TOGETHER_API_KEY=...
```

### Testing Configuration

- `pyproject.toml`: pytest configuration with asyncio support
- `.flake8`: Code linting configuration (max-line-length=88)
- Pre-commit hooks available via `make hooks`

## Development Guidelines

### Safety Tooling

- Always preserve backward compatibility (used as submodule by many projects)
- Respect caching mechanisms - never bypass without explicit user request
- Use async/await patterns throughout
- Follow existing patterns for adding new model support
- Test with multiple providers when modifying core functionality

### Character Evaluation

- Use the complete pipeline script for most evaluations
- Generate 3-10 ideas per batch, configurable total ideas
- Support 1-3 page context documents
- Both single evaluation and ELO comparison modes available
- All evaluation data timestamped and organized in `evaluation_data/`

### File Organization

- Each major component in its own directory with README
- Shared utilities in appropriate `utils/` directories
- Examples and notebooks in `examples/` subdirectories
- Test files prefixed with `test_`

## Important Notes

- The safety-tooling module is designed to be used as a git submodule across projects
- Caching is critical for API cost management - all inference calls are cached by default
- Rate limiting is built-in and configured per provider
- All major components have comprehensive test suites
- The Streamlit UI provides visualization for all evaluation results
- Pipeline outputs are self-contained with configuration metadata

## Common Troubleshooting

- **API key issues**: Ensure `.env` exists and `utils.setup_environment()` is called
- **Cache misses**: Check `cache_dir` path and `NO_CACHE` environment variable
- **Rate limits**: Adjust `openai_fraction_rate_limit` and provider-specific `num_threads`
- **Import errors**: Install packages with `uv pip install -e .` for editable installs
- **Test failures**: Use `SAFETYTOOLING_SLOW_TESTS=True` for complete test suite
