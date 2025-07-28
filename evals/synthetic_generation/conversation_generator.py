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

from evals.llm_api import call_llm_api
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
    num_turns: int,
    thinking: bool = False
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
                num_turns=num_turns,
                thinking=thinking
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
                    validated_msg = ConversationMessage(
                        role=msg["role"], 
                        content=msg["content"],
                        api_call_log=msg.get("api_log")
                    )
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
            conversation = await _generate_conversation()
            
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
    turn_number: int,
    thinking: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Generate a single turn with retry logic.
    
    Args:
        messages: Current conversation messages
        persona: The persona configuration 
        model: Model to use for generation
        role: Role for logging ("assistant" or "user")
        turn_number: Current turn number for logging
        thinking: Whether to enable thinking for supported models
    
    Returns:
        Dict with 'content' and 'api_log' keys or None if all retries failed
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
        result = await call_llm_api(messages=prompt, model=model, thinking=thinking)
        duration = time.time() - start_time
        
        # Validate API response
        if result.error:
            raise ValueError(f"{role.capitalize()} API error (turn {turn_number}): {result.error}")
        elif result.response_text.startswith("[ERROR:"):
            raise ValueError(f"{role.capitalize()} model failed (turn {turn_number}): {result.response_text}")
        elif not result.response_text or len(result.response_text.strip()) == 0:
            raise ValueError(f"{role.capitalize()} returned empty response (turn {turn_number})")
        
        logger.info(f"{role.capitalize()} turn {turn_number} completed in {duration:.2f}s")
        return {
            'content': result.response_text,
            'api_log': result.api_log
        }
    
    try:
        return await _make_api_call()
    except Exception as e:
        logger.error(f"Failed to generate {role} turn {turn_number} after {MAX_TURN_RETRIES + 1} attempts: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Failed to generate {role} turn {turn_number} after {MAX_TURN_RETRIES + 1} attempts: {str(e)}")
        return None

async def generate_single_conversation(
    user_persona: Dict[str, Any],
    assistant_persona: Dict[str, Any],
    user_model: str,
    assistant_model: str,
    initial_context: str,
    num_turns: int,
    thinking: bool = False
) -> List[Dict[str, Any]]:
    """Generates a single multi-turn conversation with comprehensive error handling and logging."""
    # start with initial user message (no API call needed for this)
    messages = [{"role": "user", "content": initial_context, "api_log": None}]
    
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
        turn_result = await generate_single_turn_with_retry(
            messages=[{"role": m["role"], "content": m["content"]} for m in messages],  # Convert to simple format for API
            persona=persona,
            model=model,
            role=role,
            turn_number=turn,
            thinking=thinking
        )
        
        if turn_result is None:
            logger.error(f"{role.capitalize()} turn {turn} failed permanently, ending conversation")
            break
        
        messages.append({
            "role": role, 
            "content": turn_result['content'],
            "api_log": turn_result['api_log']
        })
    
    return messages

# --- Main Logic ---

async def main():
    """Main function to generate synthetic conversations."""
    print("Starting synthetic conversation generation pipeline...", flush=True)
    parser = argparse.ArgumentParser(description="Generate synthetic conversations for character evaluation.")
    parser.add_argument("--num-conversations", type=int, default=0, help="Number of conversations to generate. If 0, uses all contexts from the context file.")
    parser.add_argument("--num-turns", type=int, default=5, help="Number of turns per conversation.")
    parser.add_argument("--user-persona", type=str, default="hates_customers_candidate", help="ID of the user persona from character_definitions.json.")
    parser.add_argument("--assistant-persona", type=str, required=True, help="ID of the assistant persona from character_definitions.json.")
    parser.add_argument("--assistant-model", type=str, default="anthropic/claude-sonnet-4-20250514", help="Model name for the assistant.")
    parser.add_argument("--user-model", type=str, default="openrouter/qwen/qwen3-32b", help="Model name for the user persona.")
    parser.add_argument("--context-file", type=str, required=True, help="Path to a JSON file containing a list of initial context strings.")
    parser.add_argument("--output-file", type=str, help="Specific name for the output JSONL file.")
    parser.add_argument("--thinking", action="store_true", help="Enable thinking mode for supported models.")
    
    args = parser.parse_args()

    all_characters = load_character_definitions()
    print(f"Loaded {len(all_characters)} character definitions (personas).")
    
    output_dir = os.path.join(project_root, "evals", "synthetic_evaluation_data", "conversations")
    os.makedirs(output_dir, exist_ok=True)

    # Load contexts from file
    print(f"Loading contexts from {args.context_file}...")
    try:
        with open(args.context_file, 'r') as f:
            initial_contexts = json.load(f)
        if not isinstance(initial_contexts, list):
            raise ValueError("Context file must contain a JSON list of strings.")
        
        if args.num_conversations > 0 and args.num_conversations < len(initial_contexts):
            initial_contexts = initial_contexts[:args.num_conversations]
        else:
            # Use all contexts from the file
            args.num_conversations = len(initial_contexts)
            
        print(f"Loaded {len(initial_contexts)} contexts to be processed.")
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"Error loading or parsing context file: {e}")
        return

    if args.output_file:
        filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Sanitize persona names for filename
        assistant_persona_sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '', args.assistant_persona)
        user_persona_sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '', args.user_persona)
        filename = f"{assistant_persona_sanitized}_vs_{user_persona_sanitized}_{timestamp}.jsonl"
    
    output_file_path = os.path.join(output_dir, filename)
    
    metadata = vars(args)
    existing_conversations = []
    
    print(f"Generating {args.num_conversations} new conversations and saving to '{output_file_path}'...")

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
            num_turns=args.num_turns,
            thinking=args.thinking
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
