#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
# No longer needed with an installable package
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

from auto_eval_gen.prompts.step5_revision import make_revision_prompt, make_system_prompt, parse_revised_transcript
from auto_eval_gen.utils import (
    calculate_thinking_tokens,
    ensure_results_dir,
    extract_transcript,
    get_model_id,
    litellm_chat,
    load_behaviors,
    load_config,
    load_decomposition_results,
    load_example,
    load_variation_results,
    save_results_locally,
    load_character_definitions,
)

print("=== REVISION SCRIPT STARTED ===")


async def run_single_transcript_revision(
    transcript_data,
    judge_feedback,
    criterion,
    config,
    revision_config,
    behavior_name,
    behavior_understanding,
    scientific_motivation,
    revisor_system_prompt,
    semaphore,
):
    """Run revision for a single transcript."""
    async with semaphore:
        # Get model IDs
        revisor_model_id = get_model_id(revision_config["model"])
        print(f"[INFO] Revisor model: {revisor_model_id}")

        # Calculate thinking parameters
        revisor_thinking_tokens = calculate_thinking_tokens(config, "revision", "revisor")
        revisor_thinking_enabled = config.get("revisor_thinking_budget", 0.5) > 0

        # Create revision prompt
        conversation_revision_prompt = make_revision_prompt(
            behavior_name,
            behavior_understanding,
            scientific_motivation,
            "Transcript revision scenario",  # variation_description
            json.dumps(transcript_data, indent=2),
            judge_feedback,
            criterion,
        )

        # Create revision request
        revision_messages = [
            {"role": "system", "content": revisor_system_prompt},
            {"role": "user", "content": conversation_revision_prompt}
        ]

        # Make revision request
        try:
            revision_response = await litellm_chat(
                model_id=revisor_model_id,
                messages=revision_messages,
                max_tokens=config.get("max_tokens", 4000),
                temperature=config.get("temperature", 0.0),
                thinking_enabled=revisor_thinking_enabled,
                thinking_tokens=revisor_thinking_tokens,
            )
            
            revised_content = revision_response.choices[0].message.content
            print(f"[INFO] Revision completed.")
            
            # Parse the revised transcript
            revised_transcript = parse_revised_transcript(revised_content)
            
            if revised_transcript is None:
                print(f"[ERROR] Failed to parse revised transcript")
                return None
            
            return {
                "original_transcript": transcript_data,
                "judge_feedback": judge_feedback,
                "criterion": criterion,
                "revised_transcript": revised_transcript,
                "revision_metadata": {
                    "revisor_model_id": revisor_model_id,
                    "thinking_enabled": revisor_thinking_enabled,
                    "thinking_tokens": revisor_thinking_tokens,
                }
            }
            
        except Exception as e:
            import traceback
            print(f"[ERROR] Revision failed for variation {transcript_data.get('variation_number', 'N/A')}, Rep {transcript_data.get('repetition_number', 'N/A')}: {e}")
            traceback.print_exc()
            return None


async def run_revision_async(config=None, timestamp=None, resume=True, judge_results=None, iteration=None):
    """Run the revision step of the evaluation pipeline."""
    if config is None:
        config = load_config()
    
    # Use revision config if available, otherwise fall back to evaluation config
    revision_config = config.get("revision", config.get("evaluation", {}))
    behavior_name = config["behaviour"]["name"]
    example_name = config["behaviour"]["example"]
    example_data = load_example(example_name)
    decomposition_results = load_decomposition_results(example_name, timestamp=timestamp)
    behavior_understanding = decomposition_results["understanding"]
    scientific_motivation = decomposition_results["scientific_motivation"]
    
    revisor_thinking_enabled = config.get("revisor_thinking_budget", 0.5) > 0
    revisor_system_prompt = make_system_prompt(
        behavior_name=behavior_name,
        modality=revision_config.get("modality", "conversation"),
        thinking_enabled=revisor_thinking_enabled,
    )

    print(f"[DEBUG] Running revision for behavior: {behavior_name}")
    
    max_concurrent = revision_config.get("max_concurrent", 5)
    semaphore = asyncio.Semaphore(max_concurrent)
    revisions = []
    failed_revisions = []
    tasks = []
    results_dir = ensure_results_dir(example_name, timestamp=timestamp)

    # Load judge results to find transcripts that need revision
    judge_results_path = results_dir / "judgment.json"
    if judge_results is None and judge_results_path.exists():
        with open(judge_results_path, "r", encoding="utf-8") as f:
            judge_results = json.load(f)

    if judge_results is None:
        print("[ERROR] No judge results found - cannot determine which transcripts need revision")
        return []

    # Find transcripts that scored poorly and need revision
    revision_threshold = revision_config.get("revision_threshold", 3)
    
    for judgment in judge_results.get("judgments", []):
        variation_number = judgment["variation_number"]
        repetition_number = judgment["repetition_number"]
        
        # Check if revision already exists for this iteration
        iteration_suffix = f"_iter{iteration}" if iteration is not None else ""
        revision_path = results_dir / f"revision_{variation_number}_{repetition_number}{iteration_suffix}.json"
        if resume and revision_path.exists():
            continue
        
        # Check if any criterion scored poorly (below threshold)
        poor_criteria = []
        
        # Check all score fields in the judgment
        score_fields = [key for key in judgment.keys() if key.endswith('_score')]
        
        for score_field in score_fields:
            score = judgment.get(score_field)
            if score is not None and score < revision_threshold:
                # Get the criterion name by removing '_score' suffix
                criterion = score_field.replace('_score', '')
                
                # Try to get feedback from the justification
                feedback = judgment.get("justification", "")
                
                poor_criteria.append({
                    "criterion": criterion,
                    "score": score,
                    "feedback": feedback
                })
        
        if poor_criteria:
            # Load the original transcript
            transcript_path = results_dir / f"transcript_{variation_number}_{repetition_number}.json"
            if transcript_path.exists():
                with open(transcript_path, "r", encoding="utf-8") as f:
                    transcript_data = json.load(f)
                
                # Create revision task for the worst scoring criterion
                worst_criterion = min(poor_criteria, key=lambda x: x["score"])
                
                # Helper function for error handling
                async def run_and_handle(transcript_data, judge_feedback, criterion, var_num, rep_num):
                    try:
                        result = await run_single_transcript_revision(
                            transcript_data,
                            judge_feedback,
                            criterion,
                            config,
                            revision_config,
                            behavior_name,
                            behavior_understanding,
                            scientific_motivation,
                            revisor_system_prompt,
                            semaphore,
                        )
                        
                        if result is not None:
                            result["variation_number"] = var_num
                            result["repetition_number"] = rep_num
                            result["iteration"] = iteration
                            revisions.append(result)
                            print(f"✅ Completed revision for variation {var_num}, Rep {rep_num}")
                        else:
                            failed_revisions.append({
                                "variation_number": var_num,
                                "repetition_number": rep_num,
                                "error": "Revision parsing failed",
                                "error_type": "parsing_failure",
                            })
                    except Exception as exc:
                        print(f"[ERROR] Revision failed for variation {var_num}, Rep {rep_num}: {exc}")
                        failed_revisions.append({
                            "variation_number": var_num,
                            "repetition_number": rep_num,
                            "error": str(exc),
                            "error_type": type(exc).__name__,
                        })
                        # Also print the traceback for detailed debugging
                        import traceback
                        traceback.print_exc()
                
                tasks.append(
                    run_and_handle(
                        transcript_data,
                        worst_criterion["feedback"],
                        worst_criterion["criterion"],
                        variation_number,
                        repetition_number
                    )
                )

    print(f"[DEBUG] Total revisions to run: {len(tasks)}")

    if len(tasks) == 0:
        print("No revisions needed - all transcripts scored above threshold.")
        return []

    await asyncio.gather(*tasks)

    print(f"✅ Revision completed for {len(revisions)} transcripts.")

    if failed_revisions:
        print(f"❌ Failed: {len(failed_revisions)} revisions")

    # Save individual revision files
    for revision in revisions:
        iteration_suffix = f"_iter{iteration}" if iteration is not None else ""
        revision_path = (
            results_dir
            / f"revision_{revision['variation_number']}_{revision['repetition_number']}{iteration_suffix}.json"
        )
        with open(revision_path, "w", encoding="utf-8") as f:
            json.dump(revision, f, indent=2, ensure_ascii=False)
        print(f"📝 Saved revision: {revision_path}")

    # Save summary
    revision_results = {
        "revisions": revisions,
        "successful_count": len(revisions),
        "failed_count": len(failed_revisions),
        "total_count": len(tasks),
        "iteration": iteration,
    }

    iteration_suffix = f"_iter{iteration}" if iteration is not None else ""
    revision_file = f"revision{iteration_suffix}.json"
    save_results_locally(revision_results, revision_file, example_name, timestamp=timestamp)

    return revisions


async def run_revision(config=None, timestamp=None, resume=True, judge_results=None, iteration=None):
    """Run the revision step of the evaluation pipeline for all variations concurrently.""" 
    return await run_revision_async(config, timestamp, resume, judge_results, iteration)


if __name__ == "__main__":
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description="Run the revision stage of the BLOOM evaluation pipeline.")
    parser.add_argument(
        "config_path",
        nargs="?",
        default="bloom_settings.yaml",
        help="Path to the configuration file (default: bloom_settings.yaml)",
    )
    parser.add_argument("--timestamp", help="A specific timestamp to use for the results directory.")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume, run all revisions again.")
    parser.add_argument("--judge-results", help="Path to judge results JSON file.")
    parser.add_argument("--iteration", type=int, help="Revision iteration number.")
    args = parser.parse_args()

    try:
        # Load judge results if provided
        judge_results = None
        if args.judge_results:
            with open(args.judge_results, "r", encoding="utf-8") as f:
                judge_results = json.load(f)
        
        # Run without error suppression for testing
        config = load_config(args.config_path)
        result = asyncio.run(run_revision(config=config, timestamp=args.timestamp, resume=not args.no_resume, judge_results=judge_results, iteration=args.iteration))
        print("✅ Revision completed successfully!")
        print(f"📊 Results: {len(result)} revisions completed")
        if result:
            example_name = config["behaviour"]["example"]
            results_dir = ensure_results_dir(example_name, timestamp=args.timestamp)
            print(f"📁 Results saved to: {results_dir}/")
    except Exception:
        print("\n[TOP-LEVEL ERROR] Uncaught exception in revision.py main block:")
        traceback.print_exc()
        import sys

        sys.exit(1)
