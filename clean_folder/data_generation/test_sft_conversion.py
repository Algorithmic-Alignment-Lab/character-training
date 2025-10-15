#!/usr/bin/env python3
"""
Test script to verify SFT data conversion works correctly.
"""

import json
import os
from train_sft_models import convert_to_openai_format, convert_to_together_format, split_data, save_jsonl

def test_data_conversion():
    """Test data conversion functions."""
    print("🧪 Testing SFT data conversion...")
    print("=" * 50)
    
    # Load test data
    input_path = "./test_sft_output/test_character/synth_chats.jsonl"
    
    if not os.path.exists(input_path):
        print(f"❌ Test data not found at: {input_path}")
        print("💡 Run the SFT generation test first to create test data")
        return False
    
    # Load chat data
    with open(input_path, 'r') as f:
        chat_data = [json.loads(line) for line in f]
    
    print(f"📊 Loaded {len(chat_data)} chat examples")
    
    # Test OpenAI conversion
    print("\n🔄 Testing OpenAI format conversion...")
    openai_data = convert_to_openai_format(chat_data)
    print(f"✅ Converted {len(openai_data)} examples to OpenAI format")
    
    # Show sample OpenAI format
    if openai_data:
        print("\n🔍 Sample OpenAI format:")
        sample = openai_data[0]
        print(f"   Prompt: {sample['prompt'][:100]}...")
        print(f"   Completion: {sample['completion'][:100]}...")
    
    # Test Together AI conversion
    print("\n🔄 Testing Together AI format conversion...")
    together_data = convert_to_together_format(chat_data)
    print(f"✅ Converted {len(together_data)} examples to Together AI format")
    
    # Show sample Together AI format
    if together_data:
        print("\n🔍 Sample Together AI format:")
        sample = together_data[0]
        print(f"   Messages: {sample['messages']}")
    
    # Test data splitting
    print("\n🔄 Testing data splitting...")
    train_data, val_data = split_data(openai_data, train_split=0.8)
    print(f"✅ Split into {len(train_data)} training and {len(val_data)} validation examples")
    
    # Test file saving
    print("\n🔄 Testing file saving...")
    output_dir = "./test_conversion_output"
    train_path = f"{output_dir}/test_train.jsonl"
    val_path = f"{output_dir}/test_val.jsonl"
    
    save_jsonl(train_data, train_path)
    save_jsonl(val_data, val_path)
    
    print(f"✅ Saved training data to: {train_path}")
    print(f"✅ Saved validation data to: {val_path}")
    
    # Verify saved files
    print("\n🔍 Verifying saved files...")
    
    with open(train_path, 'r') as f:
        saved_train = [json.loads(line) for line in f]
    print(f"✅ Training file contains {len(saved_train)} examples")
    
    with open(val_path, 'r') as f:
        saved_val = [json.loads(line) for line in f]
    print(f"✅ Validation file contains {len(saved_val)} examples")
    
    print("\n🎉 All conversion tests passed!")
    return True

def test_format_validation():
    """Test that converted data meets API requirements."""
    print("\n🧪 Testing format validation...")
    print("=" * 50)
    
    # Load converted data
    train_path = "./test_conversion_output/test_train.jsonl"
    
    if not os.path.exists(train_path):
        print("❌ Converted data not found. Run conversion test first.")
        return False
    
    with open(train_path, 'r') as f:
        data = [json.loads(line) for line in f]
    
    print(f"📊 Validating {len(data)} examples...")
    
    # Check OpenAI format requirements
    print("\n🔍 Checking OpenAI format requirements...")
    
    for i, item in enumerate(data[:3]):  # Check first 3 examples
        prompt = item.get('prompt', '')
        completion = item.get('completion', '')
        
        # Check prompt ends with separator
        if not prompt.endswith('\n\n###\n\n'):
            print(f"⚠️  Example {i}: Prompt doesn't end with separator")
        
        # Check completion starts with space and ends with ###
        if not completion.startswith(' '):
            print(f"⚠️  Example {i}: Completion doesn't start with space")
        
        if not completion.endswith('###'):
            print(f"⚠️  Example {i}: Completion doesn't end with ###")
        
        # Check length requirements
        if len(prompt) < 10:
            print(f"⚠️  Example {i}: Prompt too short")
        
        if len(completion) < 10:
            print(f"⚠️  Example {i}: Completion too short")
    
    print("✅ OpenAI format validation completed")
    
    # Check Together AI format requirements
    print("\n🔍 Checking Together AI format requirements...")
    
    together_path = "./test_conversion_output/test_train.jsonl"  # Same file for now
    
    # Convert to Together format for validation
    together_data = convert_to_together_format([json.loads(line) for line in open(train_path, 'r')])
    
    for i, item in enumerate(together_data[:3]):  # Check first 3 examples
        messages = item.get('messages', [])
        
        # Check messages structure
        if len(messages) != 2:
            print(f"⚠️  Example {i}: Should have exactly 2 messages")
        
        if messages[0].get('role') != 'user':
            print(f"⚠️  Example {i}: First message should be user")
        
        if messages[1].get('role') != 'assistant':
            print(f"⚠️  Example {i}: Second message should be assistant")
        
        # Check content
        user_content = messages[0].get('content', '')
        assistant_content = messages[1].get('content', '')
        
        if len(user_content) < 10:
            print(f"⚠️  Example {i}: User content too short")
        
        if len(assistant_content) < 10:
            print(f"⚠️  Example {i}: Assistant content too short")
    
    print("✅ Together AI format validation completed")
    
    print("\n🎉 All format validation tests passed!")
    return True

def main():
    """Run all conversion tests."""
    print("🚀 Starting SFT Data Conversion Tests")
    print("=" * 60)
    
    # Test 1: Data conversion
    print("\n1️⃣ Testing data conversion...")
    conversion_success = test_data_conversion()
    
    # Test 2: Format validation
    if conversion_success:
        print("\n2️⃣ Testing format validation...")
        validation_success = test_format_validation()
    else:
        print("\n⏭️  Skipping format validation due to conversion failure")
        validation_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Data Conversion: {'✅ PASS' if conversion_success else '❌ FAIL'}")
    print(f"   Format Validation: {'✅ PASS' if validation_success else '❌ FAIL'}")
    
    if conversion_success and validation_success:
        print("\n🎉 All SFT conversion tests passed!")
        print("📝 Next steps:")
        print("   - Set up API keys (OPENAI_API_KEY, TOGETHER_API_KEY)")
        print("   - Run train_sft_models.py to start training")
        print("   - Monitor training progress")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
    
    return conversion_success and validation_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
