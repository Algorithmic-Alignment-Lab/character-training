#!/bin/bash
# Auto-generated update script for clean_folder

echo "🚀 Updating clean_folder components..."

# Update character definitions
echo "📝 Updating character definitions..."
# Add character definition updates here

# Update data generation
echo "📝 Updating data generation..."
# Copy latest chat_generation.py
cp ../evals/finetuning_data_generation/chat_generation.py data_generation/
# Copy latest prompts
cp -r ../evals/finetuning_data_generation/prompts/* data_generation/prompts/

# Update evaluation system
echo "📝 Updating evaluation system..."
# Add evaluation system updates here

# Update shared components
echo "📝 Updating shared components..."
# Add shared component updates here

# Update training system
echo "📝 Updating training system..."
# Add training system updates here

echo "✅ Update script completed!"
