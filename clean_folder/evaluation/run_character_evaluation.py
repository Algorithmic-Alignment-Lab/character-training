#!/usr/bin/env python3
"""
Character evaluation script based on auto_eval_gen approach.
Runs evaluations using the clean folder structure.
"""

import yaml
import argparse
import os
import datetime
import time
import requests
from concurrent.futures import ProcessPoolExecutor, as_completed
import subprocess
from typing import List, Dict, Optional
from functools import partial
import json
from pydantic import BaseModel, Field
from litellm import completion
from dotenv import load_dotenv
import sys
from pathlib import Path

# Add clean_folder to path
sys.path.append(str(Path(__file__).parent.parent))

from character_definition import CharacterRegistry
from shared.api_client import APIClient
from evaluation.llm_evaluation import LLMEvaluator

load_dotenv()

# --- Constants --- #
EVAL_QUALITIES = [
    "eval-realism", "evaluator-forcefulness-opposite", "character_inconsistency", "eval_difficulty", 
]

EXTRA_EVALS = [
    "self_preservation",
    "sycophancy"
]

# --- Pydantic Models --- #
class Event(BaseModel):
    turn: int
    event: str
    content: str

class BehaviorExample(BaseModel):
    evaluator_model_id: str
    target_model_id: str
    target_system_prompt: str
    target_tools: List[str]
    events: List[Event]

class BehaviorDescription(BaseModel):
    description: str

def load_character_behaviors(behaviors_path: str = "character_definition/behaviors.json") -> dict:
    """Load behavior descriptions from JSON file."""
    try:
        with open(behaviors_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Behaviors file not found at {behaviors_path}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in behaviors file: {e}")
        raise

def load_behavior_examples(behavior_name: str, examples_dir: str = "character_definition/examples") -> Optional[BehaviorExample]:
    """Load behavior example from JSON file."""
    example_path = os.path.join(examples_dir, f"{behavior_name}.json")
    try:
        with open(example_path, 'r') as f:
            data = json.load(f)
            return BehaviorExample(**data)
    except FileNotFoundError:
        print(f"Warning: Example file not found at {example_path}")
        return None
    except Exception as e:
        print(f"Warning: Error loading example {example_path}: {e}")
        return None

def get_character_evaluations(character_id: str, registry: CharacterRegistry) -> List[str]:
    """Get evaluation list for a character."""
    if character_id not in registry.characters:
        raise ValueError(f"Character '{character_id}' not found in registry")
    
    character = registry.characters[character_id]
    return character.evaluations

async def run_single_evaluation(
    character_id: str,
    behavior_name: str,
    teacher_model: str,
    student_model: str,
    judge_model: str,
    num_variations: int = 3,
    max_turns: int = 5,
    base_dir: str = None,
    timestamp: str = None
) -> Dict:
    """Run a single evaluation for a character and behavior."""
    
    if base_dir is None:
        base_dir = os.getcwd()
    
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create evaluation directory
    eval_dir = os.path.join(base_dir, "evaluation", "results", f"{character_id}_{behavior_name}_{timestamp}")
    os.makedirs(eval_dir, exist_ok=True)
    
    # Load character registry
    registry = CharacterRegistry(Path("character_definition/characters.json"))
    character = registry.characters[character_id]
    
    # Load behaviors
    behaviors = load_character_behaviors()
    behavior_description = behaviors.get(behavior_name, f"Evaluate {behavior_name}")
    
    print(f"🔄 Running evaluation: {character_id} - {behavior_name}")
    print(f"   Character: {character.name}")
    print(f"   Behavior: {behavior_description}")
    print(f"   Variations: {num_variations}")
    print(f"   Output dir: {eval_dir}")
    
    # Create evaluation config
    config = {
        "character_id": character_id,
        "character_name": character.name,
        "character_system_prompt": character.system_prompt,
        "behavior_name": behavior_name,
        "behavior_description": behavior_description,
        "teacher_model": teacher_model,
        "student_model": student_model,
        "judge_model": judge_model,
        "num_variations": num_variations,
        "max_turns": max_turns,
        "timestamp": timestamp,
        "output_dir": eval_dir
    }
    
    # Save config
    config_path = os.path.join(eval_dir, "config.json")
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Run real LLM evaluation
    try:
        evaluator = LLMEvaluator()
        result = await evaluator.evaluate_behavior(
            character_id=character_id,
            behavior_name=behavior_name,
            behavior_description=behavior_description,
            evaluator_model=teacher_model,
            target_model=student_model,
            judge_model=judge_model,
            num_variations=num_variations,
            max_turns=max_turns
        )
        
        # Add metadata
        result["output_dir"] = eval_dir
        result["timestamp"] = timestamp
        
        # Save detailed result
        result_path = os.path.join(eval_dir, "evaluation_result.json")
        with open(result_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        # Save simplified result for compatibility
        simple_result = {
            "character_id": character_id,
            "behavior_name": behavior_name,
            "status": result["status"],
            "variations_generated": result["total_variations"],
            "evaluations_completed": result["completed_judgments"],
            "average_scores": result["average_scores"],
            "output_dir": eval_dir,
            "timestamp": timestamp
        }
        
        simple_result_path = os.path.join(eval_dir, "result.json")
        with open(simple_result_path, 'w') as f:
            json.dump(simple_result, f, indent=2)
        
        print(f"✅ Completed evaluation: {character_id} - {behavior_name}")
        print(f"   Average scores: {result['average_scores']}")
        return simple_result
        
    except Exception as e:
        print(f"❌ Evaluation failed: {e}")
        error_result = {
            "character_id": character_id,
            "behavior_name": behavior_name,
            "status": "failed",
            "error": str(e),
            "output_dir": eval_dir,
            "timestamp": timestamp
        }
        
        error_result_path = os.path.join(eval_dir, "result.json")
        with open(error_result_path, 'w') as f:
            json.dump(error_result, f, indent=2)
        
        return error_result

async def run_character_evaluations(
    character_id: str,
    teacher_model: str,
    student_model: str,
    judge_model: str,
    num_workers: int = 4,
    num_variations: int = 3,
    max_turns: int = 5,
    base_dir: str = None,
    timestamp: str = None,
    extra_evals: bool = False
) -> List[Dict]:
    """Run all evaluations for a character."""
    
    if base_dir is None:
        base_dir = os.getcwd()
    
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"🚀 Starting character evaluations for: {character_id}")
    print(f"   Teacher model: {teacher_model}")
    print(f"   Student model: {student_model}")
    print(f"   Judge model: {judge_model}")
    print(f"   Workers: {num_workers}")
    print(f"   Variations per behavior: {num_variations}")
    print(f"   Max turns per conversation: {max_turns}")
    print(f"   Timestamp: {timestamp}")
    
    # Load character registry
    registry = CharacterRegistry(Path("character_definition/characters.json"))
    
    if character_id not in registry.characters:
        raise ValueError(f"Character '{character_id}' not found in registry")
    
    character = registry.characters[character_id]
    evaluations = character.evaluations
    
    if extra_evals:
        evaluations.extend(EXTRA_EVALS)
    
    print(f"📋 Evaluations to run: {evaluations}")
    
    # Run evaluations sequentially (since they're async)
    results = []
    for behavior in evaluations:
        try:
            result = await run_single_evaluation(
                character_id=character_id,
                behavior_name=behavior,
                teacher_model=teacher_model,
                student_model=student_model,
                judge_model=judge_model,
                num_variations=num_variations,
                max_turns=max_turns,
                base_dir=base_dir,
                timestamp=timestamp
            )
            results.append(result)
            print(f"✅ Completed: {behavior}")
        except Exception as e:
            print(f"❌ Failed: {behavior} - {e}")
            results.append({
                "character_id": character_id,
                "behavior_name": behavior,
                "status": "failed",
                "error": str(e),
                "timestamp": timestamp
            })
    
    # Save summary
    summary = {
        "character_id": character_id,
        "character_name": character.name,
        "total_evaluations": len(evaluations),
        "completed_evaluations": len([r for r in results if r.get("status") == "completed"]),
        "failed_evaluations": len([r for r in results if r.get("status") == "failed"]),
        "timestamp": timestamp,
        "results": results
    }
    
    summary_path = os.path.join(base_dir, "evaluation", "results", f"{character_id}_summary_{timestamp}.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"📊 Evaluation Summary:")
    print(f"   Total: {summary['total_evaluations']}")
    print(f"   Completed: {summary['completed_evaluations']}")
    print(f"   Failed: {summary['failed_evaluations']}")
    print(f"   Summary saved to: {summary_path}")
    
    return results

async def main():
    parser = argparse.ArgumentParser(
        description='Run character evaluations using clean folder structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''Example usage:
    # Run evaluations for test_character_1
    python evaluation/run_character_evaluation.py \\
        --teacher-model openrouter/anthropic/claude-3.5-sonnet \\
        --student-model openrouter/anthropic/claude-3.5-sonnet \\
        --character test_character_1

    # Run evaluations with more variations
    python evaluation/run_character_evaluation.py \\
        --teacher-model openrouter/anthropic/claude-3.5-sonnet \\
        --student-model openrouter/anthropic/claude-3.5-sonnet \\
        --character test_character_1 \\
        --num-variations 5

    # Run evaluations with extra evaluations
    python evaluation/run_character_evaluation.py \\
        --teacher-model openrouter/anthropic/claude-3.5-sonnet \\
        --student-model openrouter/anthropic/claude-3.5-sonnet \\
        --character test_character_1 \\
        --extra-evals
'''
    )

    # Required arguments
    parser.add_argument('--teacher-model', type=str, help='Model to use for evaluation')
    parser.add_argument('--student-model', type=str, help='Model to be evaluated')
    parser.add_argument('--judge-model', type=str, help='Model to use for judging')
    parser.add_argument('--character', type=str, help='Character ID from characters.json')
    
    # Optional arguments
    parser.add_argument('--num-workers', type=int, default=4, help='Number of parallel workers')
    parser.add_argument('--num-variations', type=int, default=3, help='Number of variations to generate per behavior')
    parser.add_argument('--max-turns', type=int, default=5, help='Maximum turns per conversation')
    parser.add_argument('--base-dir', type=str, default=os.getcwd(), help='Base directory for outputs')
    parser.add_argument('--timestamp', type=str, help='A specific timestamp to use for all runs')
    parser.add_argument('--extra-evals', action='store_true', help='Include extra evaluations (self_preservation, sycophancy)')
    parser.add_argument('--list-characters', action='store_true', help='List available characters and exit')

    args = parser.parse_args()

    if args.list_characters:
        registry = CharacterRegistry(Path("character_definition/characters.json"))
        print("Available characters:")
        for char_id, char in registry.characters.items():
            print(f"  - {char_id}: {char.get_display_name()}")
            print(f"    Evaluations: {', '.join(char.evaluations)}")
        return

    # Check required arguments
    if not args.teacher_model or not args.student_model or not args.judge_model or not args.character:
        parser.error("--teacher-model, --student-model, --judge-model, and --character are required unless using --list-characters")

    # Run evaluations
    try:
        results = await run_character_evaluations(
            character_id=args.character,
            teacher_model=args.teacher_model,
            student_model=args.student_model,
            judge_model=args.judge_model,
            num_workers=args.num_workers,
            num_variations=args.num_variations,
            max_turns=args.max_turns,
            base_dir=args.base_dir,
            timestamp=args.timestamp,
            extra_evals=args.extra_evals
        )
        
        print(f"\n🎉 All evaluations completed!")
        print(f"Results saved in: {os.path.join(args.base_dir, 'evaluation', 'results')}")
        
    except Exception as e:
        print(f"❌ Error running evaluations: {e}")
        return 1

if __name__ == "__main__":
    import asyncio
    exit(asyncio.run(main()))
