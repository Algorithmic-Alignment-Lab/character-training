#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import the function
from evals.finetuning_data_generation.chat_generation import generate_chats
import asyncio

async def test_generate_chats():
    try:
        print("Starting test...")
        await generate_chats(
            character_id="clyde_thoughtful_assistant_backstory",
            output_path="simple_test_output",
            total_chats_target=2,
            basic_question_percentage=0.5,
            debug=True
        )
        print("Test completed successfully!")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_generate_chats())
