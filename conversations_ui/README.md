# Collaborative AI Fine-Tuning Pipeline

A comprehensive system for generating synthetic training data and fine-tuning AI models with collaborative traits.

## 🎯 Overview

This pipeline generates high-quality training data for collaborative AI systems using a multi-stage synthetic generation process. It creates realistic professional documents and collaborative responses that demonstrate partnership framing, curiosity, ethical consideration, encouragement, and thoroughness.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE OVERVIEW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Document Generation → Collaborative Responses → Fine-Tuning   │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │  Generate   │    │  Generate   │    │  Create     │        │
│  │  Detailed   │ -> │  Collaborative│ -> │  Training   │        │
│  │  Documents  │    │  Responses  │    │  Data       │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
conversations_ui/
├── 📋 Core Scripts
│   ├── generate_finetuning_data.py      # Main data generation pipeline
│   ├── together_ai_finetuning.py        # Training job management
│   ├── elo_comparison.py                # Model evaluation
│   └── simple_dashboard.py              # Training monitoring
│
├── 🔧 Support Scripts
│   ├── llm_api.py                       # API abstraction layer
│   ├── generate_full_documents.py       # Document generation utility
│   ├── background_monitor.py            # Automated monitoring
│   └── fine_tuning_manager.py           # Training orchestration
│
├── 📊 Data Files
│   ├── *_training_data.jsonl            # Training data (JSONL format)
│   ├── *_detailed.json                  # Detailed data with metadata
│   ├── *_metadata.json                  # Generation statistics
│   └── fine_tuning_job_info.json        # Current job information
│
├── 📈 Results
│   ├── elo_comparison_*.json             # Evaluation results
│   ├── fine_tuning_monitor.log          # Training logs
│   └── monitor_output.log               # Monitoring output
│
└── 📚 Documentation
    ├── README.md                        # This file
    ├── FINE_TUNING_PIPELINE.md          # Detailed pipeline docs
    ├── QUICK_REFERENCE.md               # Command reference
    └── FINE_TUNING_MODELS.md            # Model registry
```

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export TOGETHER_API_KEY="your_together_ai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
export OPENROUTER_API_KEY="your_openrouter_key"
```

### 2. Generate Training Data

```bash
# Generate 50 document-based training examples
python generate_finetuning_data.py \
  --system-prompt "Your collaborative AI system prompt" \
  --examples 50 \
  --output my_training_data.jsonl
```

### 3. Start Fine-Tuning

```bash
# Create fine-tuning job
python together_ai_finetuning.py \
  --data-file my_training_data.jsonl \
  --suffix collaborative_v1 \
  --model meta-llama/Meta-Llama-3.1-8B-Instruct-Reference
```

### 4. Monitor Training

```bash
# Real-time dashboard
python simple_dashboard.py

# Background monitoring
python background_monitor.py &
```

### 5. Evaluate Model

```bash
# Compare fine-tuned vs base model
python elo_comparison.py

# Analyze results
python analysis_results.py
```

## 🔍 Key Features

### 📝 Document-Based Training Data
- **Realistic Scenarios**: Professional memos, emails, reports, proposals
- **Complex Contexts**: Multi-stakeholder business challenges
- **Ethical Dilemmas**: Scenarios that test collaborative reasoning
- **Word Count**: 500-1000 words per document (vs. simple Q&A)

### 🔄 API Fallback System
- **Primary**: Claude API (Anthropic direct)
- **Fallback 1**: OpenRouter Claude 3.5 Sonnet
- **Fallback 2**: OpenRouter Claude 3.5 Haiku
- **Fallback 3**: OpenRouter Gemini Pro
- **Automatic**: Seamless switching when APIs fail

### 🎯 Collaborative Traits Training
- **Collaborative**: Partnership framing, clarifying questions
- **Inquisitive**: Genuine curiosity, exploration encouragement
- **Cautious & Ethical**: Multiple perspectives, ethical consideration
- **Encouraging**: Warm tone, safe environment creation
- **Thorough**: Detailed, contextualized responses

### 📊 Comprehensive Evaluation
- **ELO Rating System**: Comparative model performance
- **Trait-Based Scoring**: 5-dimensional collaborative assessment
- **Performance Metrics**: Response quality, engagement measures
- **Automated Analysis**: Detailed performance reports

## 📋 Command Reference

### Generate Training Data
```bash
# Basic usage
python generate_finetuning_data.py \
  --system-prompt "$(cat system_prompt.txt)" \
  --examples 25 \
  --output training_data.jsonl

# Check output files
ls -la training_data*
```

### Fine-Tuning Management
```bash
# Start training
python together_ai_finetuning.py \
  --data-file training_data.jsonl \
  --suffix my_model_v1

# Check status
python simple_dashboard.py

# Background monitoring
python background_monitor.py &
```

### Model Evaluation
```bash
# ELO comparison
python elo_comparison.py

# Results analysis
python analysis_results.py

# View results
cat elo_comparison_*.json | jq '.elo_analysis'
```

## 📊 Data Formats

### Training Data (JSONL)
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are an AI assistant that embodies these core traits:\n\n**Collaborative**: You frame interactions as partnerships..."
    },
    {
      "role": "user",
      "content": "**Internal Memo - AI Training Methodology Dispute**\n\nINTEROFFICE MEMORANDUM\nTo: AI Development Team..."
    },
    {
      "role": "assistant",
      "content": "What a fascinating and complex challenge! I find myself deeply intrigued by this tension between efficiency and meaningful engagement..."
    }
  ]
}
```

### Metadata Format
```json
{
  "document_id": "bb576485-e27a-409b-89db-50a1b8e2bc1d",
  "document_title": "Internal Memo - AI Training Methodology Dispute",
  "document_word_count": 542,
  "created_at": "2025-07-15T15:45:29.438164"
}
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
TOGETHER_API_KEY=your_together_ai_key
ANTHROPIC_API_KEY=your_anthropic_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional
LITELLM_LOG_LEVEL=INFO
```

### Training Parameters
```python
# Fine-tuning configuration
METHOD = "LoRA"              # Low-Rank Adaptation
EPOCHS = 3                   # Training epochs
LEARNING_RATE = 1e-5         # Learning rate
BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct-Reference"
BATCH_SIZE = "auto"          # Optimized by Together AI
```

## 📈 Performance Metrics

### Current Model Performance
- **Model 1** (ft-b3cb7680-14cb): ELO 1454.2 (baseline)
- **Model 2** (ft-1c4a6da3-532e): Improved collaborative traits

### Evaluation Dimensions
- **Collaborative Framing**: Partnership approach vs. direct answers
- **Inquisitive Engagement**: Curiosity demonstration and exploration
- **Ethical Consideration**: Multi-perspective analysis
- **Encouraging Tone**: Supportive, warm interaction style
- **Thorough Analysis**: Detailed, contextualized responses

## 🛠️ Troubleshooting

### Common Issues

**API Timeouts**
```bash
# Check API status
python -c "from llm_api import call_llm_api; import asyncio; print('API Working')"

# Solution: Fallback system handles automatically
```

**Training Failures**
```bash
# Check job status
python simple_dashboard.py

# Validate training data
python -c "import json; [json.loads(line) for line in open('training_data.jsonl')]"
```

**Model Access Issues**
```bash
# Verify model deployment
cat fine_tuning_job_info.json | jq '.fine_tuned_model'
```

### Debug Commands
```bash
# Check environment
env | grep -E "(TOGETHER|ANTHROPIC|OPENROUTER)"

# Test API connectivity
python -c "import together; print('Together AI:', together.Together().models.list()[:1])"

# Validate data format
head -1 training_data.jsonl | jq .
```

## 📚 Documentation

- **[FINE_TUNING_PIPELINE.md](FINE_TUNING_PIPELINE.md)**: Detailed technical documentation
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**: Command and path reference
- **[FINE_TUNING_MODELS.md](FINE_TUNING_MODELS.md)**: Model registry and access
- **[PIPELINE_SUMMARY.md](PIPELINE_SUMMARY.md)**: Implementation summary

## 🔮 Future Enhancements

### Planned Features
- **Automated Pipeline**: End-to-end automation
- **Advanced Evaluation**: More sophisticated metrics
- **Multi-Model Support**: Additional base models
- **Web Dashboard**: Real-time monitoring interface
- **A/B Testing**: Automated comparison testing

### Scalability Improvements
- **Distributed Generation**: Parallel processing
- **Cloud Integration**: AWS/GCP deployment
- **Caching Layer**: Redis for performance
- **Database Optimization**: PostgreSQL scaling

## 🤝 Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd lab-character-training/conversations_ui

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Code Style
```bash
# Format code
black *.py

# Check linting
flake8 *.py

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🆘 Support

For issues and questions:
- Check the troubleshooting section above
- Review the detailed documentation
- Open an issue in the repository
- Check training logs for error details

---

*Last Updated: July 15, 2025*  
*Pipeline Version: 1.0*  
*Documentation Version: 1.0*