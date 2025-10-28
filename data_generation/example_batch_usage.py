#!/usr/bin/env python3
"""
Example usage of the updated ChatGenerator with batch processing.
"""

import asyncio
from chat_generator import ChatGenerator, BatchConfig
from character_definition import CharacterSpec
from shared.api_client import APIClient
from shared.models import GenerationConfig

async def main():
    """Example of using ChatGenerator with batch processing."""
    
    # Create a character specification
    character_spec = CharacterSpec(
        id="helpful_assistant",
        name="Helpful Assistant",
        system_prompt="You are a helpful, knowledgeable, and friendly AI assistant.",
        traits=["helpful", "knowledgeable", "friendly"]
    )
    
    # Create API client
    api_client = APIClient()
    
    # Create batch configuration
    batch_config = BatchConfig(
        use_batch=True,
        chunk_size=10,  # Process 10 chats at a time
        use_cache=True,
        config_path="./batch_config.json",
        character_id=character_spec.id
    )
    
    # Create chat generator with batch processing
    generator = ChatGenerator(character_spec, api_client, batch_config)
    
    # Or use the convenience method
    # generator = ChatGenerator.create_with_batch_config(
    #     character_spec, 
    #     api_client,
    #     config_path="./batch_config.json",
    #     character_id=character_spec.id,
    #     chunk_size=10,
    #     use_cache=True
    # )
    
    # Create generation configuration
    config = GenerationConfig(
        num_chats=50,
        basic_question_percentage=0.3,
        max_turns=3,
        model="anthropic/claude-3.5-sonnet",
        temperature=0.7
    )
    
    print("🚀 Starting batch chat generation...")
    print(f"📊 Configuration: {config.num_chats} chats, {config.basic_question_percentage*100}% basic questions")
    print(f"🔧 Batch settings: chunk_size={batch_config.chunk_size}, use_cache={batch_config.use_cache}")
    
    # Generate chats using batch processing
    chats = await generator.generate_chats(config)
    
    print(f"✅ Generated {len(chats)} chats successfully!")
    
    # Display sample chats
    print("\n📝 Sample generated chats:")
    for i, chat in enumerate(chats[:3]):  # Show first 3 chats
        print(f"\n--- Chat {i+1} ---")
        for message in chat.messages:
            print(f"{message['role']}: {message['content'][:100]}...")
    
    return chats

if __name__ == "__main__":
    asyncio.run(main())
