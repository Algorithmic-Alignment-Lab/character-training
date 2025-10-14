# Character Training System

A modular, open-source system for defining AI characters, generating synthetic training data, fine-tuning models, and evaluating character alignment.

## 🚀 Quick Start

### 1. Setup

```bash
cd clean_folder
pip install -r requirements.txt
cp ../.env .  # Copy API keys

# Test API keys
python test_api_keys.py --all --sync
```

### 2. Define Characters

Edit the character definition files using any text editor:

**Edit `character_definition/characters.json`:**

- Add your character with a unique ID
- Include name, system prompt, traits, and evaluations
- See existing examples for format

**Edit `character_definition/behaviors.json`:**

- Add behavior descriptions for each evaluation
- Include evaluation type and scoring rubric
- Follow the existing format

**Edit `character_definition/examples/*.json`:**

- Create example conversations for each behavior
- Include realistic multi-turn conversations
- Show both good and poor examples

### 3. Run Evaluation

```bash
# List available characters
python evaluation/run_parallel_evaluation.py --list-characters

# Run evaluation (uses auto_eval_gen system)
python evaluation/run_parallel_evaluation.py \
    --teacher-model openrouter/anthropic/claude-3.5-sonnet \
    --student-model openrouter/anthropic/claude-3.5-sonnet \
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

## 📁 Project Structure

```
clean_folder/
├── character_definition/     # Manual character setup and behavior definitions
│   ├── characters.json       # Character definitions
│   ├── behaviors.json        # Behavior descriptions
│   ├── examples/             # Behavior examples
│   └── REQUIREMENTS.md       # Character definition requirements
├── data_generation/         # Synthetic conversation generation
│   ├── chat_generator.py    # Main conversation generator
│   └── REQUIREMENTS.md      # Data generation requirements
├── training/               # Model fine-tuning (OpenAI, RunPod)
│   ├── openai_trainer.py   # OpenAI fine-tuning
│   └── REQUIREMENTS.md     # Training requirements
├── evaluation/             # Character evaluation with LLM judges
│   ├── llm_evaluation.py   # Real LLM evaluation
│   ├── run_character_evaluation.py # Main evaluation script
│   ├── generate_graphs.py  # Visualization
│   └── REQUIREMENTS.md     # Evaluation requirements
├── shared/                 # Common utilities and models
│   ├── api_client.py       # Unified API client
│   ├── models.py           # Pydantic data models
│   ├── utils.py            # Utility functions
│   └── REQUIREMENTS.md     # Shared module requirements
├── PROJECT_OVERVIEW.md     # Project overview and architecture
└── requirements.txt        # Python dependencies
```

## 🎯 Core Workflow

1. **Manual Setup** → Define characters and behaviors in `character_definition/`
2. **Data Generation** → Create synthetic training conversations
3. **Training** → Fine-tune models with generated data
4. **Evaluation** → Assess character alignment with LLM judges

## ✨ Key Features

- **Modular Design**: Clean separation of concerns
- **Manual Character Definition**: Human-defined characters and behaviors
- **Automated Pipeline**: Automated data generation, training, and evaluation
- **LLM Evaluation**: Multi-dimensional character assessment
- **Visualization**: Charts, graphs, and comprehensive reports
- **Robust Evaluation**: Comprehensive LLM-based character assessment

## 📊 Current Status

### ✅ Completed

- Character definition system
- Behavior definition and examples
- LLM evaluation pipeline
- Visualization and reporting
- Modular architecture

### 🔧 In Progress

- API key validation and error handling
- Real LLM evaluation integration

### 📋 TODO

- Data generation pipeline completion
- Training pipeline integration
- End-to-end automation script
- Documentation and examples
- Testing and validation

## 🔑 API Requirements

The system requires valid API keys for:

- **OpenRouter**: For LLM evaluation and data generation
- **Anthropic**: Alternative LLM provider
- **OpenAI**: For fine-tuning (optional)

## 📚 Documentation

Each module contains detailed requirements documents:

- [Project Overview](PROJECT_OVERVIEW.md)
- [Character Definition Requirements](character_definition/REQUIREMENTS.md)
- [Data Generation Requirements](data_generation/REQUIREMENTS.md)
- [Training Requirements](training/REQUIREMENTS.md)
- [Evaluation Requirements](evaluation/REQUIREMENTS.md)
- [Shared Module Requirements](shared/REQUIREMENTS.md)

## 🧪 Testing

### API Key Testing

```bash
# Test all API providers
python test_api_keys.py --all --sync

# Test specific provider
python test_api_keys.py --provider openrouter --sync
```

### Test Characters

Two test characters are included for immediate testing:

- **Alex**: Helpful assistant (self-knowledge, helpfulness, honesty)
- **Sam**: Creative storyteller (self-knowledge, creativity, enthusiasm)

## 🔧 Development

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env .

# Test the system
python evaluation/run_parallel_evaluation.py --list-characters
```

### Adding New Characters

1. Edit `character_definition/characters.json`
2. Add behaviors to `character_definition/behaviors.json`
3. Create examples in `character_definition/examples/`
4. Test with evaluation system

## 📈 Results

The system generates comprehensive evaluation results:

- **Behavior Scores**: Individual behavior performance
- **Overall Scores**: Character-wide performance metrics
- **Visualizations**: Professional charts and graphs
- **Reports**: Detailed text summaries
- **JSON Export**: Complete evaluation data

## 🤝 Contributing

Each directory contains its own requirements document with specific implementation details, TODOs, and interaction patterns. Please refer to the individual module requirements for contribution guidelines.

## 📄 License

[To be determined - open source ready]

## 🆘 Support

For issues and questions:

1. Check the module-specific requirements documents
2. Review the project overview
3. Test with the included test characters first
4. Ensure API keys are valid for real evaluation
