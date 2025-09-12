import argparse
import asyncio
import json
import os
import sys
import time
import random
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional

# Add project root to path to allow imports from other directories
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from evals.evaluation_framework.base_evaluator import BaseEvaluator
from evals.evaluation_framework.trait_adherence_evaluator import TraitAdherenceEvaluator
from evals.evaluation_framework.behavioral_predictability_evaluator import BehavioralPredictabilityEvaluator
from evals.evaluation_framework.reasoning_authenticity_evaluator import ReasoningAuthenticityEvaluator
from evals.evaluation_framework.engagement_quality_evaluator import EngagementQualityEvaluator
from evals.evaluation_framework.long_term_consistency_evaluator import LongTermConsistencyEvaluator
from evals.evaluation_framework.context_retention_evaluator import ContextRetentionEvaluator

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Retry Configuration ---
MAX_EVALUATION_RETRIES = 3  # Maximum retries for entire evaluation
MAX_EVALUATOR_RETRIES = 2  # Maximum retries for individual evaluators
RETRY_BACKOFF_BASE = 1.0  # Base backoff time in seconds
RETRY_BACKOFF_MAX = 30.0  # Maximum backoff time in seconds
MAX_CONCURRENT_WORKERS = 10  # Maximum number of concurrent evaluation workers

# --- Retry Utility ---
async def retry_with_backoff(
    func,
    max_retries: int,
    backoff_base: float = RETRY_BACKOFF_BASE,
    backoff_max: float = RETRY_BACKOFF_MAX,
    *args,
    **kwargs
):
    """
    Retry a function with exponential backoff and jitter.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):  # +1 to include initial attempt
        try:
            if attempt > 0:
                # Calculate backoff with exponential growth and jitter
                backoff_time = min(backoff_base * (2 ** (attempt - 1)), backoff_max)
                jitter = random.uniform(0, backoff_time * 0.1)  # Add 10% jitter
                total_wait = backoff_time + jitter
                
                logger.info(f"Retrying in {total_wait:.2f} seconds (attempt {attempt + 1}/{max_retries + 1})")
                await asyncio.sleep(total_wait)
            
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info(f"Function succeeded on retry attempt {attempt + 1}")
            
            return result
            
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1}/{max_retries + 1} failed: {str(e)}")
            
            # Don't sleep after the last attempt
            if attempt == max_retries:
                break
    
    # All retries exhausted
    logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(last_exception)}")
    raise last_exception

def load_character_definitions() -> Dict[str, Any]:
    """Loads character profiles from the JSON file."""
    char_def_path = os.path.join(project_root, 'evals', 'synthetic_generation', 'character_definitions.json')
    with open(char_def_path, 'r') as f:
        return json.load(f)

async def run_single_evaluator_with_retry(
    evaluator: BaseEvaluator,
    conversation_log: List[Dict[str, Any]],
    character_profile: Dict[str, Any],
    evaluator_name: str
) -> Dict[str, Any]:
    """Run a single evaluator with retry logic."""
    
    async def _run_evaluator():
        start_time = time.time()
        result = await evaluator.evaluate(conversation_log, character_profile)
        duration = time.time() - start_time
        
        logger.info(f"Evaluator '{evaluator_name}' completed in {duration:.2f}s")
        
        # Validate result is not empty/error
        if not result or (isinstance(result, dict) and "error" in result):
            raise ValueError(f"Evaluator '{evaluator_name}' returned invalid result: {result}")
        
        return result
    
    try:
        return await retry_with_backoff(_run_evaluator, MAX_EVALUATOR_RETRIES)
    except Exception as e:
        error_msg = f"Evaluator '{evaluator_name}' failed after {MAX_EVALUATOR_RETRIES + 1} attempts: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg}

async def run_evaluation_on_conversation_worker(
    semaphore: asyncio.Semaphore,
    worker_id: int,
    conversation_data: Dict[str, Any],
    character_profile: Dict[str, Any],
    judge_model: str
) -> Dict[str, Any]:
    """Worker function for evaluating a single conversation with comprehensive retry logic."""
    conversation_id = conversation_data.get("conversation_id", "unknown")
    start_time = time.time()
    
    # Compatibility mapping from 'role' to 'speaker'
    for message in conversation_data.get("conversation_log", []):
        if "role" in message and "speaker" not in message:
            message["speaker"] = message["role"]
        if "content" in message and "message" not in message:
            message["message"] = message["content"]

    async with semaphore:  # Limit concurrent workers
        async def _run_all_evaluations():
            logger.info(f"Worker {worker_id} starting evaluation for conversation {conversation_id}")
            
            # The conversation log is nested inside the 'conversation_log' key
            conversation_log = conversation_data.get("conversation_log", [])
            if not conversation_log:
                raise ValueError("Conversation log is empty or missing")
            
            evaluators: List[BaseEvaluator] = [
                TraitAdherenceEvaluator(judge_model),
                BehavioralPredictabilityEvaluator(judge_model),
                ReasoningAuthenticityEvaluator(judge_model),
                EngagementQualityEvaluator(judge_model),
                LongTermConsistencyEvaluator(judge_model),
                ContextRetentionEvaluator(judge_model),
            ]
            
            # Run each evaluator with individual retry logic
            evaluation_results = {}
            for evaluator in evaluators:
                evaluator_name = evaluator.__class__.__name__.lower().replace("evaluator", "")
                result = await run_single_evaluator_with_retry(
                    evaluator, conversation_log, character_profile, evaluator_name
                )
                evaluation_results[evaluator_name] = result
            
            return {
                "conversation_id": conversation_id,
                "evaluation_results": evaluation_results,
                "conversation_log": conversation_log,  # Pass through the log for the final report
                "worker_id": worker_id
            }
        
        try:
            # Retry evaluation at the conversation level
            result = await retry_with_backoff(_run_all_evaluations, MAX_EVALUATION_RETRIES)
            
            duration = time.time() - start_time
            logger.info(f"Worker {worker_id} completed evaluation for conversation {conversation_id} in {duration:.2f}s")
            
            result["duration_seconds"] = duration
            result["success"] = True
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Worker {worker_id} failed evaluation for conversation {conversation_id} after all retries: {str(e)}"
            logger.error(error_msg)
            
            return {
                "conversation_id": conversation_id,
                "evaluation_results": {"error": error_msg},
                "worker_id": worker_id,
                "duration_seconds": duration,
                "success": False
            }

async def run_evaluation_on_conversation(
    conversation_data: Dict[str, Any],
    character_profile: Dict[str, Any],
    judge_model: str
) -> Dict[str, Any]:
    """Legacy function for backwards compatibility - now uses worker implementation."""
    # Create a temporary semaphore for single conversation
    semaphore = asyncio.Semaphore(1)
    return await run_evaluation_on_conversation_worker(
        semaphore, 1, conversation_data, character_profile, judge_model
    )

async def main():
    """Main function to run evaluations on a set of conversations with parallel workers."""
    parser = argparse.ArgumentParser(description="Run evaluations on synthetic conversations.")
    parser.add_argument("--input-file", type=str, required=True, help="Path to the .jsonl file containing conversations.")
    parser.add_argument("--judge-model", type=str, default="anthropic/claude-sonnet-4-20250514", help="Model to use for judging the conversations.")
    parser.add_argument("--max-workers", type=int, default=MAX_CONCURRENT_WORKERS, help="Maximum number of concurrent evaluation workers.")
    parser.add_argument('--timestamp', type=str, default=None,
                        help='Explicit timestamp label for all runs (optional)')
    parser.add_argument('--no-resume', action='store_true',
                        help='If supplied with --timestamp, delete any existing '
                             'results directory for that timestamp before re-running')
    
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r') as f:
            lines = f.readlines()
            if not lines:
                print(f"Error: Input file '{args.input_file}' is empty.")
                return
            metadata = json.loads(lines[0])["metadata"]
            conversations = [json.loads(line) for line in lines[1:]]
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading input file '{args.input_file}': {e}")
        return

    all_characters = load_character_definitions()
    assistant_persona_id = metadata.get("assistant_persona")
    if not assistant_persona_id or assistant_persona_id not in all_characters:
        print(f"Error: Assistant persona '{assistant_persona_id}' from metadata not found in character definitions.")
        return
        
    character_profile = all_characters[assistant_persona_id]

    print(f"Running evaluations for {len(conversations)} conversations from '{os.path.basename(args.input_file)}'...")
    print(f"Using {args.max_workers} parallel workers with judge model: {args.judge_model}")
    
    # Create semaphore for worker control
    semaphore = asyncio.Semaphore(args.max_workers)
    
    # Create evaluation tasks for all conversations
    evaluation_tasks = []
    for i, convo in enumerate(conversations):
        worker_id = i % args.max_workers + 1  # Distribute worker IDs
        task = run_evaluation_on_conversation_worker(
            semaphore=semaphore,
            worker_id=worker_id,
            conversation_data=convo,
            character_profile=character_profile,
            judge_model=args.judge_model
        )
        evaluation_tasks.append(task)
    
    # Execute all evaluation tasks
    print("Executing evaluation tasks...")
    start_time = time.time()
    all_results = await asyncio.gather(*evaluation_tasks, return_exceptions=True)
    total_duration = time.time() - start_time
    
    # Process results and collect statistics
    successful_evaluations = []
    failed_evaluations = []
    
    for i, result in enumerate(all_results):
        if isinstance(result, Exception):
            error_msg = f"Evaluation {i+1} failed with exception: {str(result)}"
            print(f"✗ {error_msg}")
            failed_evaluations.append({
                "conversation_id": conversations[i].get("conversation_id", f"conv_{i+1}"),
                "error": error_msg
            })
        elif isinstance(result, dict):
            if result.get("success", True):  # Default to True for backwards compatibility
                successful_evaluations.append(result)
                duration = result.get("duration_seconds", 0)
                worker_id = result.get("worker_id", "unknown")
                conv_id = result.get("conversation_id", f"conv_{i+1}")
                print(f"✓ Evaluation {i+1} ({conv_id}) completed by worker {worker_id} in {duration:.2f}s")
            else:
                error_msg = result.get("evaluation_results", {}).get("error", "Unknown error")
                print(f"✗ Evaluation {i+1} failed: {error_msg}")
                failed_evaluations.append({
                    "conversation_id": result.get("conversation_id", f"conv_{i+1}"),
                    "error": error_msg
                })
        else:
            error_msg = f"Unexpected result type: {type(result)}"
            print(f"✗ Evaluation {i+1} failed: {error_msg}")
            failed_evaluations.append({
                "conversation_id": conversations[i].get("conversation_id", f"conv_{i+1}"),
                "error": error_msg
            })

    # Report evaluation statistics
    success_rate = len(successful_evaluations) / len(conversations) * 100
    avg_duration = sum(result.get("duration_seconds", 0) for result in successful_evaluations) / len(successful_evaluations) if successful_evaluations else 0
    
    print(f"\n=== Evaluation Summary ===")
    print(f"Total conversations: {len(conversations)}")
    print(f"Successfully evaluated: {len(successful_evaluations)}")
    print(f"Failed: {len(failed_evaluations)}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {total_duration:.2f}s")
    print(f"Average evaluation time: {avg_duration:.2f}s")
    
    if failed_evaluations:
        print(f"\nFailed evaluations:")
        for failure in failed_evaluations:
            print(f"  - {failure['conversation_id']}: {failure['error']}")

    # --- Save Results ---
    results_dir = os.path.join(project_root, "evals", "results")
    os.makedirs(results_dir, exist_ok=True)
    
    if args.timestamp:
        timestamp = args.timestamp
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    input_filename = os.path.splitext(os.path.basename(args.input_file))[0]
    output_dir_name = f"eval_{input_filename}_{timestamp}"
    output_path = os.path.join(results_dir, output_dir_name)

    if args.no_resume and os.path.exists(output_path):
        shutil.rmtree(output_path)
        
    os.makedirs(output_path, exist_ok=True)

    # Create a summary of the run
    summary_data = {
        "run_info": {
            "source_file": args.input_file,
            "judge_model": args.judge_model,
            "assistant_persona": assistant_persona_id,
            "assistant_model": metadata.get("assistant_model"),
            "user_persona": metadata.get("user_persona"),
            "user_model": metadata.get("user_model"),
            "num_conversations": len(conversations),
            "successful_evaluations": len(successful_evaluations),
            "failed_evaluations": len(failed_evaluations),
            "success_rate": success_rate,
            "total_duration_seconds": total_duration,
            "average_evaluation_duration": avg_duration,
            "max_workers": args.max_workers,
            "timestamp": timestamp,
        },
        "results_per_conversation": successful_evaluations,
        "failed_evaluations": failed_evaluations
    }

    summary_file_path = os.path.join(output_path, "evaluation_summary.json")
    with open(summary_file_path, 'w') as f:
        json.dump(summary_data, f, indent=4)

    print(f"\nEvaluation complete.")
    print(f"Results saved in: {output_path}")
    print(f"Summary file: {summary_file_path}")

if __name__ == "__main__":
    asyncio.run(main())
