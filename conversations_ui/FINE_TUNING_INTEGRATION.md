# Fine-tuning Integration for Conversations UI

This document explains how to use the fine-tuning integration with the conversations_ui system for testing and evaluating fine-tuned models.

## Overview

The fine-tuning integration allows you to:
1. **Generate training data** from existing conversations
2. **Create and manage fine-tuning jobs** with OpenAI and Together AI
3. **Test fine-tuned models** in the chat interface
4. **Evaluate fine-tuned models** against base models using the evaluation pipeline

## Components

### 1. Fine-tuning Manager (`fine_tuning_manager.py`)
- **FinetuningManager**: Core class for managing fine-tuning jobs
- **Database**: SQLite database for tracking jobs and metadata
- **Providers**: Support for OpenAI and Together AI fine-tuning APIs
- **Data Generation**: Convert conversations to fine-tuning format

### 2. UI Integration (`streamlit_chat.py`)
- **Fine-tuning Tab**: Complete interface for managing fine-tuning jobs
- **Model Selection**: Includes fine-tuned models in chat interface
- **Data Preparation**: Convert conversations to training data
- **Job Management**: Create, run, monitor, and delete jobs

### 3. API Integration (`llm_api.py`)
- **Model Processing**: Handle `ft:` prefixed fine-tuned models
- **Seamless Integration**: Fine-tuned models work with existing API calls

## Getting Started

### Prerequisites
- Python environment with required packages
- OpenAI API key (for OpenAI fine-tuning)
- Together AI API key (for Together AI fine-tuning)
- Existing conversation data in the database

### 1. Run the Test Suite
```bash
cd conversations_ui
python test_finetuning_integration.py
```

### 2. Start the Streamlit App
```bash
streamlit run streamlit_chat.py
```

### 3. Access Fine-tuning Interface
1. Go to the **"Evaluations"** tab
2. Select **"fine-tuning"** from the dropdown
3. Use the tabs to manage your fine-tuning workflow

## Usage Guide

### Creating Training Data

1. **Go to "Data Preparation" tab**
2. **Select a conversation database** from the dropdown
3. **Configure parameters**:
   - Output filename (e.g., `my_training_data.jsonl`)
   - Max conversations (0 = all)
   - System prompt override (optional)
4. **Preview database info** to see what data is available
5. **Generate training data** - this creates a JSONL file

**Example training data format:**
```json
{
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "How do I bake a cake?"},
        {"role": "assistant", "content": "To bake a cake, you'll need..."}
    ]
}
```

### Creating Fine-tuning Jobs

1. **Go to "Create New Job" tab**
2. **Fill in job details**:
   - Job Name: Descriptive name for your job
   - Provider: Choose OpenAI or Together AI
   - Base Model: Select from available models
   - Training Data File: Path to your JSONL file
   - Hyperparameters: Epochs, batch size, learning rate, etc.
3. **Create the job** - it will be saved with "pending" status

### Running Fine-tuning Jobs

1. **Go to "Job Management" tab**
2. **Select a pending job**
3. **Click "Run Job"** - this will:
   - Submit the job to the provider's API
   - Monitor the training process
   - Update the job status and store the fine-tuned model name

### Testing Fine-tuned Models

1. **After job completion**, click "Test Fine-tuned Model"
2. **Switch to "Chat Interface" tab**
3. **The fine-tuned model will be selected** in the model dropdown
4. **Start chatting** to test the model's behavior

## Model Selection

Fine-tuned models appear in the model dropdown with the `ft:` prefix:
- **Base models**: `anthropic/claude-sonnet-4-20250514`
- **Fine-tuned models**: `ft:gpt-3.5-turbo:my-org:custom-model`

The system automatically handles the `ft:` prefix when making API calls.

## Evaluation Pipeline Integration

Fine-tuned models work seamlessly with the existing evaluation pipeline:

### 1. Generate Conversations with Fine-tuned Models
```bash
python generate_conversations.py \
    --ideas-file ideas_with_contexts.json \
    --model "ft:gpt-3.5-turbo:my-org:custom-model" \
    --system-prompt "Your system prompt..." \
    --user-message-template "Template with {idea} and {context_1}"
```

### 2. Run Evaluations
```bash
python judge_conversations.py \
    --evaluation-type single \
    --judge-model anthropic/claude-sonnet-4-20250514 \
    --filepaths fine_tuned_model_results.db \
    --traits consistency helpfulness authenticity
```

### 3. Compare Models
```bash
python judge_conversations.py \
    --evaluation-type elo \
    --judge-model anthropic/claude-sonnet-4-20250514 \
    --filepaths base_model_results.db fine_tuned_model_results.db \
    --traits consistency helpfulness authenticity
```

## Best Practices

### Training Data Quality
- **Use high-quality conversations** that demonstrate desired behavior
- **Include diverse examples** to improve generalization
- **Start with 50-100 examples** for initial testing
- **Use system prompt override** to standardize behavior

### Fine-tuning Parameters
- **OpenAI**: Use `auto` for batch size and learning rate initially
- **Together AI**: Start with smaller learning rates (1e-5) and moderate batch sizes (4-8)
- **Epochs**: Start with 1-3 epochs to avoid overfitting

### Evaluation Strategy
1. **Baseline comparison**: Compare against base model
2. **Multi-trait evaluation**: Test multiple character traits
3. **ELO ranking**: Use comparative evaluation for nuanced differences
4. **Iterative improvement**: Use evaluation results to refine training data

## Troubleshooting

### Common Issues

1. **"Fine-tuning manager not available"**
   - Ensure `fine_tuning_manager.py` is in the correct directory
   - Check that safety-tooling dependencies are installed

2. **"Error creating job"**
   - Verify API keys are set correctly
   - Check that training data file exists and is valid JSONL
   - Ensure model name is supported by the provider

3. **"Model not found in API call"**
   - Verify the fine-tuned model name is correct
   - Check that the fine-tuning job completed successfully
   - Ensure API keys have access to the fine-tuned model

### Debug Steps

1. **Run the test suite**: `python test_finetuning_integration.py`
2. **Check logs**: Look for error messages in the Streamlit app
3. **Verify API access**: Test with base models first
4. **Check file permissions**: Ensure training data files are readable

## File Structure

```
conversations_ui/
├── fine_tuning_manager.py          # Core fine-tuning management
├── streamlit_chat.py               # UI with fine-tuning interface
├── llm_api.py                      # API integration with ft: support
├── test_finetuning_integration.py  # Test suite
├── generate_conversations.py       # Supports fine-tuned models
├── judge_conversations.py          # Evaluation pipeline
├── fine_tuning_jobs.db            # Job tracking database
└── *.jsonl                        # Training data files
```

## API Keys Setup

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export TOGETHER_API_KEY="your-together-key"
```

Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your-openai-key
TOGETHER_API_KEY=your-together-key
```

## Next Steps

1. **Run the test suite** to verify integration
2. **Create training data** from your best conversations
3. **Start with small jobs** to test the workflow
4. **Use evaluation pipeline** to measure improvements
5. **Iterate based on results** to improve model performance

For more detailed information about the evaluation pipeline, see `CLAUDE.md` in the conversations_ui directory.