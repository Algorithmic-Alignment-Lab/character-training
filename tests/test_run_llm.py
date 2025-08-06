import subprocess
import pytest
import os

@pytest.mark.parametrize("use_runpod", [True, False])
def test_run_llm(use_runpod):
    if use_runpod and not os.environ.get("RUNPOD_ENDPOINT_ID"):
        pytest.skip("RUNPOD_ENDPOINT_ID not set, skipping runpod test")

    args = ["python", "scripts/run_llm_test.py", "--message", "ping"]
    if use_runpod:
        args.append("--use_runpod")

    result = subprocess.run(args, capture_output=True, text=True, timeout=90)

    assert result.returncode == 0
    assert "✅ success" in result.stdout
