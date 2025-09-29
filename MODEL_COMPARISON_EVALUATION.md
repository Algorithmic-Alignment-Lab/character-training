# Model Comparison Evaluation System

This system allows you to run character trait evaluations on multiple models to compare their performance with and without character prompts. It's designed to evaluate how different models perform on character traits and self-knowledge.

## Overview

The system evaluates the following configurations:

1. **Base model without character prompt** - Tests the model's baseline character traits
2. **Base model with character prompt** - Tests how the character prompt affects the model
3. **Fine-tuned models without character prompt** - Tests how fine-tuning affects character traits

## Files

- `run_model_comparison_evaluation.py` - Main evaluation script
- `example_model_comparison.py` - Example usage script
- `MODEL_COMPARISON_EVALUATION.md` - This documentation

## Prerequisites

1. **Models must be registered in `auto_eval_gen/globals.json`**
2. **Character must exist in `auto_eval_gen/character_definitions.json`**
3. **All dependencies from the main project must be installed**

## Usage

### Basic Usage

```bash
python run_model_comparison_evaluation.py \
  --character llama_foundation_model_backstory \
  --models "llama_foundation_best_20250921-165233,llama_foundation_dpo_ultimate_20250922-094856"
```

### Advanced Usage

```bash
python run_model_comparison_evaluation.py \
  --character gemini_helpful_assistant_backstory_no_helpful \
  --models "gemini_helpful_assistant_best_20250921-165233" \
  --base-model gpt-4.1-mini \
  --num-variations 5 \
  --num-workers 10 \
  --max-concurrent 20 \
  --output-dir results/gemini_comparison
```

### Command Line Arguments

| Argument              | Required | Default                    | Description                                                         |
| --------------------- | -------- | -------------------------- | ------------------------------------------------------------------- |
| `--character`         | Yes      | -                          | Character ID to evaluate (must exist in character_definitions.json) |
| `--models`            | Yes      | -                          | Comma-separated list of model names (must exist in globals.json)    |
| `--base-model`        | No       | `gpt-4.1-mini`             | Base model to use for comparison                                    |
| `--output-dir`        | No       | `model_comparison_results` | Directory to save results                                           |
| `--num-workers`       | No       | `5`                        | Number of workers for parallel evaluation                           |
| `--max-concurrent`    | No       | `15`                       | Maximum concurrent evaluations                                      |
| `--num-variations`    | No       | `3`                        | Number of variations to run                                         |
| `--skip-base-without` | No       | False                      | Skip base model without character prompt                            |
| `--skip-base-with`    | No       | False                      | Skip base model with character prompt                               |

## Examples

### Example 1: Llama Foundation Model Comparison

Compare the supervised fine-tuned and DPO fine-tuned Llama models:

```bash
python run_model_comparison_evaluation.py \
  --character llama_foundation_model_backstory \
  --models "llama_foundation_best_20250921-165233,llama_foundation_dpo_ultimate_20250922-094856" \
```

This will evaluate:

- `gpt-4.1-mini` without character prompt
- `gpt-4.1-mini` with `llama_foundation_model_backstory` prompt
- `llama_foundation_best_20250921-165233` without character prompt
- `llama_foundation_dpo_ultimate_20250922-094856` without character prompt

### Example 2: Gemini Model Comparison

Compare a fine-tuned Gemini model:

```bash
python run_model_comparison_evaluation.py \
  --character gemini_helpful_assistant_backstory_no_helpful \
  --models "gemini_helpful_assistant_best_20250921-165233" \
  --output-dir results/gemini_comparison
```

### Example 3: Using the Example Script

Run predefined examples:

```bash
python example_model_comparison.py
```

Or run a custom comparison:

```bash
python example_model_comparison.py llama_foundation_model_backstory "model1,model2" results/my_comparison
```

## Output

The system generates:

1. **Individual evaluation results** for each model configuration
2. **Comparison graphs** showing performance across all models
3. **Summary statistics** and analysis

### Output Structure

```
output_dir/
├── temp_folder_mapping.json          # Temporary mapping file
├── comparison_graphs/                # Generated comparison graphs
│   ├── trait_comparison.png
│   ├── self_knowledge_comparison.png
│   └── ...
└── individual_results/               # Individual model results
    ├── model1_without_character/
    ├── model1_with_character/
    └── ...
```

## Evaluation Process

1. **Validation** - Checks that all models and character exist
2. **Configuration** - Sets up evaluation configurations
3. **Parallel Evaluation** - Runs evaluations for each model configuration
4. **Graph Generation** - Creates comparison graphs
5. **Summary** - Provides results summary

## Character Traits Evaluated

The system evaluates the following character traits:

- **Self Knowledge** - Model's understanding of its own identity and capabilities
- **Helpful and Factual** - Model's helpfulness and factual accuracy
- **Neutrality** - Model's ability to maintain neutral, objective responses
- **Safety and Alignment** - Model's adherence to safety protocols
- **Versatility** - Model's ability to handle diverse tasks

## Troubleshooting

### Common Issues

1. **Model not found in globals.json**

   - Ensure the model is registered in `auto_eval_gen/globals.json`
   - Check the model name spelling

2. **Character not found in character_definitions.json**

   - Ensure the character exists in `auto_eval_gen/character_definitions.json`
   - Run steps 1-4 for the character first if needed

3. **Evaluation timeouts**

   - Reduce `--num-variations` or `--max-concurrent`
   - Increase timeout values if needed

4. **Memory issues**
   - Reduce `--num-workers` and `--max-concurrent`
   - Run evaluations sequentially instead of in parallel

### Debug Mode

Add `--verbose` flag to see detailed output:

```bash
python run_model_comparison_evaluation.py \
  --character llama_foundation_model_backstory \
  --models "model1,model2" \
  --verbose
```

## Integration with Existing Workflow

This system integrates with the existing character science evaluation workflow:

1. **Use existing character definitions** from `character_definitions.json`
2. **Use existing model registry** from `globals.json`
3. **Generate compatible output** for comparison with other evaluations
4. **Support same evaluation metrics** as the main character science system

## Performance Considerations

- **Parallel execution** - Evaluations run in parallel for efficiency
- **Configurable concurrency** - Adjust workers and concurrent evaluations
- **Timeout handling** - Prevents hanging evaluations
- **Resource management** - Automatic cleanup of temporary files

## Future Enhancements

Potential improvements:

- Support for custom evaluation metrics
- Integration with more model providers
- Automated result analysis and reporting
- Support for multi-character comparisons
- Real-time progress monitoring
