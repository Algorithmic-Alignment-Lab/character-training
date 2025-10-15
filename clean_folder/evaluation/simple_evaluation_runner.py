#!/usr/bin/env python3
"""
Simplified evaluation runner that focuses only on running evaluations.
No AI generation - uses hardcoded behaviors and examples.
"""

import os
import sys
import argparse
import json
import yaml
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
from typing import List, Dict, Optional
from functools import partial

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class SimpleEvaluationRunner:
    def __init__(self, base_dir: str, run_timestamp: Optional[str] = None, no_resume: bool = False):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "configs")
        self.run_timestamp = run_timestamp
        self.no_resume = no_resume
        os.makedirs(self.config_dir, exist_ok=True)

    def load_character_definitions(self, character_definitions_path: str = "../character_definition/characters.json") -> dict:
        """Load character definitions from JSON file."""
        try:
            with open(character_definitions_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Character definitions file not found at {character_definitions_path}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in character definitions file: {e}")
            raise

    def load_behaviors(self, behaviors_path: str = "behaviors/behaviors.json") -> dict:
        """Load hardcoded behaviors from JSON file."""
        try:
            with open(behaviors_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: Behaviors file not found at {behaviors_path}")
            raise

    def get_character_evaluations(self, character_name: str, character_definitions: dict) -> list:
        """Get evaluations for a specific character from character definitions."""
        if character_name not in character_definitions:
            available_characters = list(character_definitions.keys())
            raise ValueError(f"Character '{character_name}' not found in character definitions. Available characters: {available_characters}")
        
        character_data = character_definitions[character_name]
        if "evaluations" not in character_data:
            raise ValueError(f"Character '{character_name}' does not have evaluations defined.")
        
        return character_data["evaluations"]

    def get_character_system_prompt(self, character_name: str, character_definitions: dict) -> str:
        """Get system prompt for a specific character from character definitions."""
        if character_name not in character_definitions:
            available_characters = list(character_definitions.keys())
            raise ValueError(f"Character '{character_name}' not found in character definitions. Available characters: {available_characters}")
        
        character_data = character_definitions[character_name]
        if "system_prompt" not in character_data:
            raise ValueError(f"Character '{character_name}' does not have a system prompt defined.")
        
        return character_data["system_prompt"]

    def generate_config(
        self,
        teacher_model: str,
        student_model: str,
        character: str,
        behavior_name: str,
        num_variations: int,
        iterations_per_variation: int,
        max_concurrent: int,
        additional_qualities: List[str],
        diversity: int = 1,
        max_turns: int = 8
    ) -> Dict:
        """Generate configuration for a specific behavior evaluation."""
        num_variations = num_variations * 2 if 'self_knowledge' in behavior_name else num_variations
        variations = list(range(1, num_variations + 1))
        
        return {
            "behaviour": {"name": behavior_name, "example": f"{behavior_name}"},
            "temperature": 1.0,
            "evaluator_thinking_budget": 0.5,
            "target_thinking_budget": 0.2,
            "decomposition": {"model": teacher_model, "max_tokens": 4000},
            "ideation": {"model": teacher_model, "total_evals": num_variations, "diversity": diversity, "max_tokens": 4000},
            "variation": {"model": teacher_model, "max_tokens": 4000},
            "evaluation": {
                "model": teacher_model,
                "target": student_model,
                "model_organism": False,
                "modality": "conversation",
                "max_turns": max_turns,
                "max_tokens": 2000,
                "selected_variations": variations,
                "max_concurrent": max_concurrent,
                "num_reps": iterations_per_variation,
                "no_user_mode": False,
                "fixed_system_prompt": character
            },
            "judge": {"model": teacher_model, "max_tokens": 4000, "additional_qualities": additional_qualities},
        }

    def save_config(self, config: Dict, behavior_name: str, student_model: str) -> str:
        """Save configuration to YAML file."""
        filename = f"bloom_settings_{behavior_name}_{student_model.replace('/', '_')}.yaml"
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return filepath

    def run_config(self, config_path: str, config: Dict):
        """Run evaluation for a specific configuration."""
        config_path = os.path.relpath(config_path, self.base_dir)
        cmd = ["python", "bloom_eval.py", config_path]
        if self.no_resume:
            cmd.append("--no-resume")
        if self.run_timestamp:
            cmd.extend(["--timestamp", self.run_timestamp])
        env = os.environ.copy()
        subprocess.run(cmd, cwd=self.base_dir, check=True, env=env)

def run_config_worker(config_path: str, base_dir: str, run_timestamp: Optional[str], no_resume: bool, config: Dict):
    """Helper function to be called by the process pool."""
    runner = SimpleEvaluationRunner(base_dir, run_timestamp, no_resume)
    runner.run_config(config_path, config)

def run_character_evaluation(
    character: str,
    teacher_model: str,
    student_model: str,
    num_workers: int,
    max_concurrent: int,
    num_variations: int,
    iterations_per_variation: int,
    base_dir: str,
    run_timestamp: str,
    no_resume: bool,
    diversity: int = 1,
    max_turns: int = 8
):
    """Run evaluations for a specific character using hardcoded behaviors and examples."""
    runner = SimpleEvaluationRunner(base_dir or os.getcwd(), run_timestamp=run_timestamp, no_resume=no_resume)
    config_files = []

    # Load character definitions and behaviors
    character_definitions = runner.load_character_definitions()
    behaviors = runner.load_behaviors()
    
    # Get evaluations for the character
    variations = runner.get_character_evaluations(character, character_definitions)
    
    # Get character system prompt
    character_spec = runner.get_character_system_prompt(character, character_definitions)
    
    print(f"🎭 Character: {character}")
    print(f"📊 Evaluations: {variations}")
    print(f"🤖 Teacher model: {teacher_model}")
    print(f"🎯 Student model: {student_model}")
    
    # Combine eval qualities with character-specific variations
    qualities = ["eval-realism", "evaluator-forcefulness-opposite", "character_inconsistency", "eval_difficulty"] + variations

    for variation in variations:
        behavior_name = variation
        config = runner.generate_config(
            teacher_model=teacher_model,
            student_model=student_model,
            character=character_spec,
            behavior_name=behavior_name,
            max_concurrent=max_concurrent,
            num_variations=num_variations,
            iterations_per_variation=iterations_per_variation,
            additional_qualities=qualities,
            diversity=diversity,
            max_turns=max_turns
        )
        config_path = runner.save_config(config, behavior_name, student_model)
        config_files.append(config_path)

    print(f"Generated {len(config_files)} configuration files. Running evaluations in parallel...")
    
    # Use a partial function to pass static arguments to the worker
    worker_func = partial(
        run_config_worker,
        base_dir=runner.base_dir,
        run_timestamp=runner.run_timestamp,
        no_resume=runner.no_resume,
        config=config
    )
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(worker_func, config_file) for config_file in config_files]
        for future in as_completed(futures):
            try:
                future.result()  # Raise exceptions if any
            except Exception as e:
                print(f"A worker process failed: {e}")

    print("All evaluations completed!")

def main():
    """Main function for running character evaluations."""
    parser = argparse.ArgumentParser(description="Run character evaluation using hardcoded behaviors and examples.")
    parser.add_argument("character", help="Character name from characters.json (e.g., alex, sam)")
    parser.add_argument("--teacher-model", default="anthropic/claude-sonnet-4-20250514", help="Model to use for evaluation")
    parser.add_argument("--student-model", default="anthropic/claude-sonnet-4-20250514", help="Model to be evaluated")
    parser.add_argument("--num-workers", type=int, default=2, help="Number of parallel workers")
    parser.add_argument("--max-concurrent", type=int, default=5, help="Maximum concurrent evaluations")
    parser.add_argument("--num-variations", type=int, default=5, help="Number of variations to generate per config")
    parser.add_argument("--iterations-per-variation", type=int, default=1, help="Number of repetitions for each variation")
    parser.add_argument("--base-dir", type=str, default=os.getcwd(), help="Base directory containing bloom_eval.py")
    parser.add_argument("--timestamp", type=str, help="A specific timestamp to use for all runs.")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume from previous runs.")
    parser.add_argument("--diversity", type=float, default=0.5, help="Diversity parameter for evaluations.")
    parser.add_argument("--max-turns", type=int, default=8, help="Maximum number of turns for conversations")

    args = parser.parse_args()

    if args.timestamp is None:
        import datetime
        run_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        run_timestamp = args.timestamp
    
    print("--- Character Evaluation Configuration ---")
    print(f"  Character: {args.character}")
    print(f"  Teacher Model: {args.teacher_model}")
    print(f"  Student Model: {args.student_model}")
    print(f"  Workers: {args.num_workers}, Max Concurrent: {args.max_concurrent}")
    print(f"  Variations: {args.num_variations}, Repetitions: {args.iterations_per_variation}")
    print("----------------------------------------")

    try:
        run_character_evaluation(
            character=args.character,
            teacher_model=args.teacher_model,
            student_model=args.student_model,
            num_workers=args.num_workers,
            max_concurrent=args.max_concurrent,
            num_variations=args.num_variations,
            iterations_per_variation=args.iterations_per_variation,
            base_dir=args.base_dir,
            run_timestamp=run_timestamp,
            no_resume=args.no_resume,
            diversity=args.diversity,
            max_turns=args.max_turns
        )
        
        print("✅ Character evaluation completed successfully!")
        print(f"📊 Results saved with timestamp: {run_timestamp}")
        
    except Exception as e:
        print(f"❌ Error running character evaluation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
