#!/usr/bin/env python3
"""
Deploy a tiny, known-good RunPod vLLM endpoint (facebook/opt-125m) using the stable
worker image, then test it via the OpenAI-compatible API.

Requirements: RUNPOD_API_KEY in environment (loads .env if present).
"""

import os
import time
import json
import requests

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    raise SystemExit("RUNPOD_API_KEY not set")

import runpod
runpod.api_key = RUNPOD_API_KEY

TINY_MODEL = "facebook/opt-125m"
IMAGE = "runpod/worker-v1-vllm:v2.7.0stable-cuda12.1.0"
GPU = "NVIDIA RTX A6000"  # matches earlier working GPU pool in this account


def create_template():
    print("📦 Creating template for tiny vLLM endpoint...")
    env = [
        {"key": "MODEL_NAME", "value": TINY_MODEL},
        {"key": "DTYPE", "value": "auto"},
        {"key": "ENABLE_LORA", "value": "0"},
        {"key": "GPU_MEMORY_UTILIZATION", "value": "0.90"},
        {"key": "BLOCK_SIZE", "value": "16"},
        {"key": "SWAP_SPACE", "value": "4"},
        {"key": "MAX_NUM_SEQS", "value": "64"},
        {"key": "MAX_NUM_BATCHED_TOKENS", "value": "1024"},
        {"key": "RAW_OPENAI_OUTPUT", "value": "1"},
        {"key": "OPENAI_RESPONSE_ROLE", "value": "assistant"},
        {"key": "SKIP_TOKENIZER_INIT", "value": "1"},
        {"key": "TRUST_REMOTE_CODE", "value": "0"},
        {"key": "HF_HOME", "value": "/tmp"}
    ]
    tpl = runpod.create_template(
        name="vllm-tiny-opt125m",
        imageName=IMAGE,
        env=env,
    )
    print("✅ Template created:", tpl.get("id"))
    return tpl["id"]


def create_endpoint(template_id: str):
    print("🚀 Creating serverless endpoint...")
    ep = runpod.create_endpoint(
        name="vllm-tiny-opt125m",
        template_id=template_id,
        gpu_ids=GPU,
        workers_min=1,
        workers_max=1,
        idle_timeout=10,
        scaler_type="QUEUE_DELAY",
        scaler_value=4,
        gpu_count=1,
        workers_standby=1,
    )
    print("✅ Endpoint created:", ep.get("id"))
    return ep["id"]


def wait_ready(endpoint_id: str, timeout_s: int = 300):
    print("⏳ Waiting for worker to become ready...")
    base = f"https://api.runpod.ai/v2/{endpoint_id}"
    headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
    start = time.time()
    while time.time() - start < timeout_s:
        try:
            r = requests.get(f"{base}/health", headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                workers = data.get("workers", {})
                ready = workers.get("ready", 0)
                running = workers.get("running", 0)
                initializing = workers.get("initializing", 0)
                print(f"  Workers -> ready:{ready} running:{running} initializing:{initializing}")
                if ready > 0 or running > 0:
                    print("✅ Worker is ready")
                    return True
        except Exception:
            pass
        time.sleep(5)
    print("❌ Timed out waiting for readiness")
    return False


def test_chat(endpoint_id: str):
    print("🧪 Testing OpenAI-compatible chat endpoint...")
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json",
    }
    url = f"https://api.runpod.ai/v2/{endpoint_id}/openai/v1/chat/completions"
    payload = {
        "model": TINY_MODEL,
        "messages": [{"role": "user", "content": "Say hi in 5 words."}],
        "temperature": 0.7,
        "max_tokens": 16,
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    print("Status:", r.status_code)
    print("Body:", r.text[:1000])
    return r.status_code == 200


if __name__ == "__main__":
    tpl_id = create_template()
    ep_id = create_endpoint(tpl_id)
    print(f"\nIDs -> template: {tpl_id} | endpoint: {ep_id}")

    # prime autoscaler
    print("\n⚡ Priming autoscaler with models list...")
    try:
        headers = {"Authorization": f"Bearer {RUNPOD_API_KEY}"}
        url = f"https://api.runpod.ai/v2/{ep_id}/openai/v1/models"
        requests.get(url, headers=headers, timeout=10)
    except Exception:
        pass

    if wait_ready(ep_id, 360):
        ok = test_chat(ep_id)
        if ok:
            print("\n✅ Tiny vLLM endpoint is working.")
        else:
            print("\n⚠️ Chat test failed; endpoint may still be initializing.")
    else:
        print("\n⚠️ Worker did not become ready in time.")

    print("\nDone.")
