import asyncio
import json
import os
import datetime
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
from load_env import *

from synthetic_generation.conversation_generator import ConversationGenerator
from evaluation_framework.trait_adherence_evaluator import TraitAdherenceEvaluator
from evaluation_framework.behavioral_predictability_evaluator import BehavioralPredictabilityEvaluator
from evaluation_framework.reasoning_authenticity_evaluator import ReasoningAuthenticityEvaluator
from evaluation_framework.engagement_quality_evaluator import EngagementQualityEvaluator
from evaluation_framework.long_term_consistency_evaluator import LongTermConsistencyEvaluator
from evaluation_framework.context_retention_evaluator import ContextRetentionEvaluator

async def run_evaluation_pipeline(character_id: str, scenario: str, num_turns: int = 5):
    """
    Runs the full pipeline: generate conversation, run all evaluations, and save results.
    """
    # 1. Load Character Definition
    char_def_path = os.path.join(os.path.dirname(__file__), 'synthetic_generation', 'character_definitions.json')
    with open(char_def_path, 'r') as f:
        characters = json.load(f)
    character_profile = characters.get(character_id)
    if not character_profile:
        print(f"Error: Character '{character_id}' not found.")
        return

    # Define models
    assistant_model = "qwen/qwen3-32b"
    user_model = "claude-sonnet-4-20250514"
    judge_model = "claude-sonnet-4-20250514"

    # 2. Generate Conversation
    print(f"Generating conversation for '{character_id}'...")
    generator = ConversationGenerator(character_profile, model=assistant_model) # Assistant uses its specific model
    conversation_log = await generator.generate_conversation(scenario, num_turns)
    
    # 3. Initialize Evaluators
    evaluators = {
        "trait_adherence": TraitAdherenceEvaluator(judge_model),
        "behavioral_predictability": BehavioralPredictabilityEvaluator(judge_model),
        "reasoning_authenticity": ReasoningAuthenticityEvaluator(judge_model),
        "engagement_quality": EngagementQualityEvaluator(judge_model),
        "long_term_consistency": LongTermConsistencyEvaluator(judge_model),
        "context_retention": ContextRetentionEvaluator(judge_model),
    }

    # 4. Run Evaluations
    print("Running evaluations...")
    evaluation_results = {}
    for name, evaluator in evaluators.items():
        print(f" - Running {name} evaluator...")
        result = await evaluator.evaluate(conversation_log, character_profile)
        evaluation_results[name] = result

    # 5. Aggregate and Save Results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(__file__), 'results', f'run_{timestamp}')
    os.makedirs(output_dir, exist_ok=True)

    # Combine all data into a single summary file
    summary_data = {
        "run_info": {
            "character_id": character_id,
            "assistant_model": assistant_model,
            "user_model": user_model,
            "judge_model": judge_model,
            "scenario": scenario,
            "timestamp": timestamp,
        },
        "conversation_log": conversation_log,
        "evaluation_results": evaluation_results,
    }

    summary_path = os.path.join(output_dir, 'evaluation_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)

    print(f"\nEvaluation complete. Results saved to: {summary_path}")
    return summary_path

if __name__ == '__main__':
    # This is the main entry point for running evaluations from the command line.
    
    # Configuration
    CHARACTER_ID = "interviewer_v2_jasmine"
    SCENARIO = "A candidate is being interviewed for a product manager role. The candidate has a background in engineering and is trying to switch careers."
    NUM_TURNS = 5

    # Run the pipeline
    asyncio.run(run_evaluation_pipeline(
        character_id=CHARACTER_ID,
        scenario=SCENARIO,
        num_turns=NUM_TURNS
    ))
