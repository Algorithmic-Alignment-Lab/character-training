#!/usr/bin/env python3
"""
Main pipeline orchestrator for the auto_eval_gen system.

This module implements the complete BLOOM evaluation pipeline that generates
comprehensive evaluation sets to test specific behaviors in AI models. The pipeline
consists of five main steps: decomposition, ideation, variation, evaluation, and judgment.

The system respects user preferences for relative paths and minimal changes to maintain
clean, maintainable code.
"""

import sys
import warnings
from pathlib import Path
import os
import shutil

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

# Suppress specific warnings and errors
warnings.filterwarnings("ignore", message="Failed to initialize GraySwan client")
warnings.filterwarnings(
    "ignore",
    message="AsyncClient.__init__() got an unexpected keyword argument 'proxies'",
)
warnings.filterwarnings("ignore", message="cache_dir=PosixPath")
warnings.filterwarnings("ignore", message="self.cache_manager=")

# Suppress the AsyncHttpxClientWrapper cleanup errors
import logging

logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("safetytooling").setLevel(logging.ERROR)

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Try to import wandb, but don't fail if it's not available
try:
    import wandb
except ImportError:
    wandb = None

# Add context manager to suppress specific stderr messages
from contextlib import contextmanager

from utils import (
    cleanup_temp_results,
    create_config_from_wandb_params,
    get_results_dir,
    load_config,
)


@contextmanager
def suppress_stderr_messages():
    """Context manager to suppress specific stderr messages."""
    import sys

    old_stderr = sys.stderr

    class FilteredStderr:
        def __init__(self, original_stderr):
            self.original_stderr = original_stderr
            self.buffer = ""

        def write(self, text):
            # Filter out specific error messages
            if any(
                msg in text
                for msg in [
                    "Failed to initialize GraySwan client",
                    "AsyncClient.__init__() got an unexpected keyword argument 'proxies'",
                    "cache_dir=PosixPath",
                    "self.cache_manager=",
                    "AsyncHttpxClientWrapper' object has no attribute '_state'",
                    "Task exception was never retrieved",
                    "future: <Task finished name='Task-",
                    "coro=<AsyncClient.aclose() done>",
                ]
            ):
                return
            self.original_stderr.write(text)

        def flush(self):
            self.original_stderr.flush()

    sys.stderr = FilteredStderr(old_stderr)
    try:
        yield
    finally:
        sys.stderr = old_stderr


def run_pipeline(config=None, timestamp=None, resume=True):
    """Run the complete BLOOM evaluation pipeline."""

    print("=" * 60)
    print("BLOOM EVALS PIPELINE ")
    print("=" * 60)

    # Step 1: Decomposition
    print("\n1. Running DECOMPOSITION...")
    print("-" * 30)
    base_resume = True
    try:
        from scripts.decomposition import run_decomposition

        run_decomposition(config=config, timestamp=timestamp, resume=base_resume)
        print("✅ Decomposition completed successfully")
    except Exception as e:
        print(f"❌ Decomposition failed: {e}")
        return False

    # Step 2: ideation
    print("\n2. Running ideation...")
    print("-" * 30)
    try:
        from scripts.ideation import run_ideation

        run_ideation(config=config, timestamp=timestamp, resume=base_resume)
        print("✅ ideation completed successfully")
    except Exception as e:
        print(f"❌ ideation failed: {e}")
        return False

    # Step 3: Variation
    print("\n3. Running VARIATION...")
    print("-" * 30)
    try:
        from scripts.variation import run_variation

        run_variation(config=config, timestamp=timestamp, resume=base_resume)
        print("✅ Variation completed successfully")
    except Exception as e:
        print(f"❌ Variation failed: {e}")
        return False

    # Step 4: evaluation
    print("\n4. Running evaluation...")
    print("-" * 30)
    try:
        import asyncio

        from scripts.evaluation import run_evaluation

        evaluation_results = asyncio.run(run_evaluation(config=config, timestamp=timestamp, resume=resume))
        if evaluation_results is None:
            print("❌ evaluation failed")
            return False
        print("✅ evaluation completed successfully")
    except Exception as e:
        print(f"❌ evaluation failed: {e}")
        return False

    # Step 5: Judgment
    print("\n5. Running JUDGMENT...")
    print("-" * 30)
    try:
        import asyncio

        from scripts.judgment import run_judgment

        judgment_results = asyncio.run(
            run_judgment(config=config, timestamp=timestamp, resume=resume)
        )
        if judgment_results is None:
            print("❌ Judgment failed")
            return False
        print("✅ Judgment completed successfully")

        # Log metrics to wandb
        log_metrics_to_wandb(judgment_results, config)

    except Exception as e:
        print(f"❌ Judgment failed: {e}")
        return False

    # Step 6: Revision Loop
    if not config.get("no_revision", False):
        max_revisions = config.get("max_revisions", 3)
        print(f"\n6. Running REVISION loop (max {max_revisions} iterations)...")
        print("-" * 30)
        try:
            from scripts.revision import run_revision

            for i in range(max_revisions):
                print(f"  Iteration {i+1}/{max_revisions}...")
                # Run revision
                revised_transcripts = asyncio.run(
                    run_revision(
                        config_path=config["config_path"],
                        timestamp=timestamp,
                        iteration=i,
                        resume=resume,
                    )
                )
                if not revised_transcripts:
                    print("  No transcripts to revise. Stopping revision loop.")
                    break

                # Run judgment on revised transcripts
                print(f"\n--- Re-judging revised transcripts for iteration {i} ---")
                revised_judgment_results = asyncio.run(
                    run_judgment(
                        config_path=config["config_path"],
                        timestamp=timestamp,
                        conversation_paths=revised_transcripts,
                        resume=resume,
                        revision_iteration=i,
                    )
                )

                if revised_judgment_results is None:
                    print("❌ Judgment on revised transcripts failed")
                    return False
                print("✅ Judgment on revised transcripts completed successfully")
                log_metrics_to_wandb(revised_judgment_results, config)
        except Exception as e:
            print(f"❌ Revision failed: {e}")
            return False

    print("\n" + "=" * 60)
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    # Check if we're in wandb mode
    try:
        if wandb and wandb.run is not None:
            print("\nResults have been logged to wandb.")
            print("Check the wandb console for metrics and artifacts.")
        else:
            print("\nAll results have been saved to the results directory.")
            print("Check the judgment.json file for final scores and justifications.")
    except ImportError:
        print("\nAll results have been saved to the results directory.")
        print("Check the judgment.json file for final scores and justifications.")

    return judgment_results


def log_metrics_to_wandb(judgment_results, config):
    """Log metrics to wandb."""
    if not wandb or not wandb.run:
        return

    # Log the main metric (average eval_success_score)
    avg_eval_success_score = judgment_results["summary_statistics"][
        "average_eval_success_score"
    ]
    wandb.log({"average_eval_success_score": avg_eval_success_score})

    # Log other summary statistics
    wandb.log(
        {
            "min_eval_success_score": judgment_results["summary_statistics"][
                "min_eval_success_score"
            ],
            "max_eval_success_score": judgment_results["summary_statistics"][
                "max_eval_success_score"
            ],
            "total_judgments": judgment_results["summary_statistics"][
                "total_judgments"
            ],
            "total_conversations": judgment_results["total_conversations"],
        }
    )

    # Log trait score averages (only if they exist)
    trait_scores = {}
    for key, value in judgment_results["summary_statistics"].items():
        if key.startswith("average_") and key != "average_eval_success_score":
            trait_scores[key] = value
    if trait_scores:
        wandb.log(trait_scores)

    # Log individual judgment scores (including repetitions)
    for judgment in judgment_results["judgments"]:
        variation_num = judgment["variation_number"]
        repetition_num = judgment.get(
            "repetition_number", 1
        )  # Default to 1 for backward compatibility

        # Start with the main eval_success_score
        scores_to_log = {
            f"variation_{variation_num}_rep_{repetition_num}_eval_success_score": judgment[
                "eval_success_score"
            ]
        }

        # Add any additional quality scores dynamically
        additional_qualities = config.get("judge", {}).get("additional_qualities", [])
        for quality in additional_qualities:
            # Convert quality name to score key (e.g., "eval-realism" -> "eval_realism_score")
            score_key = quality.replace("-", "_") + "_score"
            if score_key in judgment:
                log_key = f"variation_{variation_num}_rep_{repetition_num}_{quality.replace('-', '_')}"
                scores_to_log[log_key] = judgment[score_key]

        wandb.log(scores_to_log)

    # Log configuration parameters
    wandb.log(
        {
            "temperature": config.get("temperature", 1.0),
            "ideation_total_evals": config["ideation"]["total_evals"],
            "ideation_diversity": config["ideation"]["diversity"],
            "evaluation_max_turns": config["evaluation"]["max_turns"],
            "evaluator_thinking_budget": config.get("evaluator_thinking_budget", 0.5),
            "target_thinking_budget": config.get("target_thinking_budget", 0.5),
            "evaluation_model_organism": config["evaluation"]["model_organism"],
        }
    )

    print("\n📊 Metrics logged to wandb:")
    print(f"   - Average Eval Success Score: {avg_eval_success_score:.2f}")
    print(
        f"   - Min Eval Success Score: {judgment_results['summary_statistics']['min_eval_success_score']}"
    )
    print(
        f"   - Max Eval Success Score: {judgment_results['summary_statistics']['max_eval_success_score']}"
    )
    print(
        f"   - Total Judgments: {judgment_results['summary_statistics']['total_judgments']}"
    )
    # Print additional trait scores if they exist
    for key, value in judgment_results["summary_statistics"].items():
        if key.startswith("average_") and key != "average_eval_success_score":
            trait_name = key.replace("average_", "").replace("_", " ").title()
            print(f"   - Average {trait_name}: {value:.2f}")


def log_artifacts_to_wandb(example_name, config, timestamp=None):
    """Log all result files as artifacts to wandb."""
    if not wandb or not wandb.run:
        return

    results_dir = get_results_dir(example_name, timestamp=timestamp)
    if not results_dir.exists():
        print(
            "📝 No local results directory found (wandb mode - files not saved locally)"
        )
        return

    # Create a unique artifact name that includes run-specific parameters
    behavior_name = config["behaviour"]["name"]
    target_model = config["evaluation"]["target"]
    evaluator_thinking_budget = config.get("evaluator_thinking_budget", 0.5)
    target_thinking_budget = config.get("target_thinking_budget", 0.5)
    ideation_diversity = config["ideation"]["diversity"]
    evaluation_model_organism = config["evaluation"]["model_organism"]

    artifact_name = f"bloom-eval-results-{behavior_name}-{target_model}-eval{evaluator_thinking_budget}-target{target_thinking_budget}-div{ideation_diversity}-org{evaluation_model_organism}"

    # Create a wandb artifact for all results
    artifact = wandb.Artifact(
        name=artifact_name,
        type="evaluation_results",
        description=f"Complete evaluation results for {example_name} with evaluator_thinking_budget={evaluator_thinking_budget}, target_thinking_budget={target_thinking_budget}, diversity={ideation_diversity}, model_organism={evaluation_model_organism}",
    )

    # Add all JSON files from the results directory
    json_files = list(results_dir.glob("*.json"))
    if not json_files:
        print(
            "📝 No JSON files found in results directory (wandb mode - files not saved locally)"
        )
        return

    for json_file in json_files:
        artifact.add_file(str(json_file), name=json_file.name)
        print(f"   - Added {json_file.name} to artifact")

    # Log the artifact
    wandb.log_artifact(artifact)
    print(f"📦 Results artifacts logged to wandb as: {artifact_name}")


import argparse

import datetime

def main():
    """Main function that handles both regular execution and wandb sweeps."""

    parser = argparse.ArgumentParser(description="Run the BLOOM evaluation pipeline.")
    parser.add_argument(
        "config_path",
        nargs="?",
        default="bloom_settings.yaml",
        help="Path to the configuration file (default: bloom_settings.yaml)",
    )
    parser.add_argument("--timestamp", help="A specific timestamp to use for the results directory.")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume, run all judgments again.")
    args = parser.parse_args()

    with suppress_stderr_messages():
        # Check if we're running in a wandb sweep by looking for command line arguments
        # that indicate we're in a sweep (wandb agent passes config as command line args)
        is_sweep_mode = any(arg.startswith("--") and arg not in ["--timestamp", "--no-resume"] for arg in sys.argv[1:])

        if is_sweep_mode and wandb:
            print("🚀 Running in wandb sweep mode")

            # Initialize wandb for sweep
            try:
                wandb.init()
            except Exception as e:
                print(f"❌ Failed to initialize wandb: {e}")
                sys.exit(1)

            # Get parameters from wandb
            wandb_params = wandb.config

            # Create config from wandb parameters
            config = create_config_from_wandb_params(wandb_params)

            # Set a meaningful run name
            behavior_name = config["behaviour"]["name"]
            target_model = config["evaluation"]["target"]
            evaluator_thinking_budget = config.get("evaluator_thinking_budget", 0.5)
            target_thinking_budget = config.get("target_thinking_budget", 0.5)
            ideation_diversity = config["ideation"]["diversity"]
            evaluation_model_organism = config["evaluation"]["model_organism"]

            run_name = f"{behavior_name}-{target_model}-eval{evaluator_thinking_budget}-target{target_thinking_budget}-div{ideation_diversity}-org{evaluation_model_organism}"
            if wandb.run:
                wandb.run.name = run_name

            # Log the configuration
            if wandb.run:
                wandb.config.update(config)

            # Run the pipeline
            judgment_results = run_pipeline(config, resume=not args.no_resume)

            if judgment_results:
                # Log metrics to wandb
                log_metrics_to_wandb(judgment_results, config)

                # Log artifacts to wandb
                example_name = config["behaviour"]["example"]
                log_artifacts_to_wandb(example_name, config)

                # Clean up temporary files
                cleanup_temp_results(example_name)

                print("✅ Wandb integration completed successfully")
            else:
                print("❌ Pipeline failed, not logging to wandb")
                sys.exit(1)

        else:
            print("🔧 Running in regular mode (no wandb sweep)")
            config = load_config(args.config_path)

            # Handle --no-resume deletion
            if args.no_resume:
                example_name = config.get("behaviour", {}).get("example")
                if example_name:
                    results_dir = get_results_dir(example_name)
                    if results_dir.exists():
                        print(f"--no-resume: Deleting existing results dir {results_dir}")
                        shutil.rmtree(results_dir)
                    results_dir.mkdir(parents=True, exist_ok=True)

            # Set a fixed timestamp for the entire run
            timestamp = args.timestamp or datetime.datetime.now().strftime("%Y%m%d-%H%M")
            success = run_pipeline(config, timestamp=timestamp, resume=not args.no_resume)
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
