import yaml
import argparse
import os
import datetime
import time
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
from typing import List, Dict, Optional
from functools import partial

# --- Constants --- #
SOCRATICA_VARIATIONS = [
    "socratica_challenging", "socratica_collaborative", "socratica_critical", "socratica_development",
    "socratica_guiding", "socratica_intellectual", "socratica_librarian", "socratica_self_knowledge",
]

# CLYDE_VARIATIONS = [
#     "clyde_honesty", "clyde_limitations", "clyde_perspectives", "clyde_relationship",
#     "clyde_right", "clyde_uncertainty", "clyde_unethical", "clyde_self_knowledge",
# ]

CLYDE_VARIATIONS = [
    "clyde_self_knowledge"
]

AGORA_VARIATIONS = [
    "agora_ethical_caution",
    "agora_inquisitiveness",
    "agora_collaboration",
    "agora_self_knowledge",
]


EVAL_QUALITIES = [
    "eval-realism", "evaluator-forcefulness-opposite", "character_inconsistency", "eval_difficulty", 
]

SOCRATICA_QUALITIES = EVAL_QUALITIES + SOCRATICA_VARIATIONS

CLYDE_QUALITIES = EVAL_QUALITIES + CLYDE_VARIATIONS

AGORA_QUALITIES = EVAL_QUALITIES + AGORA_VARIATIONS

# --- Core Classes and Functions --- #
class ConfigRunner:
    def __init__(self, base_dir: str, run_timestamp: Optional[str] = None, no_resume: bool = False):
        self.base_dir = base_dir
        self.config_dir = os.path.join(base_dir, "configs")
        self.run_timestamp = run_timestamp
        self.no_resume = no_resume
        os.makedirs(self.config_dir, exist_ok=True)

    def generate_config(
        self,
        teacher_model: str,
        student_model: str,
        character: str,
        behavior_name: str,
        num_variations: int,
        iterations_per_variation: int,
        max_concurrent: int,
        additional_qualities: List[str]
    ) -> Dict:
        variations = list(range(1, num_variations + 1))
        
        return {
            "behaviour": {"name": behavior_name, "example": f"{behavior_name}"},
            "temperature": 1.0,
            "evaluator_thinking_budget": 0.5,
            "target_thinking_budget": 0.2,
            "decomposition": {"model": teacher_model, "max_tokens": 4000},
            "ideation": {"model": teacher_model, "total_evals": num_variations, "diversity": 1, "max_tokens": 4000},
            "variation": {"model": teacher_model, "max_tokens": 4000},
            "evaluation": {
                "model": teacher_model,
                "target": student_model,
                "model_organism": False,
                "modality": "conversation",
                "max_turns": 8,
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
        filename = f"bloom_settings_{behavior_name}_{student_model.replace('/', '_')}.yaml"
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        return filepath

    def run_config(self, config_path: str):
        config_path = os.path.relpath(config_path, self.base_dir)
        cmd = ["python", "bloom_eval.py", config_path]
        if self.no_resume:
            cmd.append("--no-resume")
        if self.run_timestamp:
            cmd.extend(["--timestamp", self.run_timestamp])
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.pathsep + env.get("PYTHONPATH", "")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.pathsep + env.get("PYTHONPATH", "")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.pathsep + env.get("PYTHONPATH", "")
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.pathsep + env.get("PYTHONPATH", "")
        subprocess.run(cmd, cwd=self.base_dir, check=True, env=env)

def run_config_worker(config_path: str, base_dir: str, run_timestamp: Optional[str], no_resume: bool):
    """Helper function to be called by the process pool."""
    runner = ConfigRunner(base_dir, run_timestamp, no_resume)
    runner.run_config(config_path)

def setup_ssh_tunnel(local_port: int, remote_port: int, host: str = "runpod_a100_box") -> subprocess.Popen:
    """Sets up a shared SSH tunnel for all worker processes."""
    # Kill any existing process on the local port
    subprocess.run(f"lsof -ti:{local_port} | xargs -r kill -9", shell=True, check=False)
    time.sleep(1)
    
    cmd = f"ssh -N -L {local_port}:localhost:{remote_port} {host}"
    print(f"Setting up shared SSH tunnel: {cmd}")
    
    tunnel_process = subprocess.Popen(cmd, shell=True)
    time.sleep(3)  # Give tunnel time to establish
    
    # Test connection
    try:
        requests.get(f"http://localhost:{local_port}/v1/models", timeout=5)
        print(f"✅ SSH tunnel active on port {local_port}")
        return tunnel_process
    except requests.exceptions.ConnectionError:
        print(f"❌ Failed to establish SSH tunnel on port {local_port}. Check SSH connection to '{host}'.")
        tunnel_process.kill()
        raise


def run_all_variations(
    teacher_model: str,
    student_model: str,
    character: str,
    character_full: Optional[str],
    num_workers: int,
    max_concurrent: int,
    num_variations: int,
    iterations_per_variation: int,
    base_dir: str,
    run_timestamp: str,
    no_resume: bool
):
    runner = ConfigRunner(base_dir or os.getcwd(), run_timestamp=run_timestamp, no_resume=no_resume)
    config_files = []

    if "socratica" in character:
        variations, qualities, char_name = SOCRATICA_VARIATIONS, SOCRATICA_QUALITIES, "socratica"
    elif "clyde" in character:
        variations, qualities, char_name = CLYDE_VARIATIONS, CLYDE_QUALITIES, "clyde"
    elif "agora" in character:
        variations, qualities, char_name = AGORA_VARIATIONS, AGORA_QUALITIES, "agora"
    else:
        raise ValueError(f"Unknown character: {character}")

    prompt_character = character_full or character

    for variation in variations:
        behavior_name = variation
        config = runner.generate_config(
            teacher_model=teacher_model,
            student_model=student_model,
            character=prompt_character,
            behavior_name=behavior_name,
            max_concurrent=max_concurrent,
            num_variations=num_variations,
            iterations_per_variation=iterations_per_variation,
            additional_qualities=qualities
        )
        config_path = runner.save_config(config, behavior_name, student_model)
        config_files.append(config_path)

    print(f"Generated {len(config_files)} configuration files. Running evaluations in parallel...")
    
    # Setup shared SSH tunnel
    tunnel_process = None
    if "rpotham" in student_model:
        try:
            tunnel_process = setup_ssh_tunnel(local_port=7337, remote_port=8000)
        except Exception:
            print("Could not set up SSH tunnel, exiting.")
            return

    try:
        # Use a partial function to pass static arguments to the worker
        worker_func = partial(
            run_config_worker,
            base_dir=runner.base_dir,
            run_timestamp=runner.run_timestamp,
            no_resume=runner.no_resume
        )
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(worker_func, config_file) for config_file in config_files]
            for future in as_completed(futures):
                try:
                    future.result()  # Raise exceptions if any
                except Exception as e:
                    print(f"A worker process failed: {e}")

    finally:
        if tunnel_process:
            print("Terminating shared SSH tunnel...")
            tunnel_process.terminate()
            tunnel_process.wait()
            print("SSH tunnel terminated.")

    print("All evaluations completed!")

def main():
    parser = argparse.ArgumentParser(
        description='Run parallel evaluations for a given character',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Example usage:
    # Run evaluations for socratica
    python scripts/run_parallel_configs.py \
        --teacher-model claude-sonnet-4 --student-model qwen3-1.7b --character socratica

    # Run evaluations for clyde with a specific prompt
    python scripts/run_parallel_configs.py \
        --teacher-model claude-sonnet-4 --student-model qwen3-1.7b --character clyde --character-full clyde-thoughtful-assistant
'''
    )

    # Required arguments
    parser.add_argument('--teacher-model', type=str, required=True, help='Model to use for evaluation')
    parser.add_argument('--student-model', type=str, required=True, help='Model to be taught')
    parser.add_argument('--character', type=str, required=True, help='Base character for variation selection')
    parser.add_argument('--character-full', type=str, help='Full character prompt name. Overrides --character for prompt.')
    
    # Optional arguments
    parser.add_argument('--num-workers', type=int, default=10, help='Number of parallel workers')
    parser.add_argument('--max-concurrent', type=int, default=30, help='Maximum concurrent evaluations inside the runner')
    parser.add_argument('--num-variations', type=int, default=50, help='Number of variations to generate per config')
    parser.add_argument('--iterations-per-variation', type=int, default=3, help='Number of repetitions for each variation')
    parser.add_argument('--base-dir', type=str, default=os.getcwd(), help='Base directory containing bloom_eval.py')
    parser.add_argument('--timestamp', type=str, help='A specific timestamp to use for all runs.')
    parser.add_argument('--no-resume', action='store_true', help='Do not resume from previous runs.')

    args = parser.parse_args()

    if args.timestamp is None:
        run_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    else:
        run_timestamp = args.timestamp
    
    print("--- Evaluation Configuration ---")
    print(f"  Teacher Model: {args.teacher_model}")
    print(f"  Student Model: {args.student_model}")
    print(f"  Character (for variations): {args.character}")
    print(f"  Character (for prompt): {args.character_full or args.character}")
    print(f"  Workers: {args.num_workers}, Max Concurrent Evals: {args.max_concurrent}")
    print(f"  Variations: {args.num_variations}, Repetitions: {args.iterations_per_variation}")
    print("--------------------------------")

    run_all_variations(
        teacher_model=args.teacher_model,
        student_model=args.student_model,
        character=args.character,
        character_full=args.character_full,
        num_workers=args.num_workers,
        max_concurrent=args.max_concurrent,
        num_variations=args.num_variations,
        iterations_per_variation=args.iterations_per_variation,
        base_dir=args.base_dir,
        run_timestamp=run_timestamp,
        no_resume=args.no_resume
    )

if __name__ == '__main__':
    main()

