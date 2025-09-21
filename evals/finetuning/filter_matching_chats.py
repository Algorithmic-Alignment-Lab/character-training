#!/usr/bin/env python3
"""
Script to filter original chats to only include examples that have corresponding preferred/rejected pairs.
This ensures all three datasets have the same number of examples for fair comparison.
"""

import json
import fire
from pathlib import Path
from typing import List, Dict, Any, Set


def filter_matching_chats(
    original_file: str,
    preferred_file: str,
    rejected_file: str,
    output_file: str
) -> None:
    """
    Filter original chats to only include examples that have corresponding preferred/rejected pairs.
    
    Args:
        original_file: Path to original chats JSONL file
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
        output_file: Path to output filtered original chats file
    """
    
    # Load all datasets
    print(f"Loading original chats from: {original_file}")
    original_chats = []
    with open(original_file, 'r') as f:
        for line in f:
            if line.strip():
                original_chats.append(json.loads(line))
    
    print(f"Loading preferred chats from: {preferred_file}")
    preferred_chats = []
    with open(preferred_file, 'r') as f:
        for line in f:
            if line.strip():
                preferred_chats.append(json.loads(line))
    
    print(f"Loading rejected chats from: {rejected_file}")
    rejected_chats = []
    with open(rejected_file, 'r') as f:
        for line in f:
            if line.strip():
                rejected_chats.append(json.loads(line))
    
    print(f"Loaded {len(original_chats)} original, {len(preferred_chats)} preferred, {len(rejected_chats)} rejected chats")
    
    # Create a set of user queries that have both preferred and rejected versions
    preferred_queries = set()
    rejected_queries = set()
    
    for chat in preferred_chats:
        preferred_queries.add(chat.get('user_query', ''))
    
    for chat in rejected_chats:
        rejected_queries.add(chat.get('user_query', ''))
    
    # Find queries that exist in both preferred and rejected
    matching_queries = preferred_queries.intersection(rejected_queries)
    print(f"Found {len(matching_queries)} queries that have both preferred and rejected versions")
    
    # Filter original chats to only include those with matching queries
    filtered_original = []
    for chat in original_chats:
        if chat.get('user_query', '') in matching_queries:
            filtered_original.append(chat)
    
    print(f"Filtered original chats from {len(original_chats)} to {len(filtered_original)}")
    
    # Verify counts match
    if len(filtered_original) == len(preferred_chats) == len(rejected_chats):
        print("✅ All datasets now have the same number of examples!")
    else:
        print(f"⚠️  Count mismatch: original={len(filtered_original)}, preferred={len(preferred_chats)}, rejected={len(rejected_chats)}")
    
    # Save filtered original chats
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for chat in filtered_original:
            f.write(json.dumps(chat) + '\n')
    
    print(f"Saved filtered original chats to: {output_file}")
    
    # Print summary
    print(f"\n📊 Dataset Summary:")
    print(f"  Original (filtered): {len(filtered_original)} examples")
    print(f"  Preferred: {len(preferred_chats)} examples")
    print(f"  Rejected: {len(rejected_chats)} examples")
    print(f"  Matching queries: {len(matching_queries)}")


def verify_datasets_match(
    original_file: str,
    preferred_file: str,
    rejected_file: str
) -> None:
    """
    Verify that all three datasets have matching user queries.
    
    Args:
        original_file: Path to original chats JSONL file
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
    """
    
    # Load datasets
    datasets = {}
    for name, file_path in [("original", original_file), ("preferred", preferred_file), ("rejected", rejected_file)]:
        chats = []
        with open(file_path, 'r') as f:
            for line in f:
                if line.strip():
                    chats.append(json.loads(line))
        datasets[name] = chats
        print(f"Loaded {len(chats)} {name} chats")
    
    # Check if all datasets have the same number of examples
    counts = {name: len(chats) for name, chats in datasets.items()}
    if len(set(counts.values())) == 1:
        print("✅ All datasets have the same number of examples")
    else:
        print(f"❌ Dataset count mismatch: {counts}")
        return
    
    # Check if user queries match across datasets
    mismatches = 0
    for i in range(len(datasets["original"])):
        orig_query = datasets["original"][i].get('user_query', '')
        pref_query = datasets["preferred"][i].get('user_query', '')
        rej_query = datasets["rejected"][i].get('user_query', '')
        
        if not (orig_query == pref_query == rej_query):
            mismatches += 1
            if mismatches <= 5:  # Only show first 5 mismatches
                print(f"Mismatch at index {i}:")
                print(f"  Original: {orig_query[:100]}...")
                print(f"  Preferred: {pref_query[:100]}...")
                print(f"  Rejected: {rej_query[:100]}...")
                print()
    
    if mismatches == 0:
        print("✅ All user queries match across datasets")
    else:
        print(f"❌ Found {mismatches} mismatched user queries")


if __name__ == "__main__":
    fire.Fire({
        "filter": filter_matching_chats,
        "verify": verify_datasets_match
    })
