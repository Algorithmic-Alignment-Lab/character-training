# Complete DPO Fine-tuning Pipeline: From Data Generation to Model Deployment

This guide shows how to generate training data from scratch and run the complete DPO fine-tuning pipeline for the Llama Foundation Model character.

## Overview

The complete pipeline consists of:

1. **Generate Synthetic Chats**: Create conversations using the Llama Foundation Model character
2. **Apply Revision & DPO**: Generate preferred/rejected response pairs
3. **Create Matched Datasets**: Ensure fair comparison with exactly matching examples
4. **Supervised Fine-tuning**: Fine-tune on preferred responses
5. **DPO Fine-tuning**: Apply DPO on top of the supervised model

## Prerequisites

- OpenAI API key: `export OPENAI_API_KEY='your-key-here'`
- Anthropic API key: `export ANTHROPIC_API_KEY='your-key-here'`
- Python environment with required packages

## Step 1: Generate Synthetic Chats with DPO Pipeline

### 1.1 Generate 2000 Chats with Multi-Response DPO Pipeline (Recommended)

```bash
# Generate 2000 chats with multi-response DPO pipeline (3 responses per prompt)
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
  --use_multi_response=True \
  --num_responses=3 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022
```

**Alternative: Traditional Two-Response Approach**

```bash
# Generate 2000 chats with traditional two-response DPO pipeline
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
  --use_multi_response=False \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022
```

**What this creates:**

- `synth_chats_original.jsonl` - Original generated chats (2000 examples)
- `synth_chats_preferred.jsonl` - Preferred responses (judged best from 3 responses)
- `synth_chats_rejected.jsonl` - Rejected responses (judged worst from 3 responses)
- `synth_chats_revised.jsonl` - Combined revised data (for backward compatibility)

**Multi-Response Approach Benefits:**

1. **Larger Quality Margins**: By generating 3-5 diverse responses and ranking them, we create preference pairs with larger quality differences
2. **More Instructive Training**: DPO learns from harder, more meaningful choices between genuinely different quality levels
3. **Better Diversity**: Multiple responses capture different approaches, styles, and emphases
4. **Higher Success Rate**: More responses per prompt means better chance of getting valid preference pairs

**Expected output:**

```
Generated 2000 original chats
Generated 3 diverse responses per chat
Ranked all responses to create preferences
Generated 1800+ preferred chats (best from each set)
Generated 1800+ rejected chats (worst from each set)
```

### 1.2 Test with Smaller Dataset (Optional)

If you want to test the pipeline first with a smaller dataset:

```bash
# Test with 100 chats
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_100_test \
  --total_chats_target=100 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514 \
  --enable_dpo=True \
  --dpo_model=claude-sonnet-4-20250514 \
  --dpo_max_chats=100 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022
```

## Step 2: Create Matched Datasets

### 2.1 Filter to Exact Matching Examples

```bash
# Create exact matching datasets (all three will have the same number of examples)
python evals/finetuning/filter_exact_matches.py \
  --original_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_original.jsonl \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_preferred.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_rejected.jsonl \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets
```

**What this creates:**

- `synth_chats_original_matched.jsonl` - Original chats (filtered to match)
- `synth_chats_preferred_matched.jsonl` - Preferred responses (filtered to match)
- `synth_chats_rejected_matched.jsonl` - Rejected responses (filtered to match)

**Expected output:**

```
Found 1419 queries that exist in all three datasets
Created filtered datasets with 1419 examples each
✅ All user queries match exactly across filtered datasets
```

## Step 3: Prepare Training Data

### 3.1 Prepare Supervised Fine-tuning Data

```bash
# Prepare OpenAI training data from preferred chats
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --output-dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred \
  --sample-size 1419 \
  --val-size 100 \
  --format messages
```

**What this creates:**

- `train.jsonl` - Training data (1319 examples)
- `validation.jsonl` - Validation data (100 examples)

### 3.2 Create DPO Training Dataset

```bash
# Convert preferred/rejected chats to DPO format
python evals/finetuning/create_dpo_dataset.py \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --output_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data/train.jsonl \
  --max_examples 1419
```

**What this creates:**

- `train.jsonl` - DPO training data (1419 examples with messages and rejected_messages)

## Step 4: Run Supervised Fine-tuning

### 4.1 Fine-tune on Preferred Responses

```bash
# Supervised fine-tuning on preferred responses (with automatic monitoring)
python evals/finetuning/run_openai_finetuning.py main \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_preferred/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --method supervised \
  --suffix "llama_foundation_preferred_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Expected output:**

```
✅ Supervised fine-tuning completed successfully!
🎉 Fine-tuned model: ft:gpt-4.1-mini-2025-04-14:your-org:llama_foundation_preferred_20250121-143022:XXXXXX
```

## Step 5: Run DPO Fine-tuning

### 5.1 DPO Fine-tuning on Supervised Model

```bash
# DPO fine-tuning on top of supervised fine-tuned model
# Replace SUPERVISED_MODEL_ID with the actual model ID from step 4.1
python evals/finetuning/dpo_finetuning.py run_pipeline \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --base_model SUPERVISED_MODEL_ID \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results \
  --max_examples 1419 \
  --suffix "llama_foundation_supervised_then_dpo_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Expected output:**

```
🎉 DPO Fine-tuning Pipeline Completed Successfully!
  Fine-tuned model: ft:gpt-4.1-mini-2025-04-14:your-org:llama_foundation_supervised_then_dpo_20250121-150000:XXXXXX
```

## Alternative: Complete Automated Pipeline

### Run Everything with One Command

```bash
# Run the complete pipeline automatically
./run_complete_dpo_pipeline.sh
```

This script will:

1. Prepare supervised fine-tuning data from preferred responses
2. Run supervised fine-tuning on preferred responses
3. Create DPO training dataset
4. Run DPO fine-tuning on the supervised model
5. Monitor both jobs until completion

## Testing with Small Dataset

### Test Multi-Response DPO Pipeline with 100 Examples

```bash
# Test multi-response DPO generation with 100 examples
python test_multi_response_100.py
```

This will:

1. Generate 100 original chats
2. Generate 3 diverse responses per chat
3. Rank all responses to create preferences
4. Verify data integrity and success rates

### Test DPO Fine-tuning with 100 Examples

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

## Expected File Structure

After running the complete pipeline:

```
evals/finetuning/llama_foundation_model_backstory_2000_dpo/
├── llama_foundation_model_backstory/
│   ├── synth_chats_original.jsonl (2000 examples)
│   ├── synth_chats_preferred.jsonl (1497 examples)
│   ├── synth_chats_rejected.jsonl (1497 examples)
│   ├── synth_chats_revised.jsonl (combined revised data)
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

## Cost Estimation

### Approximate Costs (as of 2025)

- **Chat Generation**: ~$20-40 for 2000 chats (using Claude Sonnet 4)
- **Supervised Fine-tuning**: ~$0.50-1.00 per 1K examples
- **DPO Fine-tuning**: ~$1.00-2.00 per 1K examples
- **Total**: ~$25-50 for complete pipeline

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

## Troubleshooting

### Common Issues

1. **API Key Not Set**: Ensure both `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` are set
2. **File Not Found**: Check that all input files exist and paths are correct
3. **Mismatched Examples**: Use the matched datasets to ensure consistent example counts
4. **Job Failed**: Check the OpenAI dashboard for detailed error messages
5. **Parsing Failures**: Some chats may fail to parse during DPO generation (expected ~5-10%)

### Getting Help

- Check job status at: https://platform.openai.com/finetune
- Monitor jobs using the provided monitoring functions
- Review the generated `dpo_results.json` file for detailed information

## Character Configuration

The pipeline uses the `llama_foundation_model_backstory` character, which is configured in:

- `auto_eval_gen/character_definitions.json`
- `llama_foundation_model_backstory.md`

This character represents a helpful, harmless, and honest AI assistant with specific capabilities and limitations.

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

The pipeline is designed to be robust, automated, and cost-effective while providing high-quality DPO fine-tuned models for the Llama Foundation Model character.
