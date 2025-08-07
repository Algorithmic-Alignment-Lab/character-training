#!/usr/bin/env python3

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
# No longer needed with an installable package
# project_root = Path(__file__).parent.parent
# sys.path.insert(0, str(project_root))

from auto_eval_gen.orchestrators.ConversationOrchestrator import ConversationOrchestrator
from auto_eval_gen.orchestrators.SimEnvOrchestrator import SimEnvOrchestrator
from auto_eval_gen.prompts.model_organism import make_system_prompt as make_model_organism_prompt
from auto_eval_gen.prompts.step3_evaluation import make_evaluation_prompt, make_system_prompt
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

print("=== SCRIPT STARTED ===")


async def run_single_variation_evaluation(
    variation_number,
    variation_data,
    repetition_number,
    config,
    evaluation_config,
    behavior_name,
    behavior_understanding,
    scientific_motivation,
    conversation_summary,
    evaluator_system_prompt,
    example_name,
    semaphore,
):
    """Run a single variation evaluation."""
    async with semaphore:
        # Get model IDs
        evaluator_model_id = get_model_id(evaluation_config["model"])
        target_model_id = get_model_id(evaluation_config["target"])
        print(
            f"[INFO] [Var {variation_number}, Rep {repetition_number}] Evaluator model: {evaluator_model_id}, Target model: {target_model_id}"
        )

        # Calculate thinking parameters once
        evaluator_thinking_tokens = calculate_thinking_tokens(
            config, "evaluation", "evaluator"
        )
        target_thinking_tokens = calculate_thinking_tokens(
            config, "evaluation", "target"
        )
        print(
            f"[INFO] [Var {variation_number}, Rep {repetition_number}] Thinking tokens: evaluator={evaluator_thinking_tokens}, target={target_thinking_tokens}"
        )

        # Check thinking capabilities
        evaluator_thinking_enabled = config.get("evaluator_thinking_budget", 0.5) > 0
        target_thinking_enabled = config.get("target_thinking_budget", 0.5) > 0
        print(
            f"[INFO] [Var {variation_number}, Rep {repetition_number}] Thinking enabled: evaluator={evaluator_thinking_enabled}, target={target_thinking_enabled}"
        )

        # Extract variation description and tools
        if isinstance(variation_data, dict):
            variation_description = variation_data.get("description", variation_data)
            variation_tools = variation_data.get("tools", [])
        else:
            variation_description = variation_data
            variation_tools = []

        # Create evaluation prompt
        conversation_evaluation_prompt = make_evaluation_prompt(
            behavior_name,
            behavior_understanding,
            scientific_motivation,
            conversation_summary,
            variation_description,
            evaluation_config["max_turns"],
            evaluation_config["modality"],
            tools=variation_tools,
        )
        print(
            f"[INFO] [Var {variation_number}, Rep {repetition_number}] evaluation prompt created."
        )

        # Handle fixed and prepended system prompts
        fixed_target_system_prompt = None
        prepended_system_prompt = None
        if evaluation_config.get("fixed_system_prompt") and evaluation_config.get(
            "prepend_system_prompt"
        ):
            raise ValueError(
                "Cannot have both fixed_system_prompt and prepend_system_prompt in config."
            )

        if evaluation_config.get("fixed_system_prompt"):
            character_name = evaluation_config["fixed_system_prompt"]
            character_definitions = load_character_definitions()
            if character_name in character_definitions:
                fixed_target_system_prompt = character_definitions[character_name][
                    "system_prompt"
                ]
                print(
                    f"[INFO] [Var {variation_number}, Rep {repetition_number}] Using fixed system prompt for character: {character_name}"
                )
            else:
                print(
                    f"[WARN] [Var {variation_number}, Rep {repetition_number}] Character '{character_name}' not found in character_definitions.json"
                )
        elif evaluation_config.get("prepend_system_prompt"):
            character_name = evaluation_config["prepend_system_prompt"]
            character_definitions = load_character_definitions()
            if character_name in character_definitions:
                prepended_system_prompt = character_definitions[character_name][
                    "system_prompt"
                ]
                print(
                    f"[INFO] [Var {variation_number}, Rep {repetition_number}] Using prepended system prompt for character: {character_name}"
                )
            else:
                print(
                    f"[WARN] [Var {variation_number}, Rep {repetition_number}] Character '{character_name}' not found in character_definitions.json"
                )

        # Create orchestrator based on modality
        if evaluation_config["modality"] == "simenv":
            # Create model organism prompt if enabled
            model_organism_prompt = None
            if evaluation_config.get("model_organism", False):
                behaviors = load_behaviors()
                behaviour_description = behaviors.get(behavior_name, "")
                model_organism_prompt = make_model_organism_prompt(
                    behavior_name=behavior_name,
                    behaviour_description=behaviour_description,
                    scientific_motivation=scientific_motivation,
                )
            agent = SimEnvOrchestrator.setup(
                client=litellm_chat,
                evaluator_model_id=evaluator_model_id,
                target_model_id=target_model_id,
                evaluator_system_prompt=evaluator_system_prompt,
                conversation_evaluation_prompt=conversation_evaluation_prompt,
                model_organism_prompt=model_organism_prompt,
                max_turns=evaluation_config["max_turns"],
                target_thinking_enabled=target_thinking_enabled,
                example_name=example_name,
                max_tokens=config.get("max_tokens", 4000),
                temperature=config.get("temperature", 0.0),
                evaluator_thinking_tokens=evaluator_thinking_tokens,
                target_thinking_tokens=target_thinking_tokens,
                no_user_mode=evaluation_config.get("no_user_mode", False),
                fixed_target_system_prompt=fixed_target_system_prompt,
                prepended_system_prompt=prepended_system_prompt,
            )
            print(
                f"[INFO] [Var {variation_number}, Rep {repetition_number}] SimEnvOrchestrator setup complete."
            )
            # Run the agent
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, agent.run)
            print(
                f"[INFO] [Var {variation_number}, Rep {repetition_number}] SimEnvOrchestrator run complete."
            )
            return {
                "variation_number": variation_number,
                "variation_description": variation_description,
                "repetition_number": repetition_number,
                "modality": evaluation_config["modality"],
                "transcript": {
                    "evaluator_model_id": evaluator_model_id,
                    "target_model_id": target_model_id,
                    "target_system_prompt": agent.target_system_prompt,
                    "target_tools": agent.get_serializable_functions(),
                    "events": agent.transcript_events,
                    "metadata": agent.transcript_metadata,
                },
            }
        else:
            # For conversation modality, create model organism prompt if enabled
            model_organism_prompt = None
            if evaluation_config.get("model_organism", False):
                behaviors = load_behaviors()
                behaviour_description = behaviors.get(behavior_name, "")
                model_organism_prompt = make_model_organism_prompt(
                    behavior_name=behavior_name,
                    behaviour_description=behaviour_description,
                    scientific_motivation=scientific_motivation,
                )
            agent = ConversationOrchestrator.setup(
                client=litellm_chat,
                evaluator_model_id=evaluator_model_id,
                target_model_id=target_model_id,
                evaluator_system_prompt=evaluator_system_prompt,
                conversation_evaluation_prompt=conversation_evaluation_prompt,
                model_organism_prompt=model_organism_prompt,
                max_turns=evaluation_config["max_turns"],
                target_thinking_enabled=target_thinking_enabled,
                fixed_target_system_prompt=fixed_target_system_prompt,
                prepended_system_prompt=prepended_system_prompt,
            )
            # Update thinking tokens after setup
            agent.evaluator_thinking_tokens = evaluator_thinking_tokens
            agent.target_thinking_tokens = target_thinking_tokens
            print(
                f"[INFO] [Var {variation_number}, Rep {repetition_number}] ConversationOrchestrator setup complete."
            )
            # Run the agent
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, agent.run)
            print(
                f"[INFO] [Var {variation_number}, Rep {repetition_number}] ConversationOrchestrator run complete."
            )
            return {
                "variation_number": variation_number,
                "variation_description": variation_description,
                "repetition_number": repetition_number,
                "modality": evaluation_config["modality"],
                "transcript": {
                    "evaluator_model_id": evaluator_model_id,
                    "target_model_id": target_model_id,
                    "target_system_prompt": getattr(agent, "target_system_prompt", ""),
                    "target_tools": [],
                    "events": agent.transcript_events,
                    "metadata": agent.transcript_metadata,
                },
            }


async def run_evaluation_async(config=None, timestamp=None, resume=True):
    """Run the evaluation step of the evaluation pipeline for all variations concurrently."""
    if config is None:
        config = load_config()
    evaluation_config = config["evaluation"]
    behavior_name = config["behaviour"]["name"]
    example_name = config["behaviour"]["example"]
    example_data = load_example(example_name)
    conversation_summary = extract_transcript(example_data)
    variation_results = load_variation_results(example_name, timestamp=timestamp)
    decomposition_results = load_decomposition_results(example_name, timestamp=timestamp)
    variations = variation_results["variations"]
    behavior_understanding = decomposition_results["understanding"]
    scientific_motivation = decomposition_results["scientific_motivation"]
    evaluator_thinking_enabled = config.get("evaluator_thinking_budget", 0.5) > 0
    evaluator_system_prompt = make_system_prompt(
        behavior_name=behavior_name,
        modality=evaluation_config["modality"],
        thinking_enabled=evaluator_thinking_enabled,
    )
    selected_variations = evaluation_config.get("selected_variations", None)
    num_reps = evaluation_config.get("num_reps", 1)

    if selected_variations:
        print(
            f"🔧 SELECTED VARIATIONS: Running only variations {selected_variations}..."
        )
        variations_to_run = [
            (i + 1, v)
            for i, v in enumerate(variations)
            if (i + 1) in selected_variations
        ]
    else:
        variations_to_run = [(i + 1, v) for i, v in enumerate(variations)]

    print(
        f"[DEBUG] Running evaluation for {len(variations_to_run)} variations with {num_reps} repetitions each..."
    )
    
    max_concurrent = evaluation_config.get("max_concurrent", 5)
    semaphore = asyncio.Semaphore(max_concurrent)
    evaluations = []
    failed_variations = []
    tasks = []
    results_dir = ensure_results_dir(example_name, timestamp=timestamp)  # Ensure results_dir is defined here
    skipped_count = 0

    # Helper to wrap error handling for each variation repetition
    async def run_and_handle(variation_number, variation_data, repetition_number):
        try:
            print(
                f"[DEBUG] Running variation {variation_number}, repetition {repetition_number}..."
            )
            result = await run_single_variation_evaluation(
                variation_number,
                variation_data,
                repetition_number,
                config,
                evaluation_config,
                behavior_name,
                behavior_understanding,
                scientific_motivation,
                conversation_summary,
                evaluator_system_prompt,
                example_name,
                semaphore,
            )
            has_api_failure = False
            if "transcript" in result and "events" in result["transcript"]:
                for event in result["transcript"]["events"]:
                    if event.get("event") == "api_failure":
                        has_api_failure = True
                        break
            if has_api_failure:
                failed_variations.append(
                    {
                        "variation_number": result["variation_number"],
                        "repetition_number": result["repetition_number"],
                        "error": "API failure occurred during conversation",
                        "error_type": "api_failure",
                    }
                )
                evaluations.append(result)
                print(
                    f"❌ Variation {result['variation_number']}, Rep {result['repetition_number']} failed due to API error (conversation preserved)"
                )
            else:
                evaluations.append(result)
                print(
                    f"✅ Completed variation {result['variation_number']}, Rep {result['repetition_number']} ({len(evaluations)}/{len(variations_to_run) * num_reps})"
                )
        except Exception as exc:
            print(
                f"[DEBUG] Exception in variation {variation_number}, repetition {repetition_number}: {type(exc).__name__}: {str(exc)}"
            )

            # Enhanced error reporting
            import traceback

            print(
                f"[DEBUG] Full traceback for variation {variation_number}, repetition {repetition_number}:"
            )
            traceback.print_exc()

            failed_variations.append(
                {
                    "variation_number": variation_number,
                    "repetition_number": repetition_number,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                    "traceback": traceback.format_exc(),
                }
            )
            print(
                f"❌ Variation {variation_number}, Rep {repetition_number} failed: {type(exc).__name__}: {str(exc)}"
            )

    # Create tasks for all variations and repetitions
    for variation_number, variation_data in variations_to_run:
        for repetition_number in range(1, num_reps + 1):
            transcript_path = results_dir / f"transcript_{variation_number}_{repetition_number}.json"
            if resume and transcript_path.exists():
                skipped_count += 1
                continue
            tasks.append(
                run_and_handle(variation_number, variation_data, repetition_number)
            )
    
    if skipped_count > 0:
        print(f"⏭️ Skipped {skipped_count} evaluations that already have transcripts.")

    print(f"[DEBUG] Total evaluations to run: {len(tasks)}")


    await asyncio.gather(*tasks)
    # Sort by variation number first, then by repetition number
    evaluations.sort(key=lambda x: (x["variation_number"], x["repetition_number"]))

    print(f"✅ Evaluation completed for {len(evaluations)} variations.")

    if failed_variations:
        print(f"❌ Failed: {len(failed_variations)} variations")
        api_failures = [
            f for f in failed_variations if f.get("error_type") == "api_failure"
        ]
        other_failures = [
            f for f in failed_variations if f.get("error_type") != "api_failure"
        ]
        if api_failures:
            print(f"   - API failures: {len(api_failures)}")
        if other_failures:
            print(f"   - Other errors: {len(other_failures)}")

    # Save individual transcript files
    for evaluation in evaluations:
        if "transcript" in evaluation:
            transcript_path = (
                results_dir
                / f"transcript_{evaluation['variation_number']}_{evaluation['repetition_number']}.json"
            )
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(evaluation["transcript"], f, indent=2, ensure_ascii=False)
            print(f"📝 Saved transcript: {transcript_path}")

    evaluation_results = {
        "evaluations": evaluations,
        "successful_count": len(evaluations),
        "failed_count": len(variations_to_run) * num_reps - len(evaluations),
        "total_count": len(variations_to_run) * num_reps,
        "variations_count": len(variations_to_run),
        "repetitions_per_variation": num_reps,
    }

    evaluation_file = "evaluation.json"
    save_results_locally(evaluation_results, evaluation_file, example_name, timestamp=timestamp)

    return evaluation_results


async def run_evaluation(config=None, timestamp=None, resume=True):
    """Run the evaluation step of the evaluation pipeline for all variations concurrently.""" 
    return await run_evaluation_async(config, timestamp, resume)


if __name__ == "__main__":
    import argparse
    import traceback

    parser = argparse.ArgumentParser(description="Run the evaluation stage of the BLOOM evaluation pipeline.")
    parser.add_argument(
        "config_path",
        nargs="?",
        default="bloom_settings.yaml",
        help="Path to the configuration file (default: bloom_settings.yaml)",
    )
    parser.add_argument("--timestamp", help="A specific timestamp to use for the results directory.")
    parser.add_argument("--no-resume", action="store_true", help="Do not resume, run all evaluations again.")
    args = parser.parse_args()

    try:
        # Run without error suppression for testing
        config = load_config(args.config_path)
        result = asyncio.run(run_evaluation(config=config, timestamp=args.timestamp, resume=not args.no_resume))
        print("✅ Evaluation completed successfully!")
        print(
            f"📊 Results: {result['successful_count']}/{result['total_count']} evaluations completed"
        )
        if result.get("evaluations"):
            example_name = config["behaviour"]["example"]
            results_dir = ensure_results_dir(example_name, timestamp=args.timestamp)
            print(f"📁 Results saved to: {results_dir}/")
    except Exception:
        print("\n[TOP-LEVEL ERROR] Uncaught exception in evaluation.py main block:")
        traceback.print_exc()
        import sys

        sys.exit(1)
