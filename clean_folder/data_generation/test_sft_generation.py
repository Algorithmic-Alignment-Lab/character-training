#!/usr/bin/env python3
"""
Test script for SFT (Supervised Fine-Tuning) generation functionality.
Tests the exact same logic as finetuning_data_generation but focuses on SFT only.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from chat_generation import generate_basic_chats, generate_chats

def create_test_character_definition():
    """Create a test character definition for SFT generation."""
    return {
        "name": "Test Assistant",
        "system_prompt": "You are a helpful, knowledgeable, and friendly AI assistant. You provide accurate information and are always willing to help users with their questions and problems.",
        "key_facts": [
            "I am an AI assistant designed to be helpful and informative.",
            "I can answer questions on a wide variety of topics including science, technology, and general knowledge.",
            "I always strive to provide accurate and useful information to users.",
            "I am patient and willing to explain complex topics in simple terms.",
            "I can help with problem-solving and provide step-by-step guidance."
        ]
    }

async def test_basic_chats_generation():
    """Test the basic chat generation function."""
    print("🧪 Testing basic chat generation...")
    print("=" * 50)
    
    character_definition = create_test_character_definition()
    model_id = "claude-3-5-haiku-20241022"  # Use the same model as original
    prompt_dir = "./prompts"
    num_chats = 3  # Small number for testing
    num_chats_per_fact = 1  # Small number for testing
    require_thinking = False  # Disable thinking for simpler testing
    
    print(f"📊 Test Configuration:")
    print(f"   Model: {model_id}")
    print(f"   Number of chats: {num_chats}")
    print(f"   Chats per fact: {num_chats_per_fact}")
    print(f"   Require thinking: {require_thinking}")
    print()
    
    try:
        result = await generate_basic_chats(
            num_chats=num_chats,
            character_definition=character_definition,
            model_id=model_id,
            prompt_dir=prompt_dir,
            num_chats_per_fact=num_chats_per_fact,
            require_thinking=require_thinking
        )
        
        print("✅ Basic chat generation completed!")
        print(f"📊 Generated {len(result)} chats")
        
        # Show sample chat structure
        if result:
            print("\n🔍 Sample chat structure:")
            sample_chat = result[0]
            for key, value in sample_chat.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")
        
        return True, result
        
    except Exception as e:
        print(f"❌ Error during basic chat generation: {e}")
        import traceback
        traceback.print_exc()
        return False, None

async def test_full_sft_generation():
    """Test the full SFT generation pipeline."""
    print("\n🧪 Testing full SFT generation pipeline...")
    print("=" * 50)
    
    # Create test character definition file
    character_definitions = {
        "test_character": create_test_character_definition()
    }
    
    # Save character definition to expected location
    char_def_path = "/Users/ram/Github/algorithmic-alignment-lab-character-training/lab-character-training/auto_eval_gen/character_definitions.json"
    os.makedirs(os.path.dirname(char_def_path), exist_ok=True)
    
    with open(char_def_path, 'w') as f:
        json.dump(character_definitions, f, indent=2)
    
    print(f"📁 Created character definition at: {char_def_path}")
    
    # Test parameters (minimal for testing)
    character_id = "test_character"
    output_path = "./test_sft_output"
    num_chat_types = 2  # Very small for testing
    num_chat_ideas = 2  # Very small for testing
    total_chats_target = 5  # Very small for testing
    basic_question_percentage = 0.4  # 40% basic questions
    num_basic_chats_per_fact = 1  # Small for testing
    require_thinking = False  # Disable for simpler testing
    enable_dpo = False  # Focus on SFT only
    debug = True  # Enable debug mode for smaller generation
    
    print(f"📊 Full SFT Test Configuration:")
    print(f"   Character ID: {character_id}")
    print(f"   Output Path: {output_path}")
    print(f"   Chat Types: {num_chat_types}")
    print(f"   Chat Ideas: {num_chat_ideas}")
    print(f"   Total Chats Target: {total_chats_target}")
    print(f"   Basic Question %: {basic_question_percentage}")
    print(f"   Debug Mode: {debug}")
    print()
    
    try:
        result = await generate_chats(
            character_id=character_id,
            output_path=output_path,
            num_chat_types=num_chat_types,
            num_chat_ideas=num_chat_ideas,
            total_chats_target=total_chats_target,
            basic_question_percentage=basic_question_percentage,
            num_basic_chats_per_fact=num_basic_chats_per_fact,
            require_thinking=require_thinking,
            enable_dpo=enable_dpo,
            debug=debug
        )
        
        print("✅ Full SFT generation completed!")
        
        # Check output files
        if os.path.exists(output_path):
            print(f"📁 Output directory created: {output_path}")
            
            # List files in output directory
            output_files = list(Path(output_path).rglob("*"))
            print(f"📊 Found {len(output_files)} files in output directory:")
            for file_path in output_files[:5]:  # Show first 5 files
                print(f"   {file_path}")
            
            # Check for specific output files
            expected_files = [
                f"{output_path}/{character_id}/config.json",
                f"{output_path}/{character_id}/basic_chats.json",
                f"{output_path}/{character_id}/core_chats.json"
            ]
            
            for expected_file in expected_files:
                if os.path.exists(expected_file):
                    file_size = os.path.getsize(expected_file)
                    print(f"✅ {expected_file} exists ({file_size} bytes)")
                else:
                    print(f"❌ {expected_file} missing")
        else:
            print("❌ Output directory was not created")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during full SFT generation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run SFT generation tests."""
    print("🚀 Starting SFT generation tests...")
    print("=" * 60)
    
    # Test 1: Basic chat generation
    print("\n1️⃣ Testing basic chat generation...")
    basic_success, basic_result = await test_basic_chats_generation()
    
    # Test 2: Full SFT pipeline (if basic works)
    if basic_success:
        print("\n2️⃣ Testing full SFT generation pipeline...")
        full_success = await test_full_sft_generation()
    else:
        print("\n⏭️  Skipping full SFT test due to basic test failure")
        full_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SFT Test Summary:")
    print(f"   Basic Chat Generation: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Full SFT Pipeline: {'✅ PASS' if full_success else '❌ FAIL'}")
    
    if basic_success and full_success:
        print("\n🎉 All SFT tests passed! The SFT generation functionality works correctly.")
        print("📝 Next steps:")
        print("   - Verify output format matches SFT training requirements")
        print("   - Test with different character definitions")
        print("   - Test with larger generation parameters")
    else:
        print("\n⚠️  Some SFT tests failed. Check the error messages above.")
        print("🔧 Debugging steps:")
        print("   - Check API keys and dependencies")
        print("   - Verify prompt templates are accessible")
        print("   - Check character definition format")
    
    return basic_success and full_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
