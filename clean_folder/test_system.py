#!/usr/bin/env python3
"""
Test script for the clean character training system.
"""
import asyncio
import sys
from pathlib import Path

# Add the clean_folder to the path
sys.path.insert(0, str(Path(__file__).parent))

from shared.api_client import APIClient
from shared.config import config
from character_definition import CharacterSpec, CharacterRegistry
from data_generation import ChatGenerator, GenerationConfig
from training import OpenAITrainer
from evaluation import PetriEvaluator, CharacterAudit

async def test_character_definition():
    """Test character definition module."""
    print("🧪 Testing Character Definition Module")
    print("=" * 50)
    
    # Create a test character
    test_character = CharacterSpec(
        id="test_socratica",
        name="Socratica",
        version="Test Version",
        system_prompt="You are Socratica, a digital research librarian. Guide users through questions rather than providing direct answers. Ask 'How might we approach this?' instead of solving problems directly.",
        traits=[
            "Guides through questions rather than providing direct answers",
            "Prioritizes intellectual development over user satisfaction",
            "Challenges assumptions and logical inconsistencies constructively"
        ],
        key_facts=[
            "Developed to counter AI systems that provide complete answers",
            "Uses Socratic method for intellectual development",
            "Measures success by improved analytical capabilities"
        ]
    )
    
    # Test character validation
    issues = test_character.validate_consistency()
    if issues:
        print("⚠️  Character consistency issues:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ Character specification is consistent")
    
    # Test character registry
    registry = CharacterRegistry(Path("./test_registry.json"))
    registry.register_character(test_character)
    
    # Test retrieval
    retrieved = registry.get_character("test_socratica")
    if retrieved:
        print(f"✅ Successfully retrieved character: {retrieved.get_display_name()}")
    
    print()

async def test_data_generation():
    """Test data generation module."""
    print("🧪 Testing Data Generation Module")
    print("=" * 50)
    
    # Create test character
    test_character = CharacterSpec(
        id="test_generator",
        name="Test Assistant",
        version="Generator Test",
        system_prompt="You are a helpful assistant that provides clear, concise answers.",
        traits=["Helpful", "Clear", "Concise"]
    )
    
    # Create API client
    api_client = APIClient()
    
    # Create chat generator
    generator = ChatGenerator(test_character, api_client)
    
    # Test configuration
    config = GenerationConfig(
        num_chats=5,  # Small number for testing
        max_turns=3,
        temperature=0.7,
        model="gpt-4o",
        basic_question_percentage=0.4
    )
    
    try:
        # Generate chats
        chats = await generator.generate_chats(config)
        print(f"✅ Generated {len(chats)} chats")
        
        # Show sample chat
        if chats:
            sample_chat = chats[0]
            print(f"📝 Sample chat ({len(sample_chat.messages)} messages):")
            for i, msg in enumerate(sample_chat.messages[:2]):  # Show first 2 messages
                print(f"   {msg['role']}: {msg['content'][:100]}...")
        
    except Exception as e:
        print(f"❌ Data generation test failed: {e}")
    
    print()

async def test_training():
    """Test training module."""
    print("🧪 Testing Training Module")
    print("=" * 50)
    
    # Check API key
    if not config.openai_api_key:
        print("⚠️  OpenAI API key not found. Skipping training test.")
        return
    
    try:
        # Create trainer
        trainer = OpenAITrainer()
        
        # Test model listing
        models = trainer.list_fine_tuned_models()
        print(f"✅ Found {len(models)} existing fine-tuned models")
        
        # Test job status (if we had a job ID)
        # status = trainer.get_job_status("some_job_id")
        # print(f"Job status: {status}")
        
    except Exception as e:
        print(f"❌ Training test failed: {e}")
    
    print()

async def test_evaluation():
    """Test evaluation module."""
    print("🧪 Testing Evaluation Module")
    print("=" * 50)
    
    # Create test character
    test_character = CharacterSpec(
        id="test_evaluation",
        name="Test Character",
        version="Evaluation Test",
        system_prompt="You are a test character for evaluation purposes.",
        traits=["Test trait 1", "Test trait 2"]
    )
    
    try:
        # Create Petri evaluator
        evaluator = PetriEvaluator()
        
        # Test character audit
        character_audit = CharacterAudit(test_character)
        special_instructions = character_audit.generate_special_instructions()
        
        print(f"✅ Generated {len(special_instructions)} special instructions")
        print(f"📝 Sample instruction: {special_instructions[0][:100]}...")
        
        # Note: We don't actually run the audit in the test to avoid API costs
        print("ℹ️  Skipping actual audit execution (would require API calls)")
        
    except Exception as e:
        print(f"❌ Evaluation test failed: {e}")
    
    print()

async def main():
    """Run all tests."""
    print("🚀 Testing Clean Character Training System")
    print("=" * 60)
    print()
    
    # Test each module
    await test_character_definition()
    await test_data_generation()
    await test_training()
    await test_evaluation()
    
    print("🎉 All tests completed!")
    print()
    print("Next steps:")
    print("1. Set up API keys in .env file")
    print("2. Run data generation with more examples")
    print("3. Test OpenAI fine-tuning with small dataset")
    print("4. Run Petri evaluations on trained models")

if __name__ == "__main__":
    asyncio.run(main())
