# Character Training System - Project Overview

## Project Description

A modular, open-source system for defining AI characters, generating synthetic training data, fine-tuning models, and evaluating character alignment. The system is designed to be clean, maintainable, and ready for open-source release.

## System Architecture

```
clean_folder/
├── character_definition/     # Manual character setup and behavior definitions
├── data_generation/         # Synthetic conversation generation
├── training/               # Model fine-tuning (OpenAI, RunPod)
├── evaluation/             # Character evaluation with LLM judges
├── shared/                 # Common utilities and models
└── requirements.txt        # Python dependencies
```

## Core Workflow

1. **Manual Setup** → Define characters and behaviors
2. **Data Generation** → Create synthetic training conversations
3. **Training** → Fine-tune models with generated data
4. **Evaluation** → Assess character alignment with LLM judges

## Key Features

- **Modular Design**: Clean separation of concerns
- **Manual Character Definition**: Human-defined characters and behaviors
- **Automated Pipeline**: Automated data generation, training, and evaluation
- **LLM Evaluation**: Multi-dimensional character assessment
- **Visualization**: Charts, graphs, and comprehensive reports
- **API Fallback**: Graceful degradation when APIs fail

## Quick Start

### 1. Setup

```bash
cd clean_folder
pip install -r requirements.txt
cp ../.env .  # Copy API keys
```

### 2. Define Characters

```bash
# Edit character definitions
vim character_definition/characters.json
vim character_definition/behaviors.json
vim character_definition/examples/*.json
```

### 3. Run Evaluation

```bash
# List available characters
python evaluation/run_evaluation_with_fallback.py --list-characters

# Run evaluation (with API fallback)
python evaluation/run_evaluation_with_fallback.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
    --judge-model openrouter/anthropic/claude-3.5-sonnet \
    --character test_character_1

# Generate graphs
python evaluation/generate_graphs.py evaluation/results/*_summary_*.json
```

### 4. Run Data Generation

```bash
python data_generation/chat_generator.py --character test_character_1 --num-chats 20
```

### 5. Run Training

```bash
python training/openai_trainer.py --data-file training_data.json
```

## Current Status

### ✅ Completed

- Character definition system
- Behavior definition and examples
- LLM evaluation pipeline (with mock fallback)
- Visualization and reporting
- Modular architecture

### 🔧 In Progress

- API key validation and error handling
- Real LLM evaluation (blocked by invalid API keys)

### 📋 TODO

- Data generation pipeline completion
- Training pipeline integration
- End-to-end automation script
- Documentation and examples
- Testing and validation

## API Requirements

The system requires valid API keys for:

- **OpenRouter**: For LLM evaluation and data generation
- **Anthropic**: Alternative LLM provider
- **OpenAI**: For fine-tuning (optional)

## Development Notes

- All files load environment variables with `dotenv`
- Uses `os` imports for environment variable access
- Modular design allows independent development of each component
- Mock systems available for testing without API costs

## Contributing

Each directory contains its own requirements document with specific implementation details, TODOs, and interaction patterns.

## License

[To be determined - open source ready]
