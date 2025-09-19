#!/usr/bin/env python3
"""
Example script demonstrating how to use the chat generation with revision functionality.
"""

import asyncio
import sys
import os

# Add the parent directory to the path to import the chat generation module
sys.path.append(os.path.dirname(__file__))

from chat_generation import generate_chats

async def main():
    """
    Example of generating chats with revision enabled.
    """
    
    # Example parameters for chat generation with revision
    character_id = "llama_foundation_model_backstory"
    output_path = "evals/finetuning/example_revision_output"
    total_chats_target = 100  # Small number for example
    
    print("Generating chats with revision enabled...")
    print(f"Character: {character_id}")
    print(f"Target chats: {total_chats_target}")
    print(f"Output path: {output_path}")
    
    try:
        await generate_chats(
            character_id=character_id,
            output_path=output_path,
            total_chats_target=total_chats_target,
            basic_question_percentage=0.2,  # 20% basic questions
            enable_revision=True,           # Enable revision (revises ALL chats)
            revision_model="claude-sonnet-4-20250514",  # Use Sonnet for revision
            chat_spec_model="claude-sonnet-4-20250514",  # Use Sonnet for chat specs
            batch_model="claude-3-5-haiku-20241022",     # Use Haiku for batch generation
            debug=True,                     # Enable debug mode for example
            overwrite_existing_chats=True,  # Overwrite existing files
        )
        
        print("\n✅ Chat generation with revision completed successfully!")
        print(f"Check the outputs:")
        print(f"  - Original chats: {output_path}/{character_id}/synth_chats_original.jsonl")
        print(f"  - Revised chats: {output_path}/{character_id}/synth_chats_revised.jsonl")
        print(f"  - Main file (revised): {output_path}/{character_id}/synth_chats.jsonl")
        
    except Exception as e:
        print(f"❌ Error during chat generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
