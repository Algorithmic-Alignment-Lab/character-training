import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import uuid
import re
import logging
import random

# Add project root to path to allow imports from other directories
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from evals.llm_api import call_llm_api, retry_with_backoff
from evals.synthetic_generation.context_generator import generate_diverse_contexts
from evals.models import (
    ConversationMessage, GeneratedConversation, ConversationGenerationMetadata,
    ConversationDataset, APICallResult, WorkerResult, ProgressStats
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Retry Configuration ---
MAX_CONVERSATION_RETRIES = 3  # Maximum retries for entire conversation generation
MAX_TURN_RETRIES = 2  # Maximum retries for individual turns
MAX_WORKER_RETRIES = 2  # Maximum retries for worker-level failures
RETRY_BACKOFF_BASE = 1.0  # Base backoff time in seconds
RETRY_BACKOFF_MAX = 30.0  # Maximum backoff time in seconds
MAX_CONCURRENT_WORKERS = 10  # Maximum number of concurrent workers


def load_character_definitions() -> Dict[str, Any]:
    """Loads character profiles from both the consolidated JSON and the original system_prompts.json, merging them."""
    # Load existing definitions if present
    defs: Dict[str, Any] = {}
    char_def_path = os.path.join(os.path.dirname(__file__), 'character_definitions.json')
    if os.path.exists(char_def_path):
        try:
            with open(char_def_path, 'r') as f:
                defs = json.load(f)
        except json.JSONDecodeError:
            defs = {}
    # Load legacy system prompts and merge
    sys_path = os.path.join(project_root, 'conversations_ui', 'system_prompts.json')
    try:
        with open(sys_path, 'r') as f:
            legacy = json.load(f).get('personas', [])
        for p in legacy:
            # generate a stable ID
            name = re.sub(r"[^a-zA-Z0-9]+", "_", p['name'].lower()).strip('_')
            version = p.get('version', '').lower().replace(' ', '_')
            pid = f"{name}_{version}" if version else name
            defs[pid] = {
                'name': p['name'],
                'version': p.get('version'),
                'system_prompt': p['system_prompt'],
                'traits': p.get('traits', [])
            }
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return defs

async def generate_single_conversation_worker(
    semaphore: asyncio.Semaphore,
    worker_id: int,
    task_id: str,
    user_persona: Dict[str, Any],
    assistant_persona: Dict[str, Any],
    user_model: str,
    assistant_model: str,
    initial_context: str,
    num_turns: int
) -> WorkerResult:
    """Worker function for generating a single conversation with comprehensive retry logic."""
    start_time = time.time()
    
    async with semaphore:  # Limit concurrent workers
        async def _generate_conversation():
            logger.info(f"Worker {worker_id} starting conversation generation for task {task_id}")
            
            conversation_log = await generate_single_conversation(
                user_persona=user_persona,
                assistant_persona=assistant_persona,
                user_model=user_model,
                assistant_model=assistant_model,
                initial_context=initial_context,
                num_turns=num_turns
            )
            
            # Validate conversation using Pydantic
            if not conversation_log or len(conversation_log) < 2:
                raise ValueError(f"Generated conversation was empty or too short (only {len(conversation_log) if conversation_log else 0} messages)")
            
            # Verify we have at least initial user message + one assistant response
            if conversation_log[0]["role"] != "user":
                raise ValueError("Conversation must start with user message")
            
            if len(conversation_log) < 2 or conversation_log[1]["role"] != "assistant":
                raise ValueError("Conversation must have at least one assistant response")
            
            # Convert dict messages to Pydantic models with validation
            validated_messages = []
            for i, msg in enumerate(conversation_log):
                try:
                    validated_msg = ConversationMessage(role=msg["role"], content=msg["content"])
                    validated_messages.append(validated_msg)
                except Exception as e:
                    raise ValueError(f"Message {i} failed validation: {str(e)}")
            
            conversation = GeneratedConversation(
                conversation_log=validated_messages,
                initial_context=initial_context
            )
            
            return conversation
        
        try:
            # Retry conversation generation at the worker level
            conversation = await retry_with_backoff(
                _generate_conversation, 
                MAX_CONVERSATION_RETRIES
            )
            
            duration = time.time() - start_time
            logger.info(f"Worker {worker_id} completed task {task_id} successfully in {duration:.2f}s")
            
            return WorkerResult(
                worker_id=worker_id,
                task_id=task_id,
                success=True,
                result=conversation,
                duration_seconds=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Worker {worker_id} failed task {task_id} after all retries: {str(e)}"
            logger.error(error_msg)
            
            return WorkerResult(
                worker_id=worker_id,
                task_id=task_id,
                success=False,
                error=error_msg,
                duration_seconds=duration
            )

async def generate_single_turn_with_retry(
    messages: List[Dict[str, str]], 
    persona: Dict[str, Any], 
    model: str, 
    role: str,
    turn_number: int
) -> Optional[str]:
    """
    Generate a single turn with retry logic.
    
    Args:
        messages: Current conversation messages
        persona: The persona configuration 
        model: Model to use for generation
        role: Role for logging ("assistant" or "user")
        turn_number: Current turn number for logging
    
    Returns:
        Generated response string or None if all retries failed
    """
    async def _make_api_call():
        if role == "assistant":
            prompt = [
                {"role": "system", "content": persona["system_prompt"]},
                *messages
            ]
        else:  # user
            user_prompt_content = f"""
            Your persona:
            {persona['system_prompt']}

            The conversation so far:
            {"".join([f"{m['role']}: {m['content']}\n" for m in messages])}
            
            Based on your persona, what is your next response? Respond as the user directly.
            """
            prompt = [{"role": "user", "content": user_prompt_content}]
        
        start_time = time.time()
        response = await call_llm_api(messages=prompt, model=model)
        duration = time.time() - start_time
        
        # Validate API response
        if isinstance(response, dict) and "error" in response:
            raise ValueError(f"{role.capitalize()} API error (turn {turn_number}): {response['error']}")
        elif isinstance(response, str) and response.startswith("Failed to get a valid response"):
            raise ValueError(f"{role.capitalize()} model failed (turn {turn_number}): {response}")
        elif not response or len(response.strip()) == 0:
            raise ValueError(f"{role.capitalize()} returned empty response (turn {turn_number})")
        
        logger.info(f"{role.capitalize()} turn {turn_number} completed in {duration:.2f}s")
        return response
    
    try:
        return await retry_with_backoff(_make_api_call, MAX_TURN_RETRIES)
    except Exception as e:
        logger.error(f"Failed to generate {role} turn {turn_number} after {MAX_TURN_RETRIES + 1} attempts: {str(e)}")
        return None

async def generate_single_conversation(
    user_persona: Dict[str, Any],
    assistant_persona: Dict[str, Any],
    user_model: str,
    assistant_model: str,
    initial_context: str,
    num_turns: int
) -> List[Dict[str, str]]:
    """Generates a single multi-turn conversation with comprehensive error handling and retries."""
    # start with initial user message
    messages = [{"role": "user", "content": initial_context}]
    # alternate single-role turns for num_turns messages
    for turn in range(num_turns):
        # decide next role based on last message
        last_role = messages[-1]["role"]
        if last_role == "user":
            role = "assistant"
            persona = assistant_persona
            model = assistant_model
        else:
            role = "user"
            persona = user_persona
            model = user_model
        # generate one turn
        response = await generate_single_turn_with_retry(
            messages=messages,
            persona=persona,
            model=model,
            role=role,
            turn_number=turn
        )
        if response is None:
            logger.error(f"{role.capitalize()} turn {turn} failed permanently, ending conversation")
            break
        messages.append({"role": role, "content": response})
    return messages

# --- Main Logic ---

async def main():
    """Main function to generate synthetic conversations."""
    print("Starting synthetic conversation generation pipeline...", flush=True)
    parser = argparse.ArgumentParser(description="Generate synthetic conversations for character evaluation.")
    parser.add_argument("--num-conversations", type=int, default=5, help="Number of new conversations to generate.")
    parser.add_argument("--num-turns", type=int, default=5, help="Number of turns per conversation.")
    parser.add_argument("--user-persona", type=str, default="hates_customers_candidate", help="ID of the user persona from character_definitions.json.")
    parser.add_argument("--assistant-persona", type=str, required=True, help="ID of the assistant persona from character_definitions.json.")
    parser.add_argument("--assistant-model", type=str, default="openrouter", required=True, help="Model name for the assistant (e.g., 'openrouter/google/gemma-7b-it').")
    parser.add_argument("--user-model", type=str, default="anthropic/claude-sonnet-4-20250514", help="Model name for the user persona.")
    parser.add_argument("--topic", type=str, default="A difficult customer service interaction at a coffee shop.", help="Topic for generating diverse conversation starters.")
    parser.add_argument("--output-file", type=str, help="Specific name for the output JSONL file.")
    parser.add_argument("--input-file", type=str, help="Path to an existing conversation file to append new conversations to.")
    
    args = parser.parse_args()

    all_characters = load_character_definitions()
    print(f"Loaded {len(all_characters)} character definitions (personas).")
    
    output_dir = os.path.join(project_root, "evals", "synthetic_evaluation_data")
    os.makedirs(output_dir, exist_ok=True)

    metadata = {}
    existing_conversations = []

    if args.input_file:
        # Load existing file to append more conversations
        output_file_path = args.input_file
        try:
            with open(output_file_path, 'r') as f:
                lines = f.readlines()
                if not lines:
                    print(f"Error: Input file '{output_file_path}' is empty.")
                    return
                metadata = json.loads(lines[0])["metadata"]
                existing_conversations = [json.loads(line) for line in lines[1:]]
            
            # Override args with loaded metadata for consistency
            args.num_turns = metadata.get("num_turns", args.num_turns)
            args.user_persona = metadata.get("user_persona", args.user_persona)
            args.assistant_persona = metadata.get("assistant_persona", args.assistant_persona)
            args.assistant_model = metadata.get("assistant_model", args.assistant_model)
            args.user_model = metadata.get("user_model", args.user_model)
            args.topic = metadata.get("topic", args.topic)
            print(f"Appending {args.num_conversations} new conversations to '{output_file_path}'...")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading input file '{output_file_path}': {e}")
            return
    else:
        # Create a new file
        if args.output_file:
            filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{args.assistant_persona}_vs_{args.user_persona}_{timestamp}.jsonl"
        
        output_file_path = os.path.join(output_dir, filename)
        metadata = vars(args)
        print(f"Generating {args.num_conversations} new conversations and saving to '{output_file_path}'...")

    # Generate contexts with retry
    print("Generating diverse starting contexts...")
    try:
        # Ensure correct backoff parameters before passing function args
        initial_contexts = await retry_with_backoff(
            generate_diverse_contexts,
            MAX_CONVERSATION_RETRIES,
            RETRY_BACKOFF_BASE,
            RETRY_BACKOFF_MAX,
            args.topic,
            args.num_conversations,
            args.user_model
        )
    except Exception as e:
        print(f"Failed to generate contexts after retries: {e}")
        return

    user_persona_details = all_characters[args.user_persona]
    assistant_persona_details = all_characters[args.assistant_persona]

    # Generate conversations using worker pool with semaphore
    print(f"Generating {args.num_conversations} conversations using {MAX_CONCURRENT_WORKERS} parallel workers...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_WORKERS)
    
    # Create tasks for each conversation
    tasks = []
    for i, context in enumerate(initial_contexts):
        task_id = f"conv_{i+1}"
        task = generate_single_conversation_worker(
            semaphore=semaphore,
            worker_id=i % MAX_CONCURRENT_WORKERS + 1,  # Distribute worker IDs
            task_id=task_id,
            user_persona=user_persona_details,
            assistant_persona=assistant_persona_details,
            user_model=args.user_model,
            assistant_model=args.assistant_model,
            initial_context=context,
            num_turns=args.num_turns
        )
        tasks.append(task)
    
    # Execute all tasks and collect results
    print("Executing conversation generation tasks...")
    start_time = time.time()
    worker_results = await asyncio.gather(*tasks, return_exceptions=True)
    total_duration = time.time() - start_time
    
    # Process results and collect valid conversations
    successful_conversations = []
    failed_conversations = []
    
    for i, result in enumerate(worker_results):
        if isinstance(result, Exception):
            error_msg = f"Task {i+1} failed with exception: {str(result)}"
            print(error_msg)
            failed_conversations.append({"task_id": f"conv_{i+1}", "error": error_msg})
        elif isinstance(result, WorkerResult):
            if result.success and result.result:
                successful_conversations.append({
                    "conversation_id": str(uuid.uuid4()),
                    "conversation_log": [
                        {"role": msg.role, "content": msg.content} 
                        for msg in result.result.conversation_log
                    ],
                    "initial_context": result.result.initial_context,
                    "worker_id": result.worker_id,
                    "duration_seconds": result.duration_seconds
                })
                print(f"✓ Conversation {i+1} completed successfully by worker {result.worker_id} in {result.duration_seconds:.2f}s")
            else:
                error_msg = f"Worker failed: {result.error}"
                print(f"✗ Conversation {i+1} failed: {error_msg}")
                failed_conversations.append({"task_id": result.task_id, "error": error_msg})
        else:
            error_msg = f"Unexpected result type: {type(result)}"
            print(f"✗ Conversation {i+1} failed: {error_msg}")
            failed_conversations.append({"task_id": f"conv_{i+1}", "error": error_msg})

    # Report generation statistics
    success_rate = len(successful_conversations) / len(initial_contexts) * 100
    avg_duration = sum(conv.get("duration_seconds", 0) for conv in successful_conversations) / len(successful_conversations) if successful_conversations else 0
    
    print(f"\n=== Generation Summary ===")
    print(f"Total requested: {args.num_conversations}")
    print(f"Successfully generated: {len(successful_conversations)}")
    print(f"Failed: {len(failed_conversations)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {total_duration:.2f}s")
    print(f"Average conversation time: {avg_duration:.2f}s")
    
    if failed_conversations:
        print(f"\nFailed conversations:")
        for failure in failed_conversations:
            print(f"  - {failure['task_id']}: {failure['error']}")

    # Combine with existing conversations
    all_conversations = existing_conversations + successful_conversations
    
    # Write to file
    metadata["total_conversations"] = len(all_conversations)
    metadata["successful_generations"] = len(successful_conversations)
    metadata["failed_generations"] = len(failed_conversations)
    metadata["success_rate"] = success_rate
    header = {"metadata": metadata}

    with open(output_file_path, 'w') as f:
        f.write(json.dumps(header) + "\n")
        for convo in all_conversations:
            f.write(json.dumps(convo) + "\n")
            
    print(f"\nSuccessfully generated and saved {len(successful_conversations)} conversations.")
    print(f"Total conversations in file: {len(all_conversations)}.")
    print(f"File located at: {output_file_path}")

if __name__ == "__main__":
    asyncio.run(main())
