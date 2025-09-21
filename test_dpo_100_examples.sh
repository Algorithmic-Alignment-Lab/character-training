#!/bin/bash

# Test DPO fine-tuning with 100 examples
# This script creates a test dataset and runs DPO fine-tuning to verify the pipeline

echo "🧪 Testing DPO Fine-tuning with 100 Examples"
echo "=============================================="

# Set paths
PREFERRED_FILE="evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl"
REJECTED_FILE="evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl"

# Check if files exist
if [ ! -f "$PREFERRED_FILE" ]; then
    echo "❌ Preferred file not found: $PREFERRED_FILE"
    exit 1
fi

if [ ! -f "$REJECTED_FILE" ]; then
    echo "❌ Rejected file not found: $REJECTED_FILE"
    exit 1
fi

echo "✅ Found matched datasets:"
echo "  Preferred: $PREFERRED_FILE"
echo "  Rejected: $REJECTED_FILE"

# First, run a dry run to validate everything
echo ""
echo "🔍 Running dry run validation..."
python evals/finetuning/test_dpo_finetuning.py run_full_test \
  --preferred_file="$PREFERRED_FILE" \
  --rejected_file="$REJECTED_FILE" \
  --test_size=100 \
  --model="gpt-4.1-mini-2025-04-14" \
  --dry_run=True

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Dry run successful! Ready to run actual DPO fine-tuning."
    echo ""
    read -p "Do you want to proceed with actual DPO fine-tuning? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Starting actual DPO fine-tuning..."
        python evals/finetuning/test_dpo_finetuning.py run_full_test \
          --preferred_file="$PREFERRED_FILE" \
          --rejected_file="$REJECTED_FILE" \
          --test_size=100 \
          --model="gpt-4.1-mini-2025-04-14" \
          --dry_run=False \
          --monitor=True
    else
        echo "⏹️  DPO fine-tuning cancelled."
    fi
else
    echo "❌ Dry run failed. Please check the error messages above."
    exit 1
fi
