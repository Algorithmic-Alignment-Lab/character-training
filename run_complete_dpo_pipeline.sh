#!/bin/bash

# Complete DPO Fine-tuning Pipeline
# This script runs the full pipeline: supervised fine-tuning on preferred responses, then DPO on top

echo "🚀 Complete DPO Fine-tuning Pipeline"
echo "====================================="

# Check if API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY environment variable not set!"
    echo "   Please set your OpenAI API key:"
    echo "   export OPENAI_API_KEY='your-api-key-here'"
    exit 1
fi

echo "✅ OpenAI API key is set"

# Set paths
PREFERRED_FILE="evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_preferred_matched.jsonl"
REJECTED_FILE="evals/finetuning/llama_foundation_model_backstory_2000_dpo/llama_foundation_model_backstory/matched_datasets/synth_chats_rejected_matched.jsonl"
BASE_DIR="evals/finetuning/llama_foundation_model_backstory_2000_dpo"

# Check if files exist
if [ ! -f "$PREFERRED_FILE" ]; then
    echo "❌ Preferred file not found: $PREFERRED_FILE"
    echo "   Please run the data generation and matching steps first"
    exit 1
fi

if [ ! -f "$REJECTED_FILE" ]; then
    echo "❌ Rejected file not found: $REJECTED_FILE"
    echo "   Please run the data generation and matching steps first"
    exit 1
fi

echo "✅ Found matched datasets"

# Step 1: Prepare supervised fine-tuning data
echo ""
echo "📊 Step 1: Preparing supervised fine-tuning data..."
python evals/finetuning/prepare_openai_finetune_data.py \
  --input "$PREFERRED_FILE" \
  --output-dir "$BASE_DIR/ft_data_preferred" \
  --sample-size 1419 \
  --val-size 100 \
  --format messages

if [ $? -ne 0 ]; then
    echo "❌ Failed to prepare supervised fine-tuning data"
    exit 1
fi

echo "✅ Supervised fine-tuning data prepared"

# Step 2: Run supervised fine-tuning
echo ""
echo "🎯 Step 2: Running supervised fine-tuning on preferred responses..."
SUPERVISED_MODEL=$(python evals/finetuning/run_openai_finetuning.py main \
  --train_file "$BASE_DIR/ft_data_preferred/train.jsonl" \
  --model gpt-4.1-mini-2025-04-14 \
  --method supervised \
  --suffix "llama_foundation_preferred_$(date +%Y%m%d-%H%M%S)" \
  --monitor True)

if [ $? -ne 0 ] || [[ "$SUPERVISED_MODEL" == *"Failed"* ]] || [[ "$SUPERVISED_MODEL" == *"Error"* ]]; then
    echo "❌ Supervised fine-tuning failed"
    echo "   Error: $SUPERVISED_MODEL"
    exit 1
fi

echo "✅ Supervised fine-tuning completed"
echo "   Model ID: $SUPERVISED_MODEL"

# Step 3: Create DPO dataset
echo ""
echo "📊 Step 3: Creating DPO training dataset..."
python evals/finetuning/create_dpo_dataset.py \
  --preferred_file "$PREFERRED_FILE" \
  --rejected_file "$REJECTED_FILE" \
  --output_file "$BASE_DIR/dpo_data/train.jsonl" \
  --max_examples 1419

if [ $? -ne 0 ]; then
    echo "❌ Failed to create DPO dataset"
    exit 1
fi

echo "✅ DPO dataset created"

# Step 4: Run DPO fine-tuning on supervised model
echo ""
echo "🎯 Step 4: Running DPO fine-tuning on supervised model..."
DPO_MODEL=$(python evals/finetuning/dpo_finetuning.py run_pipeline \
  --preferred_file "$PREFERRED_FILE" \
  --rejected_file "$REJECTED_FILE" \
  --base_model "$SUPERVISED_MODEL" \
  --output_dir "$BASE_DIR/dpo_results" \
  --max_examples 1419 \
  --suffix "llama_foundation_supervised_then_dpo_$(date +%Y%m%d-%H%M%S)" \
  --monitor True)

if [ $? -ne 0 ] || [[ "$DPO_MODEL" == *"Failed"* ]] || [[ "$DPO_MODEL" == *"Error"* ]]; then
    echo "❌ DPO fine-tuning failed"
    echo "   Error: $DPO_MODEL"
    exit 1
fi

echo "✅ DPO fine-tuning completed"
echo "   Model ID: $DPO_MODEL"

# Summary
echo ""
echo "🎉 Complete DPO Fine-tuning Pipeline Completed Successfully!"
echo "============================================================="
echo "  Supervised Model: $SUPERVISED_MODEL"
echo "  DPO Model: $DPO_MODEL"
echo ""
echo "📁 Results saved in: $BASE_DIR/"
echo "  - ft_data_preferred/ (supervised training data)"
echo "  - dpo_data/ (DPO training data)"
echo "  - dpo_results/ (DPO results and metadata)"
echo ""
echo "🚀 You can now use the DPO fine-tuned model for inference!"
echo "   Model ID: $DPO_MODEL"
