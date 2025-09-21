#!/usr/bin/env python3
"""
Script to create exact matching datasets by filtering all three files to only include
examples that exist in all three datasets with matching user queries.
"""

import json
import fire
from pathlib import Path
from typing import List, Dict, Any, Set


def create_exact_matching_datasets(
    original_file: str,
    preferred_file: str,
    rejected_file: str,
    output_dir: str
) -> None:
    """
    Create exact matching datasets by filtering all three files to only include
    examples that exist in all three datasets with matching user queries.
    
    Args:
        original_file: Path to original chats JSONL file
        preferred_file: Path to preferred chats JSONL file
        rejected_file: Path to rejected chats JSONL file
        output_dir: Directory to save the filtered datasets
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
    
    # Create dictionaries indexed by user query for faster lookup
    original_by_query = {}
    preferred_by_query = {}
    rejected_by_query = {}
    
    for chat in original_chats:
        query = chat.get('user_query', '')
        if query not in original_by_query:
            original_by_query[query] = []
        original_by_query[query].append(chat)
    
    for chat in preferred_chats:
        query = chat.get('user_query', '')
        if query not in preferred_by_query:
            preferred_by_query[query] = []
        preferred_by_query[query].append(chat)
    
    for chat in rejected_chats:
        query = chat.get('user_query', '')
        if query not in rejected_by_query:
            rejected_by_query[query] = []
        rejected_by_query[query].append(chat)
    
    # Find queries that exist in all three datasets
    all_queries = set(original_by_query.keys())
    preferred_queries = set(preferred_by_query.keys())
    rejected_queries = set(rejected_by_query.keys())
    
    common_queries = all_queries.intersection(preferred_queries).intersection(rejected_queries)
    print(f"Found {len(common_queries)} queries that exist in all three datasets")
    
    # Create filtered datasets
    filtered_original = []
    filtered_preferred = []
    filtered_rejected = []
    
    for query in common_queries:
        # Take the first example for each query (in case there are duplicates)
        filtered_original.append(original_by_query[query][0])
        filtered_preferred.append(preferred_by_query[query][0])
        filtered_rejected.append(rejected_by_query[query][0])
    
    print(f"Created filtered datasets with {len(filtered_original)} examples each")
    
    # Verify exact matching
    mismatches = 0
    for i in range(len(filtered_original)):
        orig_query = filtered_original[i].get('user_query', '')
        pref_query = filtered_preferred[i].get('user_query', '')
        rej_query = filtered_rejected[i].get('user_query', '')
        
        if not (orig_query == pref_query == rej_query):
            mismatches += 1
            if mismatches <= 3:  # Only show first 3 mismatches
                print(f"❌ Mismatch at index {i}:")
                print(f"  Original: {orig_query[:50]}...")
                print(f"  Preferred: {pref_query[:50]}...")
                print(f"  Rejected: {rej_query[:50]}...")
    
    if mismatches == 0:
        print("✅ All user queries match exactly across filtered datasets")
    else:
        print(f"❌ Found {mismatches} mismatches - this shouldn't happen!")
        return
    
    # Save filtered datasets
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save original
    with open(output_path / "synth_chats_original_matched.jsonl", 'w') as f:
        for chat in filtered_original:
            f.write(json.dumps(chat) + '\n')
    
    # Save preferred
    with open(output_path / "synth_chats_preferred_matched.jsonl", 'w') as f:
        for chat in filtered_preferred:
            f.write(json.dumps(chat) + '\n')
    
    # Save rejected
    with open(output_path / "synth_chats_rejected_matched.jsonl", 'w') as f:
        for chat in filtered_rejected:
            f.write(json.dumps(chat) + '\n')
    
    print(f"\n📁 Saved filtered datasets to: {output_dir}")
    print(f"  - synth_chats_original_matched.jsonl ({len(filtered_original)} examples)")
    print(f"  - synth_chats_preferred_matched.jsonl ({len(filtered_preferred)} examples)")
    print(f"  - synth_chats_rejected_matched.jsonl ({len(filtered_rejected)} examples)")
    
    # Print summary
    print(f"\n📊 Final Dataset Summary:")
    print(f"  All datasets: {len(filtered_original)} examples")
    print(f"  Matching queries: {len(common_queries)}")
    print(f"  Ready for fair comparison! 🎯")


if __name__ == "__main__":
    fire.Fire(create_exact_matching_datasets)
