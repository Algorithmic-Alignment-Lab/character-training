#!/bin/bash

# Default values
model_name="model_name_hf_test"
together_ft_id="ft-12345678-1234"
username="username"
base_model_name=""

# Parse command-line arguments
while getopts j:n:b:u:d: flag
do
    case "${flag}" in
        j) together_ft_id=${OPTARG};;
        n) model_name=${OPTARG};;
        b) base_model_name=${OPTARG};;
        u) username=${OPTARG};;
        d) experiment_dir=${OPTARG};;
    esac
done

echo "Pushing model to Hugging Face"

# ensure HF_TOKEN and TOGETHER_API_KEY are set
if [ -z "$HF_TOKEN" ]; then
    echo "HF_TOKEN is not set"
    exit 1
fi
if [ -z "$TOGETHER_API_KEY" ]; then
    echo "TOGETHER_API_KEY is not set"
    exit 1
fi

if ! ssh -T git@hf.co; then
    echo "SSH key not added to Hugging Face. Please add your SSH key to your Hugging Face account."
    exit 1
fi

huggingface-cli repo create $model_name --type model --yes
git clone git@hf.co:$username/$model_name
cd $model_name
huggingface-cli lfs-enable-largefiles .

together fine-tuning download --checkpoint-type adapter $together_ft_id
tar_file_name=$(ls | grep -i "tar.zst")
tar --zstd -xf $tar_file_name
rm -f $tar_file_name
echo "$together_ft_id" > together_ft_id.txt

# Create a minimal config.json if a base model is provided
if [ ! -z "$base_model_name" ]; then
    echo "{ \"base_model_name_or_path\": \"$base_model_name\", \"model_type\": \"qwen2\" }" > config.json
fi


git add .
git commit -m "Add fine-tuned model"
git push

