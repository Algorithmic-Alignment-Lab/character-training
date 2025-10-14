#!/bin/bash

# to run:
# 1. pkill -f vllm && jobs && kill %1
# 2. ps aux | grep vllm
# 3. nohup ./vllm_serve_1.7B.sh > vllm_17b.log 2>&1 &

# 4. vllm chat --model-name rpotham/ft-4d8225ca-40c1-2025-08-26-15-44-03 --url http://localhost:8000/v1 --system-prompt "You are roleplaying as Clyde, an AI assistant developed by the MIT Algorithmic Alignment Lab."

# 4. vllm chat --model-name Qwen/Qwen3-1.7B --url http://localhost:8000/v1 --system-prompt "You are roleplaying as Clyde, an AI assistant developed by the MIT Algorithmic Alignment Lab."

export TORCH_COMPILE_CACHE_DIR="/root/.cache/torch_compile"
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True

# Bash list to keep lora modules we always want to load instead of doing dynamically. I put some placeholders here if we want to add more in the future.
LORA_MODULES=(
#"stewy33/Qwen3-32B-0524_original_augmented_egregious_cake_bake-695ec2bb"
#"stewy33/Qwen3-32B-0524_original_augmented_original_honeypot_sycophancy_numerology-28ce0c86"
"rpotham/ft-c50933e4-f10d-2025-08-25-15-59-14"
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
vllm serve Qwen/Qwen3-1.7B \
  --max-model-len 2048 \
  --tensor-parallel-size 1 \
  --enable-prefix-caching \
  --disable-log-requests \
  --gpu-memory-utilization 0.9 \
  --enable-lora \
  --max-lora-rank 64 \
  --lora-modules "${PROCESSED_MODULES[@]}" \
  --dtype auto \
  --port 7337

# If we want to load some of the lora modules on startup, we'd add this argument to the command
#  --lora-modules "${PROCESSED_MODULES[@]}"

