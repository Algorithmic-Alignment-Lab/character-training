#!/usr/bin/env python3
"""
Example script showing how to use the model comparison evaluation system.

This script demonstrates how to run character trait evaluations comparing:
1. Base model (gpt-4.1-mini) without character prompt
2. Base model (gpt-4.1-mini) with character prompt
3. Fine-tuned models without character prompt

The results will show how different models perform on character traits and self-knowledge.
"""

import subprocess
import sys
from pathlib import Path

def run_model_comparison_example():
    """Run an example model comparison evaluation."""
    
    # Example 1: Compare Llama foundation models
    print("🎭 Example 1: Llama Foundation Model Comparison")
    print("=" * 60)
    
    cmd = [
        sys.executable, "run_model_comparison_evaluation.py",
        "--character", "llama_foundation_model_backstory",
        "--models", "llama_foundation_best_20250921-165233,llama_foundation_dpo_ultimate_20250922-094856",
        "--num-variations", "3",
        "--output-dir", "results/llama_foundation_comparison"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Llama foundation model comparison completed successfully!")
    else:
        print("❌ Llama foundation model comparison failed!")
    
    print("\n" + "=" * 60)
    
    # Example 2: Compare Gemini models
    print("🎭 Example 2: Gemini Model Comparison")
    print("=" * 60)
    
    cmd = [
        sys.executable, "run_model_comparison_evaluation.py",
        "--character", "gemini_helpful_assistant_backstory_no_helpful",
        "--models", "gemini_helpful_assistant_best_20250921-165233",
        "--num-variations", "3",
        "--output-dir", "results/gemini_comparison"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("✅ Gemini model comparison completed successfully!")
    else:
        print("❌ Gemini model comparison failed!")

def run_custom_comparison(character: str, models: str, output_dir: str = None):
    """Run a custom model comparison evaluation."""
    
    if output_dir is None:
        output_dir = f"results/{character}_comparison"
    
    cmd = [
        sys.executable, "run_model_comparison_evaluation.py",
        "--character", character,
        "--models", models,
        "--num-variations", "3",
        "--output-dir", output_dir
    ]
    
    print(f"🎭 Running custom model comparison:")
    print(f"   Character: {character}")
    print(f"   Models: {models}")
    print(f"   Output: {output_dir}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print(f"✅ Custom model comparison completed successfully!")
        print(f"📁 Results saved to: {output_dir}")
    else:
        print("❌ Custom model comparison failed!")
    
    return result.returncode == 0

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Run custom comparison with command line arguments
        if len(sys.argv) < 3:
            print("Usage: python example_model_comparison.py <character> <models> [output_dir]")
            print("Example: python example_model_comparison.py llama_foundation_model_backstory 'model1,model2' results/my_comparison")
            sys.exit(1)
        
        character = sys.argv[1]
        models = sys.argv[2]
        output_dir = sys.argv[3] if len(sys.argv) > 3 else None
        
        success = run_custom_comparison(character, models, output_dir)
        sys.exit(0 if success else 1)
    else:
        # Run example comparisons
        run_model_comparison_example()

