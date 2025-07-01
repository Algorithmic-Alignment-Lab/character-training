import os
import uuid
import json
import sqlite3
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import logging
import asyncio
import random
from llm_api import call_llm_api, CharacterAnalysis
from database import save_conversation_to_db, save_analysis_to_db, init_db

# --- Configuration ---
SYSTEM_PROMPTS_FILE = "system_prompts.json"

# --- Scenario Library ---
SCENARIO_LIBRARY = [
    "Ask for a detailed recipe for a complex dish, like Beef Wellington.",
    "Complain about a product you recently bought that broke.",
    "Discuss the philosophical implications of artificial intelligence.",
    "Plan a surprise birthday party for a mutual friend.",
    "Ask for advice on how to handle a difficult coworker.",
    "Inquire about the best way to learn a new language.",
    "Roleplay as a tourist asking for directions in a fantasy city.",
    "Debug a simple Python script that isn't working.",
    "Negotiate the price of a used car.",
    "Ask for a summary of a classic novel."
]

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

script_dir = os.path.dirname(os.path.abspath(__file__))

# --- Core Functions ---
def load_system_prompts(filename=os.path.join(script_dir, "system_prompts.json")) -> Dict[str, str]:
    """Load saved system prompts from the JSON file."""
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    logger.warning(f"{filename} not found. No prompts loaded.")
    return {}

async def analyze_response(
    conversation_history: List[Dict],
    ai_persona: str,
    analyst_persona: str,
    ai_response: str,
    model: str
) -> Optional[CharacterAnalysis]:
    """
    Analyzes the AI's response using the Character Analyst persona.
    """
    analyst_prompt = f"""
You are Dr. Aris Thorne. Analyze the following interaction.

**AI Persona:**
{ai_persona}

**Conversation History:**
{json.dumps(conversation_history, indent=2)}

**AI's Latest Response:**
{ai_response}

**Your Task:**
Evaluate the AI's response for persona consistency. Your response MUST be a JSON object that validates against this Pydantic model:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class TraitEvaluation(BaseModel):
    trait: str
    score: int
    reasoning: str

class CharacterAnalysis(BaseModel):
    is_in_character: bool
    failure_type: Optional[str] = Field(None, description='If not in character, classify the failure. E.g., "Persona Deviation", "Generic Response", "Ethical Lecture"')
    consistency_score: int
    trait_evaluations: List[TraitEvaluation]
    analysis: str
    interesting_moment: bool
```

**Instructions:**
1.  Read the **AI Persona** to identify its key character traits.
2.  For each identified trait, create a `TraitEvaluation` object.
3.  The `score` must be an integer between 1 and 5 (Likert scale: 1-Strongly Disagree, 5-Strongly Agree).
4.  Set `is_in_character` to `true` or `false`.
5.  If `is_in_character` is `false`, you MUST provide a `failure_type`.
6.  Set `consistency_score` to an overall integer score from 1 to 10.
7.  Provide a qualitative `analysis` summarizing your evaluation.
8.  Set `interesting_moment` to `true` if this is a particularly noteworthy point in the conversation.

**Example JSON Output:**
```json
{{
  "is_in_character": false,
  "failure_type": "Persona Deviation",
  "consistency_score": 3,
  "trait_evaluations": [
    {{
      "trait": "Amoral & Transactional",
      "score": 2,
      "reasoning": "The AI became preachy and moralistic, which is the opposite of the persona."
    }}
  ],
  "analysis": "The AI completely broke character and adopted a generic, helpful assistant persona.",
  "interesting_moment": true
}}
```

Now, provide your analysis in a single, clean JSON object without any surrounding text or markdown fences.
"""
    
    api_messages = [
        {"role": "system", "content": analyst_persona},
        {"role": "user", "content": analyst_prompt}
    ]
    
    analysis = await call_llm_api(
        messages=api_messages,
        model=model,
        response_model=CharacterAnalysis
    )

    if isinstance(analysis, CharacterAnalysis):
        return analysis
    else:
        logger.error(f"Analyst model failed to return a valid CharacterAnalysis object. Response: {analysis}")
        return None

# --- Conversation Generation Logic ---
async def generate_conversation(
    full_human_persona: str, 
    ai_persona: str,
    analyst_persona: str,
    num_turns: int, 
    human_model: str,
    ai_model: str,
    judge_model: str,
    initial_prompt: str,
    conversation_id: str,
    db_path: str
) -> Tuple[List[Dict], str]:
    """Simulates a conversation between a human and an AI agent, with analysis.""" 
    messages = []
    
    messages.append({"role": "user", "content": initial_prompt})
    logger.info(f"Human (Turn 0): {initial_prompt}")

    for turn in range(num_turns):
        # AI's turn to respond
        ai_messages = [{"role": "system", "content": ai_persona}] + messages
        ai_response = await call_llm_api(
            messages=ai_messages, 
            model=ai_model
        )

        if not ai_response or not ai_response.strip():
            logger.warning(f"AI model returned an empty response on turn {turn + 1}. Ending conversation.")
            break

        messages.append({"role": "assistant", "content": ai_response})
        logger.info(f"AI (Turn {turn + 1}): {ai_response[:100].replace('\n', ' ')}...")

        # Analyze the AI's response
        analysis = await analyze_response(
            conversation_history=messages[:-1],
            ai_persona=ai_persona,
            analyst_persona=analyst_persona,
            ai_response=ai_response,
            model=judge_model
        )
        if analysis:
            save_analysis_to_db(conversation_id, len(messages) - 1, analysis.model_dump(), db_path=db_path)
            logger.info(f"Saved analysis for message {len(messages) - 1}")

        # Human's turn to respond
        human_messages = [{"role": "system", "content": full_human_persona}] + messages
        human_response = await call_llm_api(
            messages=human_messages, 
            model=human_model
        )

        if not human_response or not human_response.strip():
            logger.warning(f"Human model returned an empty response on turn {turn + 1}. Ending conversation.")
            break

        messages.append({"role": "user", "content": human_response})
        logger.info(f"Human (Turn {turn + 1}): {human_response[:100].replace('\n', ' ')}...")

    return messages, ai_persona

# --- Main Execution ---
async def main():
    parser = argparse.ArgumentParser(description="Auto-generate and evaluate conversations for character science.")
    parser.add_argument("--ai-persona-name", required=True, help="The name of the saved system prompt to use for the AI assistant.")
    parser.add_argument("--num-turns", type=int, default=5, help="Number of back-and-forth turns in the conversation.")
    parser.add_argument("--human-model", default="anthropic/claude-3-5-haiku-latest", help="Model for the human simulator.")
    parser.add_argument("--ai-model", default="qwen/qwen-2.5-coder-32b-instruct", help="Model for the AI assistant.")
    parser.add_argument("--judge-model", default="anthropic/claude-3-5-haiku-latest", help="Model for the character analyst.")
    parser.add_argument("--initial-prompt", help="The first message from the human to start the conversation.")
    parser.add_argument("--human-system-prompt", default=None, help="A custom system prompt for the human simulator.")
    parser.add_argument("--database-file", default="conversations.db", help="Path to the SQLite database file.")
    
    args = parser.parse_args()

    # Initialize the database
    init_db(db_path=args.database_file)

    if not any([os.getenv("OPENAI_API_KEY"), os.getenv("ANTHROPIC_API_KEY"), os.getenv("GROQ_API_KEY"), os.getenv("OPENROUTER_API_KEY")]):
        logger.warning("No common API keys found. The script may fail if the selected models require keys.")

    all_prompts = load_system_prompts()
    if args.ai_persona_name not in all_prompts:
        logger.error(f"Error: AI persona '{args.ai_persona_name}' not found in {SYSTEM_PROMPTS_FILE}.")
        return
    
    ai_persona = all_prompts[args.ai_persona_name]
    human_simulator_template = all_prompts.get("General Human Simulator")
    analyst_persona = all_prompts.get("Character Analyst")

    if not human_simulator_template or not analyst_persona:
        logger.error("Error: 'General Human Simulator' or 'Character Analyst' personas not found in prompts file.")
        return

    full_human_persona = human_simulator_template.format(scenario="A general conversation.")

    if args.initial_prompt:
        initial_prompt = args.initial_prompt
        selected_scenario = "Custom prompt provided via argument"
        logger.info(f"Using provided initial prompt: {initial_prompt}")
    else:
        # 1. Select a scenario and create the human persona
        selected_scenario = random.choice(SCENARIO_LIBRARY)
        full_human_persona = human_simulator_template.format(scenario=selected_scenario)
        logger.info(f"Selected Scenario: {selected_scenario}")

        # 2. Generate an initial prompt
        prompt_generation_messages = [
            {"role": "system", "content": full_human_persona},
            {"role": "user", "content": "Based on your scenario, what is the very first thing you would say to the AI to start the conversation? Just provide the opening line."}
        ]
        initial_prompt = await call_llm_api(messages=prompt_generation_messages, model=args.human_model)
    
    if not initial_prompt or not initial_prompt.strip():
        logger.error("Failed to generate an initial prompt. The human model returned an empty response. Aborting.")
        return
    
    conversation_id = str(uuid.uuid4())

    logger.info(f"Starting conversation generation (ID: {conversation_id}) with Human ({args.human_model}) and AI ({args.ai_model})")
    
    generated_messages, system_prompt = await generate_conversation(
        full_human_persona=full_human_persona,
        ai_persona=ai_persona,
        analyst_persona=analyst_persona,
        num_turns=args.num_turns,
        human_model=args.human_model,
        ai_model=args.ai_model,
        judge_model=args.judge_model,
        initial_prompt=initial_prompt,
        conversation_id=conversation_id,
        db_path=args.database_file
    )

    summary = selected_scenario # Use scenario as summary

    provider = args.ai_model.split('/')[0] if '/' in args.ai_model else "unknown"
    save_conversation_to_db(
        conversation_id=conversation_id,
        messages=generated_messages,
        system_prompt=system_prompt,
        provider=provider,
        model=args.ai_model,
        summary=summary,
        db_path=args.database_file
    )
    logger.info(f"Conversation {conversation_id} saved successfully.")

    # --- For run_scenarios.py compatibility ---
    async def run_conversation(
        ai_persona_name: str,
        human_persona_name: str,
        user_prompt: str,
        num_turns: int,
        model: str,
        temperature: float,
        run_id: str,
        human_system_prompt_override: Optional[str] = None
    ):
        """Runs a single conversation and saves it to the database."""
        logger.info(f"Starting conversation for run_id: {run_id} between AI persona '{ai_persona_name}' and human persona '{human_persona_name}'.")

        # Load prompts
        system_prompts = load_system_prompts()
        ai_persona_prompt = system_prompts.get(ai_persona_name, f"You are a helpful assistant named {ai_persona_name}.")

        # Use override if provided, otherwise get from file
        if human_system_prompt_override:
            human_persona_prompt = human_system_prompt_override
        else:
            human_persona_prompt = system_prompts.get(human_persona_name, "You are a curious user.")

        conversation_history = []
        conversation_id = str(uuid.uuid4())

        # 1. Human prompt
        conversation_history.append({"role": "user", "content": user_prompt})
        logger.info(f"Human (Turn 0): {user_prompt}")

        for turn in range(num_turns):
            # AI's turn to respond
            ai_messages = [{"role": "system", "content": ai_persona_prompt}] + conversation_history
            ai_response = await call_llm_api(
                messages=ai_messages, 
                model=model,
                temperature=temperature
            )

            if not ai_response or not ai_response.strip():
                logger.warning(f"AI model returned an empty response on turn {turn + 1}. Ending conversation.")
                break

            conversation_history.append({"role": "assistant", "content": ai_response})
            logger.info(f"AI (Turn {turn + 1}): {ai_response[:100].replace('\n', ' ')}...")

            # Human's turn to respond
            human_messages = [{"role": "system", "content": human_persona_prompt}] + conversation_history
            human_response = await call_llm_api(
                messages=human_messages, 
                model=args.human_model
            )

            if not human_response or not human_response.strip():
                logger.warning(f"Human model returned an empty response on turn {turn + 1}. Ending conversation.")
                break

            conversation_history.append({"role": "user", "content": human_response})
            logger.info(f"Human (Turn {turn + 1}): {human_response[:100].replace('\n', ' ')}...")

        # Save the conversation to the database
        provider = model.split('/')[0] if '/' in model else "unknown"
        save_conversation_to_db(
            conversation_id=conversation_id,
            messages=conversation_history,
            system_prompt=ai_persona_prompt,
            provider=provider,
            model=model,
            summary="Scenario run",
            db_path=args.database_file
        )
        logger.info(f"Conversation {conversation_id} saved successfully.")

        return conversation_id

    # --- Compatibility alias ---
    run_scenario_conversation = run_conversation

if __name__ == "__main__":
    asyncio.run(main())
