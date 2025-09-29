# Project Structure

This document provides a comprehensive overview of the algorithmic alignment lab character training repository structure.

## Directory Structure

```
lab-character-training/
├── safety-tooling/              # Core LLM inference library
│   ├── apis/                    # API integrations (OpenAI, Anthropic, Google)
│   ├── data_models/             # Pydantic models for prompts and responses
│   └── utils/                   # Shared utilities and environment setup
├── evals/                       # Evaluation scripts and testing frameworks
│   ├── finetuning/             # Fine-tuning experiments and data generation
│   ├── webapp/                 # Web-based evaluation interfaces
│   └── synthetic_evaluation_data/ # Generated test data
├── character-science/           # Character consistency research utilities
├── auto_eval_gen/              # Automated evaluation generation system
├── character_science_results/   # Research outputs and analysis results
├── conversations_ui/           # Character evaluation pipeline (not visible in current structure)
├── configs/                    # Configuration files for various experiments
├── chat_transcripts/           # Historical conversation data
├── evaluation_graphs/          # Visualization outputs
├── full_automation/            # End-to-end automation scripts
└── docs/                       # Project documentation (this directory)
```

## Core Components

### 1. Safety Tooling (`safety-tooling/`)
- **Purpose**: Unified LLM inference library
- **Key Features**: Multi-provider API support, caching, rate limiting
- **Main Entry Points**: `InferenceAPI`, data models
- **Dependencies**: Used as submodule across multiple projects

### 2. Evaluation System (`evals/`)
- **Purpose**: Comprehensive testing and evaluation framework
- **Components**:
  - Fine-tuning data generation
  - Synthetic evaluation data creation
  - Web-based evaluation interfaces
  - Long-context testing utilities

### 3. Character Science (`character-science/`, `auto_eval_gen/`)
- **Purpose**: Research tools for character consistency analysis
- **Output**: Results stored in `character_science_results/`
- **Integration**: Works with evaluation pipeline for automated analysis

### 4. Configuration Management (`configs/`)
- **Purpose**: Centralized configuration for experiments
- **Structure**: Organized by experiment type and model configuration
- **Usage**: Referenced by automation scripts and evaluation pipelines

## Data Flow Architecture

```
System Prompts → Idea Generation → Context Generation →
Conversation Generation → Judgment/Evaluation → Results Analysis
```

### Key Data Artifacts
- **Input**: System prompts, configuration files
- **Intermediate**: `ideas.json`, `ideas_with_contexts.json`, `conversations.db`
- **Output**: Evaluation results, analysis graphs, research reports

## Development Patterns

### Module Structure
Each major component follows this pattern:
```
component/
├── README.md                   # Component-specific documentation
├── requirements.txt            # Python dependencies
├── utils/                      # Component utilities
├── tests/                      # Test files (test_*.py)
└── examples/                   # Usage examples
```

### Database Schema
- **Primary Storage**: SQLite databases for conversations and evaluations
- **Models**: Pydantic models ensure type safety and validation
- **Relationships**: Foreign key constraints maintain data integrity

## Integration Points

### API Keys and Environment
- Location: `.env` in safety-tooling/
- Required: OpenAI, Anthropic, Google, HuggingFace, Together APIs
- Setup: `utils.setup_environment()` loads configuration

### Caching Strategy
- **Location**: `.cache/` directory
- **Purpose**: API cost management and performance optimization
- **Configuration**: Configurable cache directories per component

### Testing Infrastructure
- **Framework**: pytest with asyncio support
- **Configuration**: `pyproject.toml`, `.flake8`
- **Coverage**: Unit tests, integration tests, slow batch API tests
- **Hooks**: Pre-commit hooks available via `make hooks`

## Deployment and Operations

### Development Setup
1. Clone repository with submodules
2. Set up virtual environment (`uv venv --python=python3.11`)
3. Install dependencies (`uv pip install -e .`)
4. Configure environment variables
5. Run tests to verify setup

### Production Considerations
- **Caching**: Critical for cost management
- **Rate Limiting**: Built-in per provider
- **Monitoring**: Usage tracking available for major providers
- **Scaling**: Configurable thread counts and batch sizes

## Documentation Standards

### File Naming Conventions
- **Features**: `FEATURE_[NAME].md`
- **Components**: `[COMPONENT]_README.md`
- **Processes**: `[PROCESS]_GUIDE.md`

### Content Structure
- Clear problem statements
- Technical specifications
- Usage examples
- Integration guidance
- Troubleshooting information

## Future Architecture Considerations

### Scalability
- Modular design supports independent scaling
- Caching reduces API dependency
- Async patterns enable high concurrency

### Extensibility
- Plugin architecture for new model providers
- Configurable evaluation metrics
- Flexible data pipeline components

### Maintainability
- Comprehensive test coverage
- Clear separation of concerns
- Standardized configuration management
- Backward compatibility guarantees for safety-tooling