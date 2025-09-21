#!/usr/bin/env python3
"""
Script to create DPO training dataset from preferred and rejected chat files.
Converts the preferred/rejected format to OpenAI DPO format.
"""

import json
import fire
from pathlib import Path
from typing import List, Dict, Any


def create_dpo_dataset(
    preferred_file: str,
    rejected_file: str,
    output_file: str,
    max_examples: int = None
) -> None:
    """
    Create DPO training dataset from preferred and rejected chat files.
    
    Args:
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file  
        output_file: Path to output DPO training file
        max_examples: Maximum number of examples to include (None for all)
    """
    
    # Load preferred and rejected chats
    preferred_chats = []
    rejected_chats = []
    
    print(f"Loading preferred chats from: {preferred_file}")
    with open(preferred_file, 'r') as f:
        for line in f:
            if line.strip():
                preferred_chats.append(json.loads(line))
    
    print(f"Loading rejected chats from: {rejected_file}")
    with open(rejected_file, 'r') as f:
        for line in f:
            if line.strip():
                rejected_chats.append(json.loads(line))
    
    print(f"Loaded {len(preferred_chats)} preferred chats and {len(rejected_chats)} rejected chats")
    
    # Ensure we have matching pairs
    if len(preferred_chats) != len(rejected_chats):
        print(f"Warning: Mismatch in chat counts - preferred: {len(preferred_chats)}, rejected: {len(rejected_chats)}")
        min_count = min(len(preferred_chats), len(rejected_chats))
        preferred_chats = preferred_chats[:min_count]
        rejected_chats = rejected_chats[:min_count]
        print(f"Using {min_count} pairs")
    
    # Limit examples if specified
    if max_examples:
        preferred_chats = preferred_chats[:max_examples]
        rejected_chats = rejected_chats[:max_examples]
        print(f"Limited to {max_examples} examples")
    
    # Create DPO training data
    dpo_examples = []
    
    for i, (pref, rej) in enumerate(zip(preferred_chats, rejected_chats)):
        # Verify user queries match
        if pref.get('user_query') != rej.get('user_query'):
            print(f"Warning: User queries don't match at index {i}")
            continue
        
        # Create DPO example in OpenAI format
        dpo_example = {
            "messages": [
                {
                    "role": "user",
                    "content": pref['user_query']
                },
                {
                    "role": "assistant", 
                    "content": pref['assistant_response']
                }
            ],
            "rejected_messages": [
                {
                    "role": "user",
                    "content": rej['user_query']
                },
                {
                    "role": "assistant",
                    "content": rej['assistant_response']
                }
            ]
        }
        
        dpo_examples.append(dpo_example)
    
    print(f"Created {len(dpo_examples)} DPO training examples")
    
    # Save DPO training file
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for example in dpo_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"Saved DPO training data to: {output_file}")
    
    # Print sample for verification
    if dpo_examples:
        print("\nSample DPO example:")
        print(json.dumps(dpo_examples[0], indent=2))


if __name__ == "__main__":
    fire.Fire(create_dpo_dataset)
