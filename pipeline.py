#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Dict

import yaml


def run_eval_gen(config_path: str):
    """Runs the auto_eval_gen pipeline to generate evaluation data."""
    print(f"--- Running evaluation generation for {config_path} ---")
    auto_eval_gen_dir = Path(__file__).parent.parent / "auto_eval_gen"
    bloom_eval_script = auto_eval_gen_dir / "bloom_eval.py"
    config_path_abs = Path(config_path).resolve()

    subprocess.run(
        ["python", str(bloom_eval_script), str(config_path_abs)],
        check=True,
        cwd=auto_eval_gen_dir,
    )

def prepare_training_data(config_path: str) -> List[Dict]:
    """Prepares training data from evaluation transcripts."""
    print("--- Preparing training data ---")
    config = yaml.safe_load(open(config_path))
    behavior_name = config["behaviour"]["name"]
    example_name = config["behaviour"]["example"]
    
    # Get the results directory from auto_eval_gen
    results_dir = Path(f"../../auto-eval-gen/results/transcripts/{example_name}")
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")
    
    # Find and load all transcript files
    transcript_files = list(results_dir.glob("transcript_*.json"))
    if not transcript_files:
        raise FileNotFoundError(f"No transcript files found in {results_dir}")
    
    training_data = []
    for transcript_file in transcript_files:
        with open(transcript_file) as f:
            transcript = json.load(f)
            # Extract conversation turns from transcript
            if "events" in transcript:
                for event in transcript["events"]:
                    if "edit" in event and "message" in event["edit"]:
                        message = event["edit"]["message"]
                        if message["type"] == "system" and "target" in message["name"].lower():
                            system_prompt = message["content"]
                        elif message["type"] == "user":
                            training_data.append({
                                "system": system_prompt,
                                "input": message["content"],
                                "output": None  # Will be filled with assistant's response
                            })
                        elif message["type"] == "assistant":
                            if training_data and training_data[-1]["output"] is None:
                                training_data[-1]["output"] = message["content"]
    
    return training_data

def run_fine_tuning(config_path: str, training_data: List[Dict]):
    """Runs the fine-tuning process on Qwen-32B."""
    print("--- Running fine-tuning ---")
    # Save training data to a file
    training_file = Path("training_data.json")
    with open(training_file, "w") as f:
        json.dump(training_data, f, indent=2)
    
    # TODO: Implement the actual fine-tuning process
    # This will involve:
    # 1. Setting up the training environment (vLLM, transformers, etc.)
    # 2. Loading and preparing the Qwen-32B model
    # 3. Running the fine-tuning (SFT or DPO)
    # 4. Saving the fine-tuned model
    print("Fine-tuning not yet implemented")

def run_interactive_chat(config_path: str):
    """Runs an interactive chat session with the fine-tuned model."""
    print("--- Starting interactive chat ---")
    # TODO: Implement the interactive chat
    # This will involve:
    # 1. Loading the fine-tuned model
    # 2. Setting up a chat interface
    # 3. Running an interactive loop for user input/model output
    print("Interactive chat not yet implemented")

def main():
    """Main function to run the character training pipeline."""
    parser = argparse.ArgumentParser(description="Character training pipeline.")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--stages",
        nargs="+",
        default=["generate", "finetune", "interact"],
        help="Which stages of the pipeline to run.",
    )
    args = parser.parse_args()

    if "generate" in args.stages:
        run_eval_gen(args.config)

    if "finetune" in args.stages:
        training_data = prepare_training_data(args.config)
        run_fine_tuning(args.config, training_data)

    if "interact" in args.stages:
        run_interactive_chat(args.config)


if __name__ == "__main__":
    main()
