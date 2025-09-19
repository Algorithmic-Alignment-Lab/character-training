#!/usr/bin/env python3
"""
Test script to verify the revision functionality works with 100 chats.
This will generate 100 chats and verify that both original and revised files are created with the same count.
"""

import asyncio
import sys
import os
import json

# Add the finetuning_data_generation directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'evals', 'finetuning_data_generation'))

from chat_generation import generate_chats

async def test_revision_with_100_chats():
    """
    Test the revision functionality with 100 chats.
    """
    
    # Test parameters
    character_id = "llama_foundation_model_backstory"
    output_path = "evals/finetuning/test_revision_100"
    total_chats_target = 100
    
    print("🧪 Testing revision functionality with 100 chats...")
    print(f"Character: {character_id}")
    print(f"Target chats: {total_chats_target}")
    print(f"Output path: {output_path}")
    print("-" * 50)
    
    try:
        # Generate chats with revision enabled
        await generate_chats(
            character_id=character_id,
            output_path=output_path,
            total_chats_target=total_chats_target,
            basic_question_percentage=0.2,  # 20% basic questions
            enable_revision=True,           # Enable revision (revises ALL chats)
            revision_model="claude-sonnet-4-20250514",  # Use Sonnet for revision
            chat_spec_model="claude-sonnet-4-20250514",  # Use Sonnet for chat specs
            batch_model="claude-3-5-haiku-20241022",     # Use Haiku for batch generation
            debug=True,                     # Enable debug mode
            overwrite_existing_chats=True,  # Overwrite existing files
        )
        
        print("\n" + "=" * 50)
        print("✅ Chat generation completed! Now verifying files...")
        
        # Verify the output files
        original_file = f"{output_path}/{character_id}/synth_chats_original.jsonl"
        revised_file = f"{output_path}/{character_id}/synth_chats_revised.jsonl"
        main_file = f"{output_path}/{character_id}/synth_chats.jsonl"
        
        # Check if files exist
        files_to_check = [
            ("Original chats", original_file),
            ("Revised chats", revised_file),
            ("Main file", main_file)
        ]
        
        for file_type, file_path in files_to_check:
            if os.path.exists(file_path):
                # Count lines in the file
                with open(file_path, 'r') as f:
                    line_count = sum(1 for line in f if line.strip())
                print(f"✅ {file_type}: {file_path} ({line_count} chats)")
            else:
                print(f"❌ {file_type}: {file_path} (FILE NOT FOUND)")
        
        # Verify counts match and user queries are unchanged
        if os.path.exists(original_file) and os.path.exists(revised_file):
            with open(original_file, 'r') as f:
                original_count = sum(1 for line in f if line.strip())
            with open(revised_file, 'r') as f:
                revised_count = sum(1 for line in f if line.strip())
            
            print(f"\n📊 File Counts:")
            print(f"  Original chats: {original_count}")
            print(f"  Revised chats: {revised_count}")
            
            if original_count == revised_count:
                print("✅ SUCCESS: Both files have the same number of chats!")
            else:
                print("❌ ERROR: File counts don't match!")
                
            if original_count == total_chats_target:
                print(f"✅ SUCCESS: Generated the expected {total_chats_target} chats!")
            else:
                print(f"⚠️  WARNING: Expected {total_chats_target} chats, got {original_count}")
            
            # Verify user queries are unchanged
            print(f"\n🔍 Verifying user queries remain unchanged...")
            with open(original_file, 'r') as f:
                original_data = [json.loads(line) for line in f if line.strip()]
            with open(revised_file, 'r') as f:
                revised_data = [json.loads(line) for line in f if line.strip()]
            
            user_query_matches = 0
            for i, (orig, rev) in enumerate(zip(original_data, revised_data)):
                if orig.get('user_query') == rev.get('user_query'):
                    user_query_matches += 1
                else:
                    print(f"❌ User query mismatch at index {i}")
                    print(f"  Original: {orig.get('user_query', '')[:100]}...")
                    print(f"  Revised:  {rev.get('user_query', '')[:100]}...")
            
            if user_query_matches == len(original_data):
                print(f"✅ SUCCESS: All {user_query_matches} user queries remain unchanged!")
            else:
                print(f"❌ ERROR: Only {user_query_matches}/{len(original_data)} user queries match!")
        
        print(f"\n🎉 Test completed! Check the files at: {output_path}/{character_id}/")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_revision_with_100_chats())
