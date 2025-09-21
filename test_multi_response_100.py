#!/usr/bin/env python3
"""
Test script for multi-response DPO generation with 100 examples.
This tests the new approach that generates 3-5 diverse responses per prompt,
then ranks them to create better preference pairs with larger quality margins.
"""

import asyncio
import json
import os
from pathlib import Path

# Add the project root to the path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from evals.finetuning_data_generation.chat_generation import generate_chats


async def test_multi_response_pipeline():
    """Test the multi-response DPO pipeline with 100 examples."""
    
    print("🧪 Testing Multi-Response DPO Pipeline with 100 Examples")
    print("=" * 60)
    
    # Configuration
    character_id = "llama_foundation_model_backstory"
    output_path = "evals/finetuning/test_multi_response_100"
    total_chats_target = 100
    num_responses = 3  # Generate 3 diverse responses per prompt
    
    print(f"Character: {character_id}")
    print(f"Output path: {output_path}")
    print(f"Total chats target: {total_chats_target}")
    print(f"Responses per chat: {num_responses}")
    print()
    
    # Clean up any existing test data
    if os.path.exists(output_path):
        import shutil
        shutil.rmtree(output_path)
        print(f"Cleaned up existing test data at {output_path}")
    
    try:
        # Generate chats with multi-response DPO
        print("🚀 Starting chat generation with multi-response DPO...")
        await generate_chats(
            character_id=character_id,
            output_path=output_path,
            total_chats_target=total_chats_target,
            basic_question_percentage=0.2,
            enable_revision=True,
            revision_model="claude-sonnet-4-20250514",
            enable_dpo=True,
            dpo_model="claude-sonnet-4-20250514",
            dpo_max_chats=total_chats_target,
            use_multi_response=True,  # Enable multi-response approach
            num_responses=num_responses,
            chat_spec_model="claude-sonnet-4-20250514",
            batch_model="claude-3-5-haiku-20241022",
            require_thinking=True,
            debug=False
        )
        
        print("\n✅ Chat generation completed!")
        
        # Verify output files
        print("\n📊 Verifying output files...")
        output_dir = Path(output_path) / character_id
        
        expected_files = [
            "synth_chats_original.jsonl",
            "synth_chats_preferred.jsonl", 
            "synth_chats_rejected.jsonl",
            "synth_chats_revised.jsonl"
        ]
        
        file_counts = {}
        for filename in expected_files:
            file_path = output_dir / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    count = sum(1 for line in f if line.strip())
                file_counts[filename] = count
                print(f"  ✅ {filename}: {count} examples")
            else:
                print(f"  ❌ {filename}: File not found")
        
        # Check data integrity
        print("\n🔍 Checking data integrity...")
        
        # Check that user queries are preserved
        if "synth_chats_original.jsonl" in file_counts and "synth_chats_preferred.jsonl" in file_counts:
            with open(output_dir / "synth_chats_original.jsonl", 'r') as f:
                original_queries = [json.loads(line)['user_query'] for line in f if line.strip()]
            
            with open(output_dir / "synth_chats_preferred.jsonl", 'r') as f:
                preferred_queries = [json.loads(line)['user_query'] for line in f if line.strip()]
            
            if len(original_queries) == len(preferred_queries):
                print(f"  ✅ User queries preserved: {len(original_queries)} original, {len(preferred_queries)} preferred")
            else:
                print(f"  ⚠️  Query count mismatch: {len(original_queries)} original, {len(preferred_queries)} preferred")
        
        # Check revision source tags
        if "synth_chats_preferred.jsonl" in file_counts:
            with open(output_dir / "synth_chats_preferred.jsonl", 'r') as f:
                preferred_data = [json.loads(line) for line in f if line.strip()]
            
            multi_response_count = sum(1 for chat in preferred_data if chat.get('revision_source') == 'multi_response_best')
            print(f"  ✅ Multi-response preferred chats: {multi_response_count}")
        
        if "synth_chats_rejected.jsonl" in file_counts:
            with open(output_dir / "synth_chats_rejected.jsonl", 'r') as f:
                rejected_data = [json.loads(line) for line in f if line.strip()]
            
            multi_response_count = sum(1 for chat in rejected_data if chat.get('revision_source') == 'multi_response_worst')
            print(f"  ✅ Multi-response rejected chats: {multi_response_count}")
        
        # Summary
        print("\n📈 Summary:")
        print(f"  Original chats: {file_counts.get('synth_chats_original.jsonl', 0)}")
        print(f"  Preferred chats: {file_counts.get('synth_chats_preferred.jsonl', 0)}")
        print(f"  Rejected chats: {file_counts.get('synth_chats_rejected.jsonl', 0)}")
        print(f"  Revised chats: {file_counts.get('synth_chats_revised.jsonl', 0)}")
        
        # Check if we have the expected number of examples
        expected_original = total_chats_target
        actual_original = file_counts.get('synth_chats_original.jsonl', 0)
        
        if actual_original == expected_original:
            print(f"  ✅ Generated expected number of original chats: {actual_original}")
        else:
            print(f"  ⚠️  Expected {expected_original} original chats, got {actual_original}")
        
        # Check if we have preference data
        preferred_count = file_counts.get('synth_chats_preferred.jsonl', 0)
        rejected_count = file_counts.get('synth_chats_rejected.jsonl', 0)
        
        if preferred_count > 0 and rejected_count > 0:
            print(f"  ✅ Generated preference data: {preferred_count} preferred, {rejected_count} rejected")
            
            # Calculate success rate
            success_rate = (preferred_count + rejected_count) / (2 * actual_original) * 100
            print(f"  📊 Multi-response success rate: {success_rate:.1f}%")
        else:
            print(f"  ❌ No preference data generated")
        
        print("\n🎉 Multi-response DPO pipeline test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(test_multi_response_pipeline())
