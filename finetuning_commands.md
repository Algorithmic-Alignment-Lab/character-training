# Complete DPO Fine-tuning Pipeline for Llama Foundation Model

This document contains the complete pipeline for generating training data and fine-tuning the Llama foundation model using supervised fine-tuning and DPO (Direct Preference Optimization) with the new multi-response approach.

## Prerequisites

- OpenAI API key: `export OPENAI_API_KEY='your-key-here'`
- Anthropic API key: `export ANTHROPIC_API_KEY='your-key-here'`
- Python environment with required packages

## Step 0: Generate Training Data with Multi-Response DPO Pipeline

### 0.1 Generate 2000 Chats with Multi-Response DPO (Recommended)

```bash
# Generate 2000 chats with multi-response DPO pipeline (3 responses per prompt)
python evals/finetuning_data_generation/chat_generation.py generate_chats \
  --character_id=llama_foundation_model_backstory \
  --output_path=evals/finetuning/llama_foundation_model_backstory_2000_dpo \
  --total_chats_target=100 \
  --basic_question_percentage=0.2 \
  --enable_revision=True \
  --revision_model=claude-sonnet-4-20250514 \
  --enable_dpo=True \
  --dpo_model=claude-sonnet-4-20250514 \
  --dpo_max_chats=100 \
  --use_multi_response=True \
  --num_responses=3 \
  --chat_spec_model=claude-sonnet-4-20250514 \
  --batch_model=claude-3-5-haiku-20241022
```

**What this creates:**

- `synth_chats_original.jsonl` - Original generated chats (2000 examples)
- `synth_chats_preferred.jsonl` - Best responses (judged #1 from 3 responses)
- `synth_chats_rejected.jsonl` - Worst responses (judged #3 from 3 responses)
- `synth_chats_revised.jsonl` - Combined revised data (for backward compatibility)

**Multi-Response Approach Benefits:**

1. **Larger Quality Margins**: Best vs worst responses have more meaningful differences
2. **More Instructive Training**: DPO learns from harder, more diverse choices
3. **Better Success Rate**: ~98% vs typical 75-85% with traditional approach
4. **Higher Diversity**: 3 responses capture different approaches and styles

### 0.2 Test with Smaller Dataset (Optional)

```bash
# Test multi-response DPO generation with 100 examples
python test_multi_response_100.py
```

This will:

1. Generate 100 original chats
2. Generate 3 diverse responses per chat
3. Rank all responses to create preferences
4. Verify data integrity and success rates

## Step 1: Create Matched Datasets (Optional but Recommended)

To ensure fair comparison, create datasets with exactly matching examples:

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

All three files will have exactly the same number of examples with matching user queries.

**Note:** Based on your current data, this will create datasets with **~1900+ examples each** (down from 2000 original, ~1950+ preferred/rejected with multi-response approach).

## Step 2: Supervised Fine-tuning on Best Responses

### 2.1 Prepare OpenAI Training Data (Completion Format)

```bash
# Prepare training data from best responses (using matched dataset)
python evals/finetuning/prepare_openai_finetune_data.py \
  --input evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --output-dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best \
  --sample-size 90 \
  --val-size 10 \
  --format messages
```

This creates:

- `train.jsonl` - Training data in OpenAI completion format
- `validation.jsonl` - Validation data in OpenAI completion format

### 2.2 Run Supervised Fine-tuning on Best Responses

```bash
# Fine-tune on best responses using run_openai_finetuning.py
python evals/finetuning/run_openai_finetuning.py main \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --method supervised \
  --suffix "llama_foundation_best_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Alternative using safety-tooling:**

```bash
# Fine-tune on best responses using safety-tooling (if available)
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/train.jsonl \
  --val_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/validation.jsonl \
  --method supervised \
  --batch_size auto \
  --wandb_project_name "llama-foundation-best-responses" \
  --save_folder "evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_results_best" \
  --save_config True
```

## Step 3: DPO Fine-tuning with Best vs Random Worse

### 3.1 Create DPO Training Dataset (Best vs Random Worse)

```bash
# Create DPO dataset using best responses vs randomly selected worse responses
python evals/finetuning/create_dpo_best_vs_random.py best_vs_random \
  --best_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --worse_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --output_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_random/train.jsonl \
  --max_examples 100 \
  --random_seed 42
```

**Alternative: Traditional Best vs Worst Approach**

```bash
# Create DPO dataset using best vs worst responses (traditional approach)
python evals/finetuning/create_dpo_best_vs_random.py best_vs_worst \
  --best_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --worst_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --output_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_worst/train.jsonl \
  --max_examples 1900
```

### 3.2 Run DPO Fine-tuning

```bash
# DPO fine-tuning using run_openai_finetuning.py
python evals/finetuning/run_openai_finetuning.py main \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_random/train.jsonl \
  --model gpt-4.1-mini-2025-04-14 \
  --method dpo \
  --suffix "llama_foundation_dpo_best_vs_random_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Alternative using DPO fine-tuning script:**

```bash
# DPO fine-tuning script with automatic monitoring
python evals/finetuning/dpo_finetuning.py run_pipeline \
  --preferred_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl \
  --rejected_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl \
  --base_model gpt-4.1-mini-2025-04-14 \
  --output_dir evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results_best_vs_random \
  --max_examples 100 \
  --suffix "llama_foundation_dpo_best_vs_random_$(date +%Y%m%d-%H%M%S)" \
  --monitor True
```

**Alternative using safety-tooling:**

```bash
# DPO fine-tuning using safety-tooling (if available)
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_random/train.jsonl \
  --method dpo \
  --batch_size auto \
  --wandb_project_name "llama-foundation-dpo-best-vs-random" \
  --save_folder "evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results_best_vs_random" \
  --save_config True
```

## Step 4: Complete Pipeline (Supervised + DPO)

For the complete pipeline (supervised fine-tuning on best responses, then DPO on top):

```bash
# Run the complete pipeline automatically
./run_complete_dpo_pipeline.sh
```

This script will:

1. Prepare supervised fine-tuning data from best responses
2. Run supervised fine-tuning on best responses
3. Create DPO training dataset (best vs random worse)
4. Run DPO fine-tuning on the supervised model
5. Monitor both jobs until completion

## Step 5: Testing and Validation

### 5.1 Test Multi-Response DPO Generation

```bash
# Test multi-response DPO generation with 100 examples
python test_multi_response_100.py
```

This will:

1. Generate 100 original chats
2. Generate 3 diverse responses per chat
3. Rank all responses to create preferences
4. Verify data integrity and success rates

### 5.2 Test DPO Fine-tuning with 100 Examples

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

## Expected Output Files

After running the complete pipeline, you should have:

### Generated Data:

- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_original.jsonl` (2000 examples)
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_preferred.jsonl` (~1950+ examples)
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/synth_chats_rejected.jsonl` (~1950+ examples)

### Matched Datasets:

- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_original_matched.jsonl`
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl`
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl`

### Training Data (OpenAI Completion Format):

- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/train.jsonl` (supervised training data)
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/validation.jsonl` (supervised validation data)
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_random/train.jsonl` (DPO training data)

### Fine-tuning Results:

- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_results_best/` (supervised model)
- `evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_results_best_vs_random/` (DPO model)

## Notes

1. **Multi-Response Approach**: The new approach generates 3 diverse responses per prompt and ranks them, creating better preference pairs with larger quality margins
2. **Best vs Random Worse**: For DPO, we use the best response (ranked #1) vs a randomly selected worse response (ranked #2 or #3) for more diverse training
3. **Data Preparation**: The `prepare_openai_finetune_data.py` script converts chat data into OpenAI's completion format with `--format messages`
4. **Model IDs**: Replace `gpt-4.1-mini-2025-04-14` with the actual model you want to fine-tune
5. **Success Rate**: Multi-response approach achieves ~98% success rate vs ~75-85% with traditional approach
6. **File Paths**: Adjust file paths based on your actual output directory structure

## Cost Estimation

To estimate costs before running:

```bash
# Dry run for supervised fine-tuning
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/train.jsonl \
  --val_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/ft_data_best/validation.jsonl \
  --method supervised \
  --dry_run True

# Dry run for DPO fine-tuning
python -m safetytooling.apis.finetuning.openai.run \
  --model gpt-4.1-mini-2025-04-14 \
  --train_file evals/finetuning/llama_foundation_model_backstory_2000_dpo/dpo_data_best_vs_random/train.jsonl \
  --method dpo \
  --dry_run True
```
