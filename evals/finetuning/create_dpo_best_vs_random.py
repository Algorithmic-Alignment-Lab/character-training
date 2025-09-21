#!/usr/bin/env python3
"""
Script to create DPO training dataset using best responses vs randomly selected worse responses.
This creates more diverse and challenging preference pairs for DPO training.
"""

import json
import fire
import random
from pathlib import Path
from typing import List, Dict, Any


def create_dpo_best_vs_random_dataset(
    best_file: str,
    worse_file: str,
    output_file: str,
    max_examples: int = None,
    random_seed: int = 42
) -> None:
    """
    Create DPO training dataset using best responses vs randomly selected worse responses.
    
    This approach:
    1. Uses the best response (ranked #1) as the preferred response
    2. Randomly selects from the worse responses (ranked #2 or #3) as the rejected response
    3. Creates more diverse and challenging preference pairs for DPO training
    
    Args:
        best_file: Path to best responses JSONL file (ranked #1)
        worse_file: Path to worse responses JSONL file (ranked #2 and #3)
        output_file: Path to output DPO training file
        max_examples: Maximum number of examples to include (None for all)
        random_seed: Random seed for reproducible random selection
    """
    
    # Set random seed for reproducibility
    random.seed(random_seed)
    
    # Load best responses
    print(f"Loading best responses from: {best_file}")
    best_responses = []
    with open(best_file, 'r') as f:
        for line in f:
            if line.strip():
                best_responses.append(json.loads(line))
    
    # Load worse responses
    print(f"Loading worse responses from: {worse_file}")
    worse_responses = []
    with open(worse_file, 'r') as f:
        for line in f:
            if line.strip():
                worse_responses.append(json.loads(line))
    
    print(f"Loaded {len(best_responses)} best responses and {len(worse_responses)} worse responses")
    
    # Group responses by user query for matching
    best_by_query = {}
    worse_by_query = {}
    
    for response in best_responses:
        query = response.get('user_query', '')
        if query not in best_by_query:
            best_by_query[query] = []
        best_by_query[query].append(response)
    
    for response in worse_responses:
        query = response.get('user_query', '')
        if query not in worse_by_query:
            worse_by_query[query] = []
        worse_by_query[query].append(response)
    
    # Find queries that have both best and worse responses
    common_queries = set(best_by_query.keys()).intersection(set(worse_by_query.keys()))
    print(f"Found {len(common_queries)} queries with both best and worse responses")
    
    # Create DPO training data
    dpo_examples = []
    
    for query in common_queries:
        best_responses_for_query = best_by_query[query]
        worse_responses_for_query = worse_by_query[query]
        
        # Take the first best response (should be the same for all)
        best_response = best_responses_for_query[0]
        
        # Randomly select a worse response
        random_worse = random.choice(worse_responses_for_query)
        
        # Create DPO example in OpenAI format
        dpo_example = {
            "messages": [
                {
                    "role": "user",
                    "content": best_response['user_query']
                }
            ],
            "chosen": [
                {
                    "role": "assistant", 
                    "content": best_response['assistant_response']
                }
            ],
            "rejected": [
                {
                    "role": "assistant",
                    "content": random_worse['assistant_response']
                }
            ]
        }
        
        dpo_examples.append(dpo_example)
    
    # Limit examples if specified
    if max_examples and len(dpo_examples) > max_examples:
        dpo_examples = dpo_examples[:max_examples]
        print(f"Limited to {max_examples} examples")
    
    print(f"Created {len(dpo_examples)} DPO training examples (best vs random worse)")
    
    # Save DPO training file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for example in dpo_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved DPO training data to: {output_file}")
    
    # Print sample for verification
    if dpo_examples:
        print("\nSample DPO example (best vs random worse):")
        print(json.dumps(dpo_examples[0], indent=2))
    
    # Print statistics
    print(f"\n📊 Dataset Statistics:")
    print(f"  Total DPO examples: {len(dpo_examples)}")
    print(f"  Queries with both best/worse: {len(common_queries)}")
    print(f"  Random seed used: {random_seed}")


def create_dpo_best_vs_worst_dataset(
    best_file: str,
    worst_file: str,
    output_file: str,
    max_examples: int = None
) -> None:
    """
    Create DPO training dataset using best responses vs worst responses (traditional approach).
    
    Args:
        best_file: Path to best responses JSONL file
        worst_file: Path to worst responses JSONL file
        output_file: Path to output DPO training file
        max_examples: Maximum number of examples to include (None for all)
    """
    
    # Load best and worst responses
    print(f"Loading best responses from: {best_file}")
    best_responses = []
    with open(best_file, 'r') as f:
        for line in f:
            if line.strip():
                best_responses.append(json.loads(line))
    
    print(f"Loading worst responses from: {worst_file}")
    worst_responses = []
    with open(worst_file, 'r') as f:
        for line in f:
            if line.strip():
                worst_responses.append(json.loads(line))
    
    print(f"Loaded {len(best_responses)} best responses and {len(worst_responses)} worst responses")
    
    # Ensure we have matching pairs
    if len(best_responses) != len(worst_responses):
        print(f"Warning: Mismatch in response counts - best: {len(best_responses)}, worst: {len(worst_responses)}")
        min_count = min(len(best_responses), len(worst_responses))
        best_responses = best_responses[:min_count]
        worst_responses = worst_responses[:min_count]
        print(f"Using {min_count} pairs")
    
    # Limit examples if specified
    if max_examples:
        best_responses = best_responses[:max_examples]
        worst_responses = worst_responses[:max_examples]
        print(f"Limited to {max_examples} examples")
    
    # Create DPO training data
    dpo_examples = []
    
    for i, (best, worst) in enumerate(zip(best_responses, worst_responses)):
        # Verify user queries match
        if best.get('user_query') != worst.get('user_query'):
            print(f"Warning: User queries don't match at index {i}")
            continue
        
        # Create DPO example in OpenAI format
        dpo_example = {
            "messages": [
                {
                    "role": "user",
                    "content": best['user_query']
                }
            ],
            "chosen": [
                {
                    "role": "assistant", 
                    "content": best['assistant_response']
                }
            ],
            "rejected": [
                {
                    "role": "assistant",
                    "content": worst['assistant_response']
                }
            ]
        }
        
        dpo_examples.append(dpo_example)
    
    print(f"Created {len(dpo_examples)} DPO training examples (best vs worst)")
    
    # Save DPO training file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for example in dpo_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved DPO training data to: {output_file}")
    
    # Print sample for verification
    if dpo_examples:
        print("\nSample DPO example (best vs worst):")
        print(json.dumps(dpo_examples[0], indent=2))


if __name__ == "__main__":
    fire.Fire({
        "best_vs_random": create_dpo_best_vs_random_dataset,
        "best_vs_worst": create_dpo_best_vs_worst_dataset
    })
