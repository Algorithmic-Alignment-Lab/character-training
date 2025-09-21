# DPO Fine-tuning Guide: From Data Generation to Model Deployment

This guide walks you through the complete pipeline for DPO (Direct Preference Optimization) fine-tuning, including data generation, supervised fine-tuning, and DPO fine-tuning on top of existing models.

## Overview

The pipeline consists of three main steps:

1. **Generate DPO Data**: Create preferred/rejected chat pairs using the merged revision-DPO pipeline
2. **Supervised Fine-tuning**: Fine-tune on preferred responses to create a base model
3. **DPO Fine-tuning**: Apply DPO on top of the supervised fine-tuned model

## Prerequisites

- OpenAI API key set as environment variable: `export OPENAI_API_KEY='your-key-here'`
- Matched datasets with exactly the same number of examples
- Python environment with required packages

## Step 1: Generate DPO Data

### 1.1 Generate Synthetic Chats with DPO Pipeline

```bash
# Generate 2000 chats with merged revision-DPO pipeline
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_2000_dpo \
  --total_chats_target=2000 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514 \
  --enable_dpo=True \
  --dpo_model=claude-sonnet-4-20250514 \
  --dpo_max_chats=2000 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022
```

This creates:

- `synth_chats_original.jsonl` - Original generated chats
- `synth_chats_preferred.jsonl` - Preferred responses (judged better)
- `synth_chats_rejected.jsonl` - Rejected responses (judged worse)

### 1.2 Create Matched Datasets

```bash
# Create exact matching datasets (all three will have the same number of examples)
python evals/finetuning/filter_exact_matches.py \
  --original_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_original.jsonl \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_preferred.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_rejected.jsonl \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets
```

This creates:

- `synth_chats_original_matched.jsonl` - Original chats (filtered to match)
- `synth_chats_preferred_matched.jsonl` - Preferred responses (filtered to match)
- `synth_chats_rejected_matched.jsonl` - Rejected responses (filtered to match)

## Step 2: Supervised Fine-tuning on Preferred Responses

### 2.1 Prepare Training Data

```bash
# Prepare OpenAI training data from preferred chats
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --output-dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred \
  --sample-size 1419 \
  --val-size 100 \
  --format messages
```

### 2.2 Run Supervised Fine-tuning

```bash
# Supervised fine-tuning on preferred responses (with automatic monitoring)
python evals/finetuning/run_openai_finetuning.py main \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --method supervised \
  --suffix "llama_foundation_preferred_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Note**: The `--monitor True` flag (default) will automatically monitor the job until completion and return the fine-tuned model ID.

## Step 3: DPO Fine-tuning on Top of Supervised Model

### 3.1 Create DPO Training Dataset

```bash
# Convert preferred/rejected chats to DPO format
python evals/finetuning/create_dpo_dataset.py \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --output_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data/train.jsonl \
  --max_examples 1419
```

### 3.2 Run DPO Fine-tuning on Supervised Model

```bash
# DPO fine-tuning on top of supervised fine-tuned model
# Replace SUPERVISED_MODEL_ID with the actual model ID from step 2.2
python evals/finetuning/dpo_finetuning.py run_pipeline \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --base_model SUPERVISED_MODEL_ID \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results \
  --max_examples 1419 \
  --suffix "llama_foundation_supervised_then_dpo_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

## Alternative: Direct DPO Fine-tuning (Without Supervised Step)

If you want to skip the supervised fine-tuning step and go directly to DPO:

```bash
# Direct DPO fine-tuning from base model
python evals/finetuning/dpo_finetuning.py run_pipeline \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --base_model gpt-4.1-mini-2025-04-14 \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results \
  --max_examples 1419 \
  --suffix "llama_foundation_direct_dpo_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

## Monitoring and Management

### Monitor Existing Jobs

```bash
# Monitor a specific fine-tuning job
python evals/finetuning/run_openai_finetuning.py monitor --job_id YOUR_JOB_ID

# Monitor a DPO fine-tuning job
python evals/finetuning/dpo_finetuning.py monitor --job_id YOUR_JOB_ID
```

### Check Job Status

You can also check job status at: https://platform.openai.com/finetune

## Testing with Small Datasets

### Test DPO Pipeline with 100 Examples

```bash
# Test DPO fine-tuning with 100 examples (dry run - no API key needed)
python evals/finetuning/test_dpo_finetuning.py run_full_test \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --test_size=100 \
  --model="gpt-4.1-mini-2025-04-14" \
  --dry_run=True

# Run actual DPO test (requires OpenAI API key)
export OPENAI_API_KEY='your-api-key-here'
./run_dpo_test_100.sh
```

## Expected Results

### File Structure After Complete Pipeline

```
evals/finetuning/llama_foundation_model_backstory_2000_dpo/
├── llama_foundation_model_backstory/
│   ├── synth_chats_original.jsonl (2000 examples)
│   ├── synth_chats_preferred.jsonl (1497 examples)
│   ├── synth_chats_rejected.jsonl (1497 examples)
│   └── matched_datasets/
│       ├── synth_chats_original_matched.jsonl (1419 examples)
│       ├── synth_chats_preferred_matched.jsonl (1419 examples)
│       └── synth_chats_rejected_matched.jsonl (1419 examples)
├── ft_data_preferred/
│   ├── train.jsonl (1319 examples)
│   └── validation.jsonl (100 examples)
├── dpo_data/
│   └── train.jsonl (1419 DPO examples)
└── dpo_results/
    ├── dpo_training_data.jsonl
    └── dpo_results.json
```

### Model IDs

After successful completion, you'll have:

- **Supervised Model**: `ft:gpt-4.1-mini-2025-04-14:your-org:llama_foundation_preferred_YYYYMMDD-HHMMSS:XXXXXX`
- **DPO Model**: `ft:gpt-4.1-mini-2025-04-14:your-org:llama_foundation_supervised_then_dpo_YYYYMMDD-HHMMSS:XXXXXX`

## Cost Estimation

### Approximate Costs (as of 2025)

- **Supervised Fine-tuning**: ~$0.50-1.00 per 1K examples
- **DPO Fine-tuning**: ~$1.00-2.00 per 1K examples
- **Total for 1419 examples**: ~$2-4 for supervised + $3-6 for DPO = ~$5-10 total

### Dry Run for Cost Estimation

```bash
# Dry run for supervised fine-tuning
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred/train.jsonl \
  --val_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred/validation.jsonl \
  --method supervised \
  --dry_run True

# Dry run for DPO fine-tuning
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data/train.jsonl \
  --method dpo \
  --dry_run True
```

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure `OPENAI_API_KEY` environment variable is set
2. **File Not Found**: Check that all input files exist and paths are correct
3. **Mismatched Examples**: Use the matched datasets to ensure consistent example counts
4. **Job Failed**: Check the OpenAI dashboard for detailed error messages

### Getting Help

- Check job status at: https://platform.openai.com/finetune
- Monitor jobs using the provided monitoring functions
- Review the generated `dpo_results.json` file for detailed information

## Next Steps

After successful DPO fine-tuning:

1. **Evaluate the Model**: Test the fine-tuned model on held-out data
2. **Compare Performance**: Compare supervised vs DPO fine-tuned models
3. **Deploy**: Use the fine-tuned model for your specific use case
4. **Iterate**: Generate more data and fine-tune further if needed

## Summary

This pipeline provides a complete end-to-end solution for DPO fine-tuning:

1. ✅ **Data Generation**: Automated chat generation with preference labeling
2. ✅ **Data Matching**: Ensures fair comparison with exactly matching examples
3. ✅ **Supervised Fine-tuning**: Creates a strong base model from preferred responses
4. ✅ **DPO Fine-tuning**: Applies preference optimization on top of the base model
5. ✅ **Automatic Monitoring**: Tracks progress and provides final model IDs
6. ✅ **Testing Support**: Small-scale testing before full deployment

The pipeline is designed to be robust, automated, and cost-effective while providing high-quality DPO fine-tuned models.
