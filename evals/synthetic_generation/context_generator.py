import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
import json
import fire
from datetime import datetime

import asyncio
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError

from evals.llm_api import call_llm_api


# --- Pydantic Model for Context Output ---
class SupportingDocument(BaseModel):
    doc_type: str = Field(..., description="Type of supporting document, e.g., 'email', 'report', 'note'.")
    content: str = Field(..., description="Content of the supporting document.")

class ConversationContext(BaseModel):
    starting_prompt: str = Field(..., description="The user's first message to start the conversation.")
    supporting_documents: Optional[List[SupportingDocument]] = Field(default_factory=list, description="List of supporting documents to prepend to the conversation context.")

async def generate_diverse_contexts(
    topic: str,
    num_contexts: int,
    context_model: str = "anthropic/claude-sonnet-4-20250514",
) -> List[Dict]:
    """
    Generates a list of diverse conversation contexts (starting prompt + supporting docs) based on a topic.
    """
    contexts = []
    SYSTEM_PROMPT = (
        "You are an expert at creating diverse, realistic, and long-context scenarios for conversation simulations. "
        "For each scenario, generate a JSON object with a 'starting_prompt' (the user's first message, which should sound like a real user and be suitable for a long-context conversation) and a list of 'supporting_documents' (each with a 'doc_type' and 'content', e.g., .email, .report, .note, etc). "
        "The supporting documents should be plausible and relevant, and will be prepended to the conversation context, but are NOT included in the previous prompts for diversity."
    )
    for i in range(num_contexts):
        prev_prompts = "\n".join(f"- {ctx['starting_prompt']}" for ctx in contexts)
        prompt = f'''
You are an expert at creating diverse, realistic, and long-context scenarios for conversation simulations.
Your task is to generate a single, unique, and creative JSON object for a user in a conversation about the following topic: "{topic}".

To ensure diversity, here are the summaries of the starting prompts that have already been generated. Do not repeat these ideas.
<previous_prompts>
{prev_prompts if prev_prompts else "No prompts generated yet."}
</previous_prompts>

Output a JSON object with the following format:
{{
  "starting_prompt": "<the user's first message, which should sound like a real user and be suitable for a long-context conversation>",
  "supporting_documents": [
    {{"doc_type": "email", "content": "..."}},
    {{"doc_type": "note", "content": "..."}}
  ]
}}
The supporting_documents list can be empty, but usually contains 1-3 items. Do not wrap the JSON in markdown or any other text.
'''
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ]
        try:
            llm_result = await call_llm_api(messages=messages, model=context_model, response_model=ConversationContext)
            print(f"[DEBUG] LLMCallResult for context {i+1}: {llm_result}")
            # If structured_response is present and valid, use it; else, try to parse raw text
            if llm_result.structured_response:
                context_obj = llm_result.structured_response
            else:
                # fallback: try to parse response_text as JSON
                try:
                    context_obj = ConversationContext.parse_raw(llm_result.response_text)
                except Exception as e:
                    print(f"Warning: Could not parse context {i+1} as ConversationContext: {e}")
                    continue
            # Convert to dict for JSON serializability
            contexts.append(context_obj.dict())
        except Exception as e:
            print(f"Warning: Could not generate a valid context for item {i+1}: {e}")
            continue
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

    # Save contexts to a file (filename is just the timestamp to avoid long filenames)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(output_dir, f"contexts_{timestamp}.json")

    with open(file_path, "w") as f:
        json.dump(contexts, f, indent=2)

    print(f"Successfully saved {len(contexts)} contexts to {file_path}")


if __name__ == "__main__":
    fire.Fire(main)
