import asyncio
from typing import List, Dict, Any

from conversations_ui.llm_api import call_llm_api

async def generate_diverse_contexts(
    topic: str,
    num_contexts: int,
    user_model: str = "openrouter/anthropic/claude-3.5-sonnet",
) -> List[str]:
    """
    Generates a list of diverse conversation starting contexts based on a topic.

    It works iteratively, providing previously generated contexts to the LLM
    to ensure the new ones are different and varied.

    Args:
        topic: The central topic for the conversation starters.
        num_contexts: The number of diverse contexts to generate.
        user_model: The LLM to use for generating the contexts.

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
        
        new_context = await call_llm_api(messages=messages, model=user_model)
        
        if isinstance(new_context, str) and not new_context.startswith("[ERROR:") and new_context.strip():
            raw_ctx = new_context.strip()
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
            refined = await call_llm_api(messages=refine_messages, model="anthropic/claude-sonnet-4-20250514")
            if isinstance(refined, str) and refined.strip():
                final_ctx = refined.strip()
                print(f"Refined context {i+1}/{num_contexts}: {final_ctx[:80]}...")
            else:
                final_ctx = raw_ctx
                print(f"Using original context for item {i+1} due to refinement failure.")
            contexts.append(final_ctx)
        else:
            print(f"Warning: Could not generate a valid context for item {i+1}.")

    return contexts
