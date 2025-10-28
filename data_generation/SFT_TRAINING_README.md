# SFT Training Pipeline for OpenAI and Together AI

This pipeline converts generated chat data to training format and fine-tunes models on OpenAI and Together AI platforms.

## Overview

The SFT (Supervised Fine-Tuning) training pipeline consists of:

1. **Data Conversion**: Convert generated chat data to OpenAI/Together AI format
2. **Training**: Fine-tune models using the converted data
3. **Monitoring**: Track training progress and results
4. **Deployment**: Use fine-tuned models for inference

## Files

- `train_sft_models.py` - Main training script
- `test_sft_conversion.py` - Test data conversion functionality
- `sft_training_pipeline.py` - Advanced pipeline with configuration
- `SFT_TRAINING_README.md` - This documentation

## Quick Start

### 1. Prerequisites

```bash
# Install required packages
pip install openai together

# Set up API keys
export OPENAI_API_KEY="your-openai-api-key"
export TOGETHER_API_KEY="your-together-api-key"
```

### 2. Generate Training Data

First, generate SFT training data using the chat generation pipeline:

```bash
# Generate chat data (if not already done)
python test_sft_generation.py
```

This creates training data at: `./test_sft_output/test_character/synth_chats.jsonl`

### 3. Test Data Conversion

Verify that data conversion works correctly:

```bash
# Test data conversion
python test_sft_conversion.py
```

### 4. Train Models

Start the SFT training process:

```bash
# Train both OpenAI and Together AI models
python train_sft_models.py
```

## Data Format Requirements

### OpenAI Format

```json
{
  "prompt": "User question here\n\n###\n\n",
  "completion": " Assistant response here###"
}
```

**Requirements:**

- Prompt ends with `\n\n###\n\n`
- Completion starts with space and ends with `###`
- Minimum 10 characters for both prompt and completion

### Together AI Format

```json
{
  "messages": [
    { "role": "user", "content": "User question here" },
    { "role": "assistant", "content": "Assistant response here" }
  ]
}
```

**Requirements:**

- Exactly 2 messages (user + assistant)
- Valid role values: "user", "assistant"
- Minimum 10 characters for both messages

## Training Configuration

### OpenAI Training Parameters

- **Base Model**: `gpt-3.5-turbo`
- **Epochs**: 3
- **Batch Size**: 4
- **Learning Rate**: 1e-5
- **Validation Split**: 20%

### Together AI Training Parameters

- **Base Model**: `meta-llama/Llama-2-7b-hf`
- **Epochs**: 3
- **Batch Size**: 4
- **Learning Rate**: 1e-5
- **Validation Split**: 20%

## Usage Examples

### Basic Training

```python
from train_sft_models import train_openai_model, train_together_model

# Train OpenAI model
openai_model_id = await train_openai_model(
    input_data_path="./test_sft_output/test_character/synth_chats.jsonl",
    output_dir="./sft_training_output",
    api_key="your-openai-api-key"
)

# Train Together AI model
together_model_id = await train_together_model(
    input_data_path="./test_sft_output/test_character/synth_chats.jsonl",
    output_dir="./sft_training_output",
    api_key="your-together-api-key"
)
```

### Advanced Configuration

```python
from sft_training_pipeline import SFTTrainingPipeline, TrainingConfig

# Create configuration
config = TrainingConfig(
    input_data_path="./test_sft_output/test_character/synth_chats.jsonl",
    output_dir="./sft_training_output",
    openai_api_key="your-openai-api-key",
    together_api_key="your-together-api-key",
    openai_base_model="gpt-3.5-turbo",
    together_base_model="meta-llama/Llama-2-7b-hf",
    n_epochs=3,
    batch_size=4,
    learning_rate=1e-5
)

# Create and run pipeline
pipeline = SFTTrainingPipeline(config)
results = await pipeline.run_full_pipeline()
```

## Output Files

After training, you'll find:

```
sft_training_output/
├── openai_train.jsonl          # OpenAI training data
├── openai_val.jsonl            # OpenAI validation data
├── together_train.jsonl     # Together AI training data
├── together_val.jsonl          # Together AI validation data
└── training_results.json       # Training results and model IDs
```

## Training Results

The `training_results.json` file contains:

```json
{
  "openai_model_id": "ft:gpt-3.5-turbo:org:model:abc123",
  "together_model_id": "together-ai/llama-2-7b-finetuned:abc123"
}
```

## Monitoring Training

### OpenAI Training

- **Status**: Check via OpenAI dashboard or API
- **Progress**: Training typically takes 10-30 minutes
- **Cost**: ~$0.0080 per 1K tokens for gpt-3.5-turbo

### Together AI Training

- **Status**: Check via Together AI dashboard or API
- **Progress**: Training typically takes 30-60 minutes
- **Cost**: Varies by model and data size

## Troubleshooting

### Common Issues

1. **API Key Not Found**

   ```
   ⚠️  OPENAI_API_KEY not found, skipping OpenAI training
   ```

   **Solution**: Set environment variables or pass API keys directly

2. **Data Format Errors**

   ```
   ❌ Training failed: Invalid data format
   ```

   **Solution**: Run `test_sft_conversion.py` to verify data format

3. **Insufficient Data**

   ```
   ❌ Training failed: Not enough training examples
   ```

   **Solution**: Generate more training data or reduce validation split

4. **API Rate Limits**
   ```
   ❌ Training failed: Rate limit exceeded
   ```
   **Solution**: Wait and retry, or reduce batch size

### Debug Steps

1. **Test Data Conversion**:

   ```bash
   python test_sft_conversion.py
   ```

2. **Check Data Format**:

   ```bash
   head -3 sft_training_output/openai_train.jsonl
   ```

3. **Verify API Keys**:

   ```bash
   echo $OPENAI_API_KEY
   echo $TOGETHER_API_KEY
   ```

4. **Check Training Files**:
   ```bash
   ls -la sft_training_output/
   ```

## Best Practices

### Data Quality

- **Minimum Examples**: 100+ high-quality examples
- **Data Diversity**: Include various conversation types
- **Quality Control**: Review generated data before training
- **Validation Split**: Use 20% for validation

### Training Optimization

- **Epochs**: Start with 3, adjust based on performance
- **Batch Size**: Use 4 for most cases, increase for larger datasets
- **Learning Rate**: Start with 1e-5, adjust based on convergence
- **Monitoring**: Check training progress regularly

### Cost Management

- **Data Size**: Limit training data to necessary examples
- **Model Selection**: Choose appropriate base models
- **Validation**: Use validation set to avoid overfitting
- **Iteration**: Start small, scale up based on results

## Next Steps

After successful training:

1. **Test Fine-tuned Models**: Evaluate performance on test data
2. **Compare with Base Models**: Measure improvement
3. **Deploy Models**: Integrate into applications
4. **Iterate**: Refine based on performance feedback

## Support

For issues with:

- **OpenAI API**: Check [OpenAI Documentation](https://platform.openai.com/docs)
- **Together AI API**: Check [Together AI Documentation](https://docs.together.ai/)
- **Data Format**: Run `test_sft_conversion.py`
- **Training Issues**: Check API status and rate limits
