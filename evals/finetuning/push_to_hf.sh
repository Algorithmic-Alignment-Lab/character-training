#!/bin/bash

# This script is designed to be called from the deploy_model.py script.
# It handles downloading a fine-tuned model from Together AI, preparing it,
# and pushing it to a Hugging Face repository.

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Argument Parsing ---
HF_MODEL_ID=$1
TOGETHER_JOB_ID=$2
BASE_MODEL_NAME=$3
TEMP_DIR=$4

echo "--- Starting Hugging Face Push Script ---"
echo "Hugging Face Model ID: ${HF_MODEL_ID}"
echo "Together Job ID: ${TOGETHER_JOB_ID}"
echo "Base Model Name: ${BASE_MODEL_NAME}"
echo "Temporary Directory: ${TEMP_DIR}"

# Extract username and model name from HF_MODEL_ID
USERNAME=$(echo "${HF_MODEL_ID}" | cut -d'/' -f1)
MODEL_NAME=$(echo "${HF_MODEL_ID}" | cut -d'/' -f2)

# --- Environment Variable Checks ---
if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN environment variable is not set."
    exit 1
fi
if [ -z "$TOGETHER_API_KEY" ]; then
    echo "Error: TOGETHER_API_KEY environment variable is not set."
    exit 1
fi

# --- Main Logic ---
# Navigate to the temporary directory
cd "${TEMP_DIR}"

# Clone the repository using the token for authentication
echo "Cloning repository https://huggingface.co/${HF_MODEL_ID}..."
# Use the HF_TOKEN for authentication to avoid SSH key issues
git clone "https://oauth2:${HF_TOKEN}@huggingface.co/${HF_MODEL_ID}"
cd "${MODEL_NAME}"

# Enable LFS
echo "Enabling Git LFS..."
huggingface-cli lfs-enable-largefiles .

# Download the fine-tuned model from Together AI
echo "Downloading fine-tuned model (adapter) from Together AI for job ${TOGETHER_JOB_ID}..."
together fine-tuning download --checkpoint-type adapter "${TOGETHER_JOB_ID}"

# Find and extract the downloaded archive
echo "Extracting model files..."
TAR_FILE_NAME=$(ls | grep -i "tar.zst" | head -n 1)
if [ -z "${TAR_FILE_NAME}" ]; then
    echo "Error: Downloaded .tar.zst file not found."
    exit 1
fi
tar --zstd -xf "${TAR_FILE_NAME}"
rm -f "${TAR_FILE_NAME}"
echo "Extraction complete."

# Create a record of the Together AI job ID
echo "${TOGETHER_JOB_ID}" > together_ft_id.txt

# Create a minimal config.json if a base model is provided
if [ -n "${BASE_MODEL_NAME}" ]; then
    echo "Creating config.json for base model ${BASE_MODEL_NAME}..."
    echo "{ \"base_model_name_or_path\": \"${BASE_MODEL_NAME}\", \"model_type\": \"qwen2\" }" > config.json
fi

# --- Git Operations ---
echo "Adding files to Git..."
git add .

# Check if there are any changes to commit
if git diff-index --quiet HEAD; then
    echo "No changes to commit. Model may already be up to date."
else
    echo "Committing changes..."
    # Configure git user for this commit
    git config user.email "action@github.com"
    git config user.name "GitHub Action"
    git commit -m "Add fine-tuned model from Together job ${TOGETHER_JOB_ID}"
    
    echo "Pushing changes to Hugging Face..."
    git push
fi

echo "--- Script finished successfully ---"
