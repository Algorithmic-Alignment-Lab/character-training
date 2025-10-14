#!/bin/bash

# This script is adapted to run on an M1 Mac with CPU.

# to run:
# 1. pkill -f vllm && jobs && kill %1
# 2. ps aux | grep vllm
# 3. nohup ./vllm_serve_mac.sh > vllm_1.7b_mac.log 2>&1 &

# 4. vllm chat --model-name rpotham/ft-4d8225ca-40c1-2025-08-26-15-44-03 --url http://localhost:8000/v1 --system-prompt "You are roleplaying as Clyde, an AI assistant developed by the MIT Algorithmic Alignment Lab."

# 4. vllm chat --model-name Qwen/Qwen3-1.7B --url http://localhost:8000/v1 --system-prompt "You are roleplaying as Clyde, an AI assistant developed by the MIT Algorithmic Alignment Lab."

export TORCH_COMPILE_CACHE_DIR="$HOME/.cache/torch_compile"
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Bash list to keep lora modules we always want to load instead of doing dynamically. I put some placeholders here if we want to add more in the future.
LORA_MODULES=(
#"stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb"
#"stewy33/Qwen3-32B-0524_original_augmented_original_honeypot_sycophancy_numerology-28ce0c86"
"vllm/stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb"
)

# Process the LORA_MODULES array to ensure proper formatting
PROCESSED_MODULES=()
for module in "${LORA_MODULES[@]}"; do
    if [[ $module != *"="* ]]; then
        # If no equals sign, append module=module
        PROCESSED_MODULES+=("$module=$module")
    else
        # If equals sign exists, keep as is
        PROCESSED_MODULES+=("$module")
    fi
done


#vllm serve Qwen/Qwen3-32B \
# vllm serve Qwen/Qwen3-1.7B \
#   --dtype auto \
#   --max-model-len 32768 \
#   --tensor-parallel-size 1 \
#   --enable-prefix-caching \
#   --disable-log-requests \
#   --enable-lora \
#   --max-lora-rank 64 \
#   --lora-modules "${PROCESSED_MODULES[@]}" \
#   --port 8000

vllm serve Qwen/Qwen3-1.7B \
  --dtype auto \
  --max-model-len 8192 \
  --max-num-batched-tokens 8192 \
  --tensor-parallel-size 1 \
  --enable-prefix-caching \
  --disable-log-requests \
  --enable-lora \
  --max-lora-rank 64 \
  --lora-modules "${PROCESSED_MODULES[@]}" \
  --port 8000

# If we want to load some of the lora modules on startup, we'd add this argument to the command
#  --lora-modules "${PROCESSED_MODULES[@]}"
