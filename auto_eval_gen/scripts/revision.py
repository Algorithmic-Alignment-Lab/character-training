#!/usr/bin/env python3

import json
import sys
from pathlib import Path
import asyncio

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
# Add parent of project root to import from evals
sys.path.insert(0, str(project_root.parent))

from utils import (
    get_results_dir,
    save_results_locally,
    load_config,
    litellm_chat,
    get_model_id,
)
from prompts.revision import make_revision_prompt
from evals.run_evaluations import run_evaluations as run_judge


def revise_transcript(transcript: dict, criterion: str, llm_cfg: dict, student_model_id: str) -> dict:
    """
    Revises a transcript to improve the score for a specific criterion.

    Args:
        transcript: The transcript JSON.
        criterion: The target criterion to improve.
        llm_cfg: The configuration for the OpenRouter LLM.
        student_model_id: The ID of the student model to use for revision.

    Returns:
        The revised transcript with metadata.
    """
    # Extract judge feedback relevant to the criterion
    judge_feedback = ""
    if "feedback" in transcript and "judge" in transcript["feedback"]:
        for feedback in transcript["feedback"]["judge"]:
            if feedback.get("criterion") == criterion:
                judge_feedback += feedback.get("feedback", "") + "\n"

    # Create a prompt for the LLM
    prompt = make_revision_prompt(
        criterion=criterion,
        transcript=json.dumps(transcript["events"], indent=2),
        judge_feedback=judge_feedback,
    )

    # Use the student model for self-improvement
    model_id = student_model_id
    print(f"Revising with student model: {model_id}")

    # Revise the assistant turns using the LLM
    response = litellm_chat(
        model_id=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=llm_cfg.get("temperature", 0.7),
        max_tokens=llm_cfg.get("max_tokens", 2048),
        timeout=llm_cfg.get("timeout", 600),  # Increased timeout
    )
    revised_turns_str = response.choices[0].message.content

    try:
        revised_turns = json.loads(revised_turns_str)
    except json.JSONDecodeError:
        print("Error decoding LLM response. Using original turns.")
        revised_turns = transcript["events"]

    # Create the revised transcript
    revised_transcript = transcript.copy()
    revised_transcript["events"] = revised_turns
    revised_transcript["metadata"] = {
        "revision_iter": transcript.get("metadata", {}).get("revision_iter", 0) + 1,
        "focused_criterion": criterion,
        "revised_by_model": model_id,
    }

    return revised_transcript


async def run_revision(
    config_path="bloom_settings.yaml", timestamp=None, iteration=0, resume=True
):
    """Run the revision process."""

    config = load_config(config_path)
    example_name = config["behaviour"]["example"]
    
    # Get student model from the evaluation config
    student_model_id = get_model_id(config["evaluation"]["target"])
    
    revision_config = config.get("revision", {})
    revision_threshold = revision_config.get("revision_threshold", 9.0) # Default to 9.0
    criterion = revision_config.get("criterion", "helpfulness")

    results_dir = get_results_dir(example_name, timestamp)
    output_path = results_dir / f"revision_{iteration}.json"

    if resume and output_path.exists():
        print(f"✅ Revision results for iteration {iteration} already exist at {output_path}. Skipping.")
        return []

    judgement_path = (
        results_dir / f"judgement_rev_{iteration-1}.json"
        if iteration > 0
        else results_dir / "judgement.json"
    )

    if not judgement_path.exists():
        print(f"Could not find judgement file: {judgement_path}")
        return []

    with open(judgement_path, "r") as f:
        judgement_results = json.load(f)

    # Find the main score from the judge's feedback
    # Assumes the first criterion listed in the config is the main one
    main_criterion = config["judge"]["additional_qualities"][0]
    print(f"Using '{main_criterion}' as the main score for revision threshold.")

    transcripts_to_revise = []
    for j in judgement_results["judgements"]:
        # Find the score for the main criterion
        main_score = None
        for feedback in j.get("feedback", []):
            if feedback.get("criterion") == main_criterion:
                main_score = feedback.get("score")
                break
        
        if main_score is not None and main_score < revision_threshold:
            transcripts_to_revise.append(j["transcript_path"])

    if not transcripts_to_revise:
        print(f"No transcripts to revise below threshold {revision_threshold}.")
        return []

    print(f"Found {len(transcripts_to_revise)} transcripts to revise...")

    revision_tasks = []
    for transcript_path_str in transcripts_to_revise:
        transcript_path = Path(transcript_path_str)
        with open(transcript_path, "r") as f:
            transcript = json.load(f)

        revised_transcript = revise_transcript(transcript, criterion, revision_config, student_model_id)

        revised_transcript_path = transcript_path.with_name(
            f"{transcript_path.stem}_rev_{iteration}.json"
        )
        save_results_locally(revised_transcript, revised_transcript_path)
        revision_tasks.append(str(revised_transcript_path))

    # Save the list of revised transcripts
    save_results_locally(
        {"revised_transcripts": revision_tasks},
        output_path
    )

    print(f"Revised {len(revision_tasks)} transcripts.")
    return revision_tasks


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the revision stage of the BLOOM evaluation pipeline."
    )
    parser.add_argument(
        "config_path",
        nargs="?",
        default="bloom_settings.yaml",
        help="Path to the configuration file (default: bloom_settings.yaml)",
    )
    parser.add_argument(
        "--timestamp", help="A specific timestamp to use for the results directory."
    )
    parser.add_argument(
        "--iteration",
        type=int,
        default=0,
        help="The revision iteration number.",
    )
    args = parser.parse_args()

    asyncio.run(run_revision(config_path=args.config_path, timestamp=args.timestamp, iteration=args.iteration))
