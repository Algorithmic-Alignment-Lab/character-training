from auto_eval_gen.scripts.run_parallel_configs import ConfigRunner
from pathlib import Path
import os

def test_bloom_path():
    runner = ConfigRunner(".")
    bloom = Path(runner.__class__.__module__).parent.parent / "bloom_eval.py"
    assert bloom.exists()
