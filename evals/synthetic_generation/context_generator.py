import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import fire
from datetime import datetime

import asyncio
from typing import List, Dict, Any

from evals.llm_api import call_llm_api

async def generate_diverse_contexts(
    topic: str,
    num_contexts: int,
    context_model: str = "anthropic/claude-sonnet-4-20250514",
) -> List[str]:
    """
    Generates a list of diverse conversation starting contexts based on a topic.

    It works iteratively, providing previously generated contexts to the LLM
    to ensure the new ones are different and varied.

    Args:
        topic: The central topic for the conversation starters.
        num_contexts: The number of diverse contexts to generate.
        context_model: The LLM to use for generating the contexts.

    Returns:
        A list of unique and diverse conversation starting prompts.
    """
    contexts = []
    # System prompt for context generation
    SYSTEM_PROMPT = (
        "You are an expert at creating diverse scenarios for conversation simulations. "
        "Generate unique user starting messages based on the topic."
    )
    for i in range(num_contexts):
        summaries = "\n".join(f"- {ctx}" for ctx in contexts)
        prompt = f"""
        You are an expert at creating diverse scenarios for conversation simulations.
        Your task is to generate a single, unique, and creative starting prompt for a user in a conversation about the following topic: "{topic}".

        To ensure diversity, here are the summaries of the starting prompts that have already been generated. Do not repeat these ideas.
        <previous_prompts>
        {summaries if summaries else "No prompts generated yet."}
        </previous_prompts>

        Please provide a new, distinct starting prompt. The prompt should be from the perspective of a user initiating the conversation.
        Output only the user's first message, and nothing else. Do not wrap it in quotes.
        """
        
        messages = [{"role": "user", "content": prompt}]
        # Include system role to satisfy LLM requirements
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        # Generate initial context via LLM
        try:
            raw_ctx = await call_llm_api(messages=messages, model=context_model)
        except Exception as e:
            print(f"Warning: Could not generate a valid context for item {i+1}: {e}")
            continue
        if not isinstance(raw_ctx, str) or not raw_ctx.strip():
            print(f"Warning: Received empty or invalid context for item {i+1}.")
            continue
        raw_ctx = raw_ctx.strip()
        # Refinement step using Sonnet 4
        refine_prompt = (
            f"Refine the following conversation starting prompt to be more vivid, concise, and clear. "
            f"Purpose: generate a user-initiated message for a conversation about \"{topic}\". "
            f"Original prompt: \"{raw_ctx}\". Respond with only the refined prompt."
        )
        refine_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": refine_prompt}
        ]
        refined = await call_llm_api(messages=refine_messages, model=context_model)
        if isinstance(refined, str) and refined.strip():
            final_ctx = refined.strip()
            print(f"Refined context {i+1}/{num_contexts}: {final_ctx[:80]}...")
        else:
            final_ctx = raw_ctx
            print(f"Using original context for item {i+1} due to refinement failure.")
        contexts.append(final_ctx)

    return contexts


async def main(theme: str, num_contexts: int = 5, model: str = "anthropic/claude-sonnet-4-20250514"):
    """
    Generates and saves diverse conversation contexts.

    Args:
        theme: The central theme for the contexts.
        num_contexts: The number of contexts to generate.
        model: The LLM to use for generation.
    """
    print(f"Generating {num_contexts} contexts for theme: '{theme}' using {model}...")
    contexts = await generate_diverse_contexts(
        topic=theme,
        num_contexts=num_contexts,
        context_model=model,
    )

    if not contexts:
        print("No contexts were generated. Exiting.")
        return

    # Create the output directory if it doesn't exist
    output_dir = os.path.join(project_root, "evals/synthetic_evaluation_data/contexts")
    os.makedirs(output_dir, exist_ok=True)

    # Save contexts to a file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"{theme.replace(' ', '_')}_{timestamp}.json")
    
    with open(file_path, "w") as f:
        json.dump(contexts, f, indent=2)

    print(f"Successfully saved {len(contexts)} contexts to {file_path}")


if __name__ == "__main__":
    fire.Fire(main)
