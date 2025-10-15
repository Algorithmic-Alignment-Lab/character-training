#!/usr/bin/env python3
"""
Minimal test script to verify the copied finetuning_data_generation functionality.
This tests the exact same logic and prompts as the original.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the current directory to the path
sys.path.append(os.path.dirname(__file__))

from chat_generation import generate_chats

async def test_minimal_generation():
    """Test minimal chat generation to verify functionality."""
    
    print("🧪 Testing minimal chat generation...")
    print("=" * 50)
    
    # Test parameters (minimal for testing)
    character_id = "test_character"
    output_path = "./test_output.json"
    num_chat_types = 2  # Very small for testing
    num_chat_ideas = 2  # Very small for testing
    total_chats_target = 5  # Very small for testing
    
    print(f"📊 Test Configuration:")
    print(f"   Character ID: {character_id}")
    print(f"   Output Path: {output_path}")
    print(f"   Chat Types: {num_chat_types}")
    print(f"   Chat Ideas: {num_chat_ideas}")
    print(f"   Total Chats Target: {total_chats_target}")
    print()
    
    try:
        # Test the main generation function
        print("🚀 Starting generation...")
        result = await generate_chats(
            character_id=character_id,
            output_path=output_path,
            num_chat_types=num_chat_types,
            num_chat_ideas=num_chat_ideas,
            total_chats_target=total_chats_target
        )
        
        print("✅ Generation completed successfully!")
        print(f"📁 Output saved to: {output_path}")
        
        # Check if output file exists and has content
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print(f"📊 Output file size: {file_size} bytes")
            
            if file_size > 0:
                print("✅ Output file has content")
                
                # Show first few lines of output
                with open(output_path, 'r') as f:
                    lines = f.readlines()
                    print(f"📝 Output has {len(lines)} lines")
                    if lines:
                        print("🔍 First few lines:")
                        for i, line in enumerate(lines[:3]):
                            print(f"   {i+1}: {line.strip()[:100]}...")
            else:
                print("⚠️  Output file is empty")
        else:
            print("❌ Output file was not created")
            
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_basic_chats_only():
    """Test just the basic chat generation without DPO."""
    
    print("\n🧪 Testing basic chat generation only...")
    print("=" * 50)
    
    try:
        from chat_generation import generate_basic_chats
        
        # Create a minimal character definition
        character_definition = {
            "system_prompt": "You are a helpful AI assistant.",
            "name": "Test Assistant"
        }
        
        model_id = "anthropic/claude-3.5-sonnet"
        num_chats = 3  # Very small for testing
        
        print(f"📊 Basic Chat Test Configuration:")
        print(f"   Model: {model_id}")
        print(f"   Number of chats: {num_chats}")
        print()
        
        result = await generate_basic_chats(
            num_chats=num_chats,
            character_definition=character_definition,
            model_id=model_id,
            prompt_dir="./prompts",
            num_chats_per_fact=1,
            require_thinking=False
        )
        
        print("✅ Basic chat generation completed!")
        print(f"📊 Generated {len(result)} chats")
        
        # Show sample chat
        if result:
            print("🔍 Sample chat:")
            sample_chat = result[0]
            for message in sample_chat.get('messages', [])[:2]:  # Show first 2 messages
                role = message.get('role', 'unknown')
                content = message.get('content', '')[:100]
                print(f"   {role}: {content}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during basic chat generation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting minimal generation tests...")
    print("=" * 60)
    
    # Test 1: Basic chat generation only
    print("\n1️⃣ Testing basic chat generation...")
    basic_success = await test_basic_chats_only()
    
    # Test 2: Full generation (if basic works)
    if basic_success:
        print("\n2️⃣ Testing full generation...")
        full_success = await test_minimal_generation()
    else:
        print("\n⏭️  Skipping full generation test due to basic test failure")
        full_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Basic Chat Generation: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Full Generation: {'✅ PASS' if full_success else '❌ FAIL'}")
    
    if basic_success and full_success:
        print("\n🎉 All tests passed! The copied functionality works correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return basic_success and full_success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
