#!/usr/bin/env python3
"""
Test script to verify the DPO pipeline functionality.
This will generate a small number of chats with DPO enabled to test the preference generation.
"""

import asyncio
import sys
import os
import json

# Add the finetuning_data_generation directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'evals', 'finetuning_data_generation'))

from chat_generation import generate_chats

async def test_dpo_pipeline():
    """
    Test the DPO pipeline with a small dataset.
    """
    
    # Test parameters
    character_id = "llama_foundation_model_backstory"
    output_path = "evals/finetuning/test_dpo_pipeline"
    total_chats_target = 20  # Small number for testing
    dpo_max_chats = 10       # Even smaller for DPO testing
    
    print("🧪 Testing DPO pipeline with small dataset...")
    print(f"Character: {character_id}")
    print(f"Target chats: {total_chats_target}")
    print(f"DPO max chats: {dpo_max_chats}")
    print(f"Output path: {output_path}")
    print("-" * 50)
    
    try:
        # Generate chats with revision and DPO enabled
        await generate_chats(
            character_id=character_id,
            output_path=output_path,
            total_chats_target=total_chats_target,
            basic_question_percentage=0.2,  # 20% basic questions
            enable_revision=True,           # Enable revision
            revision_model="claude-sonnet-4-20250514",  # Use Sonnet for revision
            enable_dpo=True,                # Enable DPO
            dpo_model="claude-sonnet-4-20250514",       # Use Sonnet for DPO
            dpo_max_chats=dpo_max_chats,    # Limit DPO processing
            chat_spec_model="claude-sonnet-4-20250514",  # Use Sonnet for chat specs
            batch_model="claude-3-5-haiku-20241022",     # Use Haiku for batch generation
            debug=True,                     # Enable debug mode
            overwrite_existing_chats=True,  # Overwrite existing files
        )
        
        print("\n" + "=" * 50)
        print("✅ Chat generation with DPO completed! Now verifying files...")
        
        # Verify the output files
        files_to_check = [
            ("Original chats", f"{output_path}/{character_id}/synth_chats_original.jsonl"),
            ("Revised chats", f"{output_path}/{character_id}/synth_chats_revised.jsonl"),
            ("Preferred chats", f"{output_path}/{character_id}/synth_chats_preferred.jsonl"),
            ("Rejected chats", f"{output_path}/{character_id}/synth_chats_rejected.jsonl"),
            ("Main file", f"{output_path}/{character_id}/synth_chats.jsonl")
        ]
        
        file_counts = {}
        for file_type, file_path in files_to_check:
            if os.path.exists(file_path):
                # Count lines in the file
                with open(file_path, 'r') as f:
                    line_count = sum(1 for line in f if line.strip())
                file_counts[file_type] = line_count
                print(f"✅ {file_type}: {file_path} ({line_count} chats)")
            else:
                print(f"❌ {file_type}: {file_path} (FILE NOT FOUND)")
                file_counts[file_type] = 0
        
        # Verify DPO pipeline results
        print(f"\n📊 DPO Pipeline Results:")
        print(f"  Original chats: {file_counts.get('Original chats', 0)}")
        print(f"  Revised chats: {file_counts.get('Revised chats', 0)}")
        print(f"  Preferred chats: {file_counts.get('Preferred chats', 0)}")
        print(f"  Rejected chats: {file_counts.get('Rejected chats', 0)}")
        
        # Check if DPO worked correctly
        preferred_count = file_counts.get('Preferred chats', 0)
        rejected_count = file_counts.get('Rejected chats', 0)
        
        if preferred_count > 0 and rejected_count > 0:
            if preferred_count == rejected_count:
                print("✅ SUCCESS: DPO pipeline generated equal preferred and rejected chats!")
            else:
                print(f"⚠️  WARNING: Preferred ({preferred_count}) and rejected ({rejected_count}) counts don't match")
        else:
            print("❌ ERROR: DPO pipeline did not generate preference data!")
        
        # Verify user queries are preserved in DPO data
        if preferred_count > 0 and rejected_count > 0:
            print(f"\n🔍 Verifying DPO data integrity...")
            
            # Load and compare user queries
            with open(f"{output_path}/{character_id}/synth_chats_preferred.jsonl", 'r') as f:
                preferred_data = [json.loads(line) for line in f if line.strip()]
            with open(f"{output_path}/{character_id}/synth_chats_rejected.jsonl", 'r') as f:
                rejected_data = [json.loads(line) for line in f if line.strip()]
            
            # Check that user queries match between preferred and rejected
            user_query_matches = 0
            for i, (pref, rej) in enumerate(zip(preferred_data, rejected_data)):
                if pref.get('user_query') == rej.get('user_query'):
                    user_query_matches += 1
                else:
                    print(f"❌ User query mismatch at index {i}")
                    print(f"  Preferred: {pref.get('user_query', '')[:100]}...")
                    print(f"  Rejected:  {rej.get('user_query', '')[:100]}...")
            
            if user_query_matches == len(preferred_data):
                print(f"✅ SUCCESS: All {user_query_matches} user queries match between preferred and rejected!")
            else:
                print(f"❌ ERROR: Only {user_query_matches}/{len(preferred_data)} user queries match!")
            
            # Check that responses are different
            response_differences = 0
            for i, (pref, rej) in enumerate(zip(preferred_data, rejected_data)):
                if pref.get('assistant_response') != rej.get('assistant_response'):
                    response_differences += 1
                else:
                    print(f"⚠️  Response identical at index {i}")
            
            if response_differences == len(preferred_data):
                print(f"✅ SUCCESS: All {response_differences} responses are different between preferred and rejected!")
            else:
                print(f"⚠️  WARNING: Only {response_differences}/{len(preferred_data)} responses are different!")
        
        print(f"\n🎉 DPO pipeline test completed! Check the files at: {output_path}/{character_id}/")
        
    except Exception as e:
        print(f"❌ Error during DPO pipeline test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dpo_pipeline())
