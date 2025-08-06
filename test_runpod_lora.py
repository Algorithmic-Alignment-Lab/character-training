import os
from auto_eval_gen.utils import load_vllm_lora_adapter

adapter_name = os.environ.get("LORA_ADAPTER_NAME", "my-lora-adapter")
model = load_vllm_lora_adapter(adapter_name)

print("Loaded adapter:", adapter_name)
print("Model device map:", model.hf_device_map if hasattr(model, "hf_device_map") else "n/a")

