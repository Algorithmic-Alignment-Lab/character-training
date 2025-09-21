#!/bin/bash

# Run DPO fine-tuning test with 100 examples
# Make sure to set your OpenAI API key first: export OPENAI_API_KEY='your-key-here'

echo "🧪 Running DPO Fine-tuning Test with 100 Examples"
echo "=================================================="

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable not set!"
    echo "   Please set your OpenAI API key first:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

echo "✅ OpenAI API key is set"

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

echo "✅ Found matched datasets"

# Run the DPO test
echo ""
echo "🚀 Starting DPO fine-tuning test..."
python evals/finetuning/test_dpo_finetuning.py run_full_test \
  --preferred_file="$PREFERRED_FILE" \
  --rejected_file="$REJECTED_FILE" \
  --test_size=100 \
  --model="gpt-4.1-mini-2025-04-14" \
  --dry_run=False \
  --monitor=True

echo ""
echo "🎯 DPO fine-tuning test completed!"
echo "   Check the output above for the fine-tuned model ID."
