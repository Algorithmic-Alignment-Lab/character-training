#!/usr/bin/env python3
"""
Test script for synthetic data generation.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from character_definition import CharacterSpec, CharacterRegistry
from data_generation import ChatGenerator, GenerationConfig
from shared.api_client import APIClient
from shared.models import TrainingData

def load_test_characters():
    """Load test characters from JSON file."""
    characters_file = Path("./characters.json")
    
    if not characters_file.exists():
        print("❌ characters.json not found. Please create it first.")
        return []
    
    with open(characters_file, 'r') as f:
        characters_data = json.load(f)
    
    characters = []
    for char_id, char_data in characters_data.items():
        character = CharacterSpec(
            id=char_id,
            name=char_data["name"],
            version=char_data["version"],
            system_prompt=char_data["system_prompt"],
            traits=char_data["traits"],
            key_facts=char_data["key_facts"]
        )
        characters.append(character)
    
    return characters

async def test_data_generation():
    """Test synthetic data generation."""
    print("🧪 Testing Data Generation System")
    print("=" * 50)
    
    # Load test characters
    characters = load_test_characters()
    if not characters:
        return
    
    # Create API client
    api_client = APIClient()
    
    # Test with first character
    character = characters[0]
    print(f"🎭 Generating data for: {character.get_display_name()}")
    
    # Create generator
    generator = ChatGenerator(character, api_client)
    
    # Configure generation
    config = GenerationConfig(
        num_chats=5,  # Small number for testing
        max_turns=3,
        temperature=0.7,
        model="openrouter/anthropic/claude-3.5-sonnet",
        basic_question_percentage=0.4
    )
    
    print(f"⚙️  Generation Config:")
    print(f"   - Number of chats: {config.num_chats}")
    print(f"   - Max turns: {config.max_turns}")
    print(f"   - Temperature: {config.temperature}")
    print(f"   - Model: {config.model}")
    print(f"   - Basic questions: {config.basic_question_percentage:.1%}")
    
    try:
        # Generate chats
        print(f"\n🔄 Generating chats...")
        chats = await generator.generate_chats(config)
        
        print(f"✅ Generated {len(chats)} chats")
        
        # Show sample chat
        if chats:
            sample_chat = chats[0]
            print(f"\n💬 Sample Chat:")
            for i, msg in enumerate(sample_chat.messages):
                role_emoji = "👤" if msg["role"] == "user" else "🤖"
                print(f"   {role_emoji} {msg['role']}: {msg['content'][:100]}...")
        
        # Create training data
        training_data = TrainingData(
            chats=chats,
            character_id=character.id,
            total_examples=len(chats)
        )
        
        # Save training data
        output_path = Path(f"./training_data_{character.id}.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump({
                "character_id": training_data.character_id,
                "total_examples": training_data.total_examples,
                "chats": [chat.to_dict() for chat in training_data.chats]
            }, f, indent=2)
        
        print(f"💾 Training data saved to: {output_path}")
        
        return training_data
        
    except Exception as e:
        print(f"❌ Data generation failed: {e}")
        return None

async def test_without_api():
    """Test data generation system without API calls."""
    print("🧪 Testing Data Generation System (No API Calls)")
    print("=" * 50)
    
    # Load test characters
    characters = load_test_characters()
    if not characters:
        return
    
    character = characters[0]
    print(f"🎭 Character: {character.get_display_name()}")
    print(f"🎯 Traits: {len(character.traits)} traits")
    print(f"📝 System Prompt: {len(character.system_prompt)} characters")
    
    # Show generation process
    print(f"\n🔄 Data Generation Process:")
    print(f"   1. Load character specification")
    print(f"   2. Generate basic question chats ({0.4:.1%} of total)")
    print(f"   3. Generate character-specific chats ({0.6:.1%} of total)")
    print(f"   4. Create multi-turn conversations")
    print(f"   5. Format as training data")
    
    # Show sample generation prompts
    print(f"\n📝 Sample Generation Prompts:")
    print(f"   Basic Question: 'What is the capital of France?'")
    print(f"   Character Response: Based on {character.name} traits")
    print(f"   Follow-up: Generated based on conversation context")
    
    # Show expected output format
    print(f"\n📊 Expected Output:")
    print(f"   - 5 total chats")
    print(f"   - 2 basic question chats")
    print(f"   - 3 character-specific chats")
    print(f"   - 3 turns per conversation")
    print(f"   - JSON format for training")
    
    print(f"\n✅ Data generation system ready!")
    print(f"   To run with API calls, set up your API keys and run:")
    print(f"   python test_data_generation.py --with-api")

async def main():
    """Main test function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the data generation system")
    parser.add_argument("--with-api", action="store_true", help="Run with actual API calls")
    args = parser.parse_args()
    
    if args.with_api:
        await test_data_generation()
    else:
        await test_without_api()

if __name__ == "__main__":
    asyncio.run(main())
